from anyio import Path
from pydantic import BaseModel
from deployment_manager.commands.upload.models import PushException
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from deployment_manager.commands.deploy.common.helpers import (
    validate_credentials,
)
from rich import print as pprint
from rich.panel import Panel
from deployment_manager.commands.deploy.subcommands.run.helpers import get_token
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from deployment_manager.commands.upload.dependencies import (
    mark_unstaged_objects_as_updated,
    merge_formula_changes,
    merge_hook_changes,
)

from deployment_manager.common.determine_path import (
    determine_object_type_from_url,
)
from deployment_manager.common.modified_at import check_modified_timestamp
from deployment_manager.common.read_write import read_object_from_json, write_object_to_json
from deployment_manager.utils.consts import (
    GIT_CHARACTERS,
    CustomResource,
    display_error,
    display_warning,
    settings,
)

from deployment_manager.commands.download.directory import OrganizationDirectory
from deployment_manager.common.git import get_changed_file_paths
from deployment_manager.utils.functions import (
    find_all_object_paths,
    gather_with_concurrency,
)


class ChangedObject(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    operation: GIT_CHARACTERS
    path: Path
    data: dict = {}

    @property
    def type(self) -> Resource:
        url = self.data.get("url", "")
        return determine_object_type_from_url(url)

    @property
    def id(self) -> str:
        return self.data.get("id", "")

    @property
    def display_type(self) -> str:
        # Remove the plural 's'
        return f"[yellow]{self.type.value[:-2 if self.type in [Resource.Inbox] else -1]}[/yellow]"

    @property
    def display_label(self) -> str:
        name = self.data.get("name", "no-name")
        if self.id and name:
            return f'"[orange]{name}[/orange] ([purple]{self.id}[/purple])"'
        else:
            return f"[red]{self.path}[/red]"

    @property
    def display_operation(self):
        display_operation = ""
        match self.operation:
            case GIT_CHARACTERS.CREATED | GIT_CHARACTERS.CREATED_STAGED:
                display_operation = settings.CREATE_PRINT_STR
            case GIT_CHARACTERS.DELETED:
                display_operation = settings.CREATE_PRINT_STR
            case GIT_CHARACTERS.UPDATED | GIT_CHARACTERS.PARTIALLY_UPADTED:
                display_operation = settings.UPDATE_PRINT_STR
        return display_operation

    def create_timestamp_mismatch_message(self):
        return f"{self.display_type} {self.display_label}: Remote object has a different timestamp. Please stash your changes and run {settings.DOWNLOAD_COMMAND_NAME} first."

    def create_success_message(self):
        return f"{self.display_operation} {self.display_type} {self.display_label}"

    def create_failure_message(self, error: str):
        return f"{self.display_operation} {self.display_type} {self.display_label}: {error}"


class UploadOrganizationDirectory(OrganizationDirectory):
    upload_all: bool = False
    force: bool = False
    indexed_only: bool = False
    changed_objects: list[ChangedObject] = []
    request_errors: list[str] = []
    include_only_files: list[Path] | None = None

    async def initialize(self):
        if not self.project_path:
            self.project_path = Path(".")

        if not self.client:
            token = await get_token(
                project_path=self.project_path,
                org_name=self.name,
                api_url=self.api_base,
            )
            credentials = Credentials(token=token, url=self.api_base)
            await validate_credentials(credentials)
            self.client = ElisAPIClient(base_url=self.api_base, token=token)

    async def prepare_changed_objects(self):
        changes = get_changed_file_paths(
            self.project_path / self.name, indexed_only=self.indexed_only
        )
        if self.include_only_files:
            filtered_changes = []
            for change_type, change_filename in changes:
                if change_filename in self.include_only_files:
                    filtered_changes.append((change_type, change_filename))
            changes = filtered_changes

        if not changes:
            display_warning(
                f"No changes to {settings.UPLOAD_COMMAND_NAME} found in {self.org_path}."
            )
            return

        changes = await merge_hook_changes(changes, self.project_path)
        # changes = await evaluate_delete_dependencies(changes, org_path)
        changes = await merge_formula_changes(changes)
        changes = await mark_unstaged_objects_as_updated(
            changes, self.project_path, self.client
        )

        # Include files from all subdirs, the non-included subdir objects will be filtered out later
        if self.upload_all:
            await self.include_unmodified_files(changes)

        for op, path in changes:
            # Deleted object cannot be read from a local path...
            if op == GIT_CHARACTERS.DELETED:
                continue

            data = await read_object_from_json(path)
            if not (object_url := data.get('url', "")):
                continue
            object_type = determine_object_type_from_url(object_url)
            subdir = self.find_subdir_of_object(data)
            if not subdir:
                display_warning(f"No subdir found for path: {path}, skipping.")
                continue
            # Change found in a subdir not selected by the user to be pushed, skip
            elif not subdir.include:
                continue
            # Some objects cannot be updated via Elis API
            elif object_type in [CustomResource.Workflow, CustomResource.WorkflowStep]:
                continue

            changed_object = ChangedObject(operation=op, path=path, data=data)
            self.changed_objects.append(changed_object)

    def find_subdir_of_object(self, object: dict):
        for subdir in self.subdirectories.values():
            if object.get("id", None) in subdir.object_ids:
                return subdir
        return None

    async def upload_organization(self):
        try:
            await self.initialize()
        except Exception as e:
            display_error(f"Error while initializing {self.display_label}: {str(e)}")
            return

        try:
            await self.find_object_ids_for_subdirs()
            await self.prepare_changed_objects()
            requests = await self.prepare_upload_requests()
            if not requests:
                return
        except PushException as e:
            display_error(
                f"Error while preparing objects to {settings.UPLOAD_COMMAND_NAME} for {self.display_label}: {str(e)}",
            )
            return
        except Exception as e:
            display_error(
                f"Error while preparing objects to {settings.UPLOAD_COMMAND_NAME} for {self.display_label}: {str(e)}",
                e,
            )
            return

        pprint(
            Panel(
                f"Pushing objects to {self.display_label} (Total objects: {len(requests)})"
            )
        )
        # Update in batches of 5
        await gather_with_concurrency(5, *requests)

    async def prepare_upload_requests(self):
        requests = []
        for changed_object in self.changed_objects:
            match changed_object.operation:
                case GIT_CHARACTERS.CREATED | GIT_CHARACTERS.CREATED_STAGED:
                    requests.append(self.make_create_request(object=changed_object))
                case GIT_CHARACTERS.UPDATED | GIT_CHARACTERS.PARTIALLY_UPADTED:
                    requests.append(self.make_update_request(object=changed_object))
                case _:
                    self.request_errors.append(
                        f'Unrecognized operation "{changed_object.operation}" for {changed_object.display_type} {changed_object.display_label}.'
                    )

        return requests

    async def include_unmodified_files(self, changes: list[tuple[str, Path]]):
        all_files = await find_all_object_paths(self.org_path)

        changes_paths = set(map(lambda x: x[1], changes))
        for file_path in all_files:
            if file_path not in changes_paths:
                changes.append((GIT_CHARACTERS.UPDATED.value, file_path))

    async def make_update_request(self, object: ChangedObject):
        try:
            url = object.data.get("url", None)
            if not object.id:
                raise Exception("Missing object ID")
            if not url:
                raise Exception("Missing object URL")
            local_remote_timestamp_synced = await check_modified_timestamp(
                client=self.client,
                resource=object.type,
                id=object.id,
                local_object=object.data,
            )
            if not self.force and not local_remote_timestamp_synced:
                self.request_errors.append(object.create_timestamp_mismatch_message())
                return None

            # queue.inbox attributes are ready-only in Elis API, but we don't ignore them when pulling to distinguish queues with and without inboxes
            if object.type == Resource.Queue:
                object.data.pop("inbox", None)

            result = await self.client._http_client.update(
                object.type, object.id, object.data
            )

            # Just to update the timestamp
            await write_object_to_json(
                object.path,
                result,
                object.type,
            )

            pprint(object.create_success_message())
            return result
        except Exception as e:
            self.request_errors.append(object.create_failure_message(str(e)))

            if self.upload_all:
                pprint(
                    Panel(f"Recreating {object.display_type} {object.display_label}")
                )
                return await self.make_create_request(object=object)

    async def make_create_request(self, object: ChangedObject):
        try:
            object.data["id"] = None
            result = await self.client._http_client.create(object.type, object.data)

            # Just to update the timestamp
            await write_object_to_json(
                object.path,
                result,
                object.type,
            )

            pprint(object.create_success_message())
            return result
        except Exception as e:
            self.request_errors.append(object.create_failure_message(str(e)))

    async def make_delete_request(self, object: ChangedObject):
        try:
            local_remote_timestamp_synced = await check_modified_timestamp(
                self.client, object.type, object.id, object.data
            )
            if not self.force and not local_remote_timestamp_synced:
                self.request_errors.append(object.create_timestamp_mismatch_message())
                return None

            await self.client._http_client.delete(object.type, object.id)

            pprint(f"{object.create_success_message()} - object not deleted locally!")
        except Exception as e:
            self.request_errors.append(object.create_failure_message(str(e)))
