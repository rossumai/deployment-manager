import asyncio
import os
from anyio import Path
from pydantic import BaseModel
from rich import print as pprint


from deployment_manager.commands.deploy.common.helpers import (
    validate_credentials,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import get_token
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from deployment_manager.commands.download.downloader import Downloader
from deployment_manager.commands.download.helpers import (
    delete_empty_folders,
    delete_orphaned_formulas,
    replace_code_paths,
    should_write_object,
)
from deployment_manager.commands.download.subdirectory import (
    SubdirectoriesDict,
    Subdirectory,
)
from deployment_manager.common.determine_path import determine_object_type_from_url
from deployment_manager.utils.consts import display_error, display_warning, settings
from deployment_manager.commands.download.saver import (
    HookSaver,
    InboxSaver,
    QueueSaver,
    SchemaSaver,
    WorkspaceSaver,
)
from deployment_manager.common.git import get_changed_file_paths
from deployment_manager.common.read_write import read_json, write_json
from deployment_manager.utils.functions import (
    detemplatize_name_id,
    extract_id_from_url,
    find_all_object_paths,
    templatize_name_id,
)

from rich.panel import Panel
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource


class DownloadException(Exception): ...


# TODO: use ConfigDict instead of Config class (pydantic)


class OrganizationDirectory(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    # Present in the config YAML
    name: str
    org_id: int
    api_base: str
    subdirectories: SubdirectoriesDict = {}

    # Added later
    client: ElisAPIClient = None
    project_path: Path = None

    @property
    def org_path(self):
        return self.project_path / self.name

    @property
    def display_label(self):
        return f'"[blue]{self.org_path}[/blue] ([purple]{self.org_id}[/purple])"'

    async def find_object_ids_for_subdirs(self):
        for subdir in self.subdirectories.values():
            subdir_path = self.project_path / self.name / subdir.name
            object_paths = await find_all_object_paths(subdir_path)

            object_ids = set()
            for object_path in object_paths:
                object = await read_json(object_path)
                object_id = object.get("id", None)
                if object_id:
                    object_ids.add(object_id)
            subdir.object_ids = object_ids


# TODO: use display label


class DownloadOrganizationDirectory(OrganizationDirectory):
    id_object_map: dict = {}
    changed_files: list = []

    download_all: bool = False

    workspace_saver: WorkspaceSaver = None
    queue_saver: QueueSaver = None
    inbox_saver: InboxSaver = None
    schema_saver: SchemaSaver = None
    hook_saver: HookSaver = None

    async def initialize(self):
        if not self.project_path:
            self.project_path = Path(".")

        changed_files = get_changed_file_paths(self.org_path)
        changed_files = list(map(lambda x: x[1], changed_files))
        changed_files = replace_code_paths(changed_files)
        self.changed_files = changed_files

        if not self.client:
            token = await get_token(
                project_path=self.project_path,
                org_name=self.name,
                api_url=self.api_base,
            )
            credentials = Credentials(token=token, url=self.api_base)
            await validate_credentials(credentials)
            self.client = ElisAPIClient(base_url=self.api_base, token=token)

    # TODO: catch errors on org-dir or subdir level?
    async def download_organization(self):
        await self.initialize()

        pprint(Panel(f"Scanning for remote changes in {self.org_path}..."))

        try:
            await self.download_and_save_organization_object()

            downloader = Downloader(client=self.client)
            (
                workspaces_for_mapping,
                queues_for_mapping,
                inboxes_for_mapping,
                schemas_for_mapping,
                hooks_for_mapping,
            ) = await asyncio.gather(
                *[
                    downloader.download_remote_objects(type=Resource.Workspace),
                    downloader.download_remote_objects(type=Resource.Queue),
                    downloader.download_remote_objects(type=Resource.Inbox),
                    downloader.download_remote_objects(type=Resource.Schema),
                    downloader.download_remote_objects(type=Resource.Hook),
                ]
            )

        except DownloadException as e:
            display_error(f"Downloading from remote failed for {self.name}: {e}")
            return
        except Exception as e:
            display_error(f"Downloading from remote failed for {self.name}: {e}", e)
            return

        await self.find_object_ids_for_subdirs()

        subdir_list = list(self.subdirectories.values())

        try:
            self.workspace_saver = WorkspaceSaver(
                base_path=self.project_path / self.name,
                objects=workspaces_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await self.workspace_saver.save_downloaded_objects()

            self.queue_saver = QueueSaver(
                base_path=self.project_path / self.name,
                objects=queues_for_mapping,
                workspaces=workspaces_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await self.queue_saver.save_downloaded_objects()

            # TODO: test inbox without any queue
            self.inbox_saver = InboxSaver(
                base_path=self.project_path / self.name,
                objects=inboxes_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await self.inbox_saver.save_downloaded_objects()

            self.schema_saver = SchemaSaver(
                base_path=self.project_path / self.name,
                objects=schemas_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await self.schema_saver.save_downloaded_objects()

            self.hook_saver = HookSaver(
                base_path=self.project_path / self.name,
                objects=hooks_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await self.hook_saver.save_downloaded_objects()
        except Exception as e:
            display_error("Error while saving objects ^", e)

        self.id_object_map = self.create_id_object_map(
            [
                *workspaces_for_mapping,
                *queues_for_mapping,
                *inboxes_for_mapping,
                *schemas_for_mapping,
                *hooks_for_mapping,
            ]
        )

        await self.remove_stale_objects()
        await self.remove_empty_queue_dirs()

        pprint(Panel(f"Finished {settings.DOWNLOAD_COMMAND_NAME} for {self.name}."))

    async def download_and_save_organization_object(self):
        try:
            organization = await self.client._http_client.fetch_one(
                Resource.Organization, self.org_id
            )
            org_file_path = self.project_path / self.name / "organization.json"
            if self.download_all or await should_write_object(
                org_file_path, organization, self.changed_files
            ):
                await write_json(
                    org_file_path,
                    organization,
                    Resource.Organization,
                    log_message=f"Pulled {org_file_path}.",
                )
        except APIClientError as e:
            if e.status_code == 404:
                raise DownloadException(
                    f'Organization with ID "{self.org_id}" not found with the specified token in {self.api_base}. Please make sure you have to correct token and target URL.'
                )
            elif e.status_code == 401:
                raise DownloadException(
                    f'Invalid token "{self.client._http_client.token}" for organization with ID "{self.org_id}" and URL "{self.api_base}". Please make sure you have to correct token.'
                )

    def create_id_object_map(self, objects: list[dict]):
        map = {}
        for object in objects:
            map[object["id"]] = object
        return map

    async def remove_stale_objects(self):
        for subdir in self.subdirectories.values():
            if not subdir.include:
                continue

            object_paths = []
            subdir_path = self.project_path / self.name / subdir.name
            object_paths.extend(await find_all_object_paths(subdir_path))

            for object_path in object_paths:
                if object_path.name == "organization.json":
                    continue

                remove = await self.should_remove_object(object_path, subdir=subdir)
                if remove:
                    display_warning(
                        f"Deleting a local object that no longer exists in Rossum or was renamed: [green]{object_path}[/green]"
                    )
                    os.remove(object_path)

    async def remove_empty_queue_dirs(self):
        for subdir in self.subdirectories.values():
            if not subdir.include:
                continue
            subdir_ws_path = self.project_path / self.name / subdir.name / "workspaces"
            await delete_orphaned_formulas(subdir_ws_path)
            await delete_empty_folders(subdir_ws_path)

    async def should_remove_object(self, object_path: Path, subdir: Subdirectory):
        try:
            local_object = await read_json(object_path)
            url, id = local_object.get("url", ""), local_object.get("id", "")
            # Clearly not a Rossum object, just ignore
            if not url or not id:
                return False

            # The ID is not among all downloaded objects in that organization
            if id not in self.id_object_map:
                return True

            if self.is_object_path_different(
                local_object=local_object, local_path=object_path, subdir=subdir
            ):
                return True

            return False
        except Exception as e:
            display_error(
                f"Error while checking if object [green]{object_path}[/green] should be removed (skipping) ^",
                e,
            )
            return False

    def is_object_path_different(
        self, local_object: dict, local_path: Path, subdir: Subdirectory
    ):
        remote_object = self.id_object_map[local_object["id"]]
        object_type = determine_object_type_from_url(local_object["url"])

        # Construct paths and compare them
        # Objects with same IDs and different paths should get the local (previous) version removed
        match object_type:
            case Resource.Hook:
                remote_path = self.hook_saver.construct_object_path(
                    subdir, remote_object
                )
            case Resource.Schema:
                remote_path = self.schema_saver.construct_object_path(
                    subdir, remote_object
                )
            case Resource.Inbox:
                remote_path = self.inbox_saver.construct_object_path(
                    subdir, remote_object
                )
            case Resource.Queue:
                remote_path = self.queue_saver.construct_object_path(
                    subdir, remote_object
                )
            case Resource.Workspace:
                remote_path = self.workspace_saver.construct_object_path(
                    subdir, remote_object
                )

        # The names are lowercased because some OS's (mainly MacOS) are case-insensitive in their paths
        return str(remote_path).casefold() != str(local_path).casefold()
