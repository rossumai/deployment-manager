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
    replace_code_paths,
    should_write_object,
)
from deployment_manager.commands.download.subdirectory import SubdirectoriesDict
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
            workspace_saver = WorkspaceSaver(
                base_path=self.project_path / self.name,
                objects=workspaces_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await workspace_saver.save_downloaded_objects()

            queue_saver = QueueSaver(
                base_path=self.project_path / self.name,
                objects=queues_for_mapping,
                workspaces=workspaces_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await queue_saver.save_downloaded_objects()

            # TODO: test inbox without any queue
            inbox_saver = InboxSaver(
                base_path=self.project_path / self.name,
                objects=inboxes_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await inbox_saver.save_downloaded_objects()

            schema_saver = SchemaSaver(
                base_path=self.project_path / self.name,
                objects=schemas_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await schema_saver.save_downloaded_objects()

            hook_saver = HookSaver(
                base_path=self.project_path / self.name,
                objects=hooks_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                subdirs=subdir_list,
            )
            await hook_saver.save_downloaded_objects()
        except Exception as e:
            display_error("Error while saving objects ^", e)

        # 2. Find preexisting objects in download:true subdirs and update them
        # 3. For new objects from remote, apply the subdir regex if it is there.
        # If a download:true subdir matches, put it there
        # If no such subdir matches, list the objects to the user and ask if he wants to assign them into one of the subdirs manually (not just download:true)
        # 4. Delete non-existent objects, moved objects are moved on their own (by the user)

        self.id_object_map = self.create_id_object_map(
            [
                *workspaces_for_mapping,
                *queues_for_mapping,
                *inboxes_for_mapping,
                *schemas_for_mapping,
                *hooks_for_mapping,
            ]
        )
        await self.remove_objects_without_remote()

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

    async def remove_objects_without_remote(self):
        object_paths = await find_all_object_paths(self.project_path / self.name)
        for object_path in object_paths:
            if object_path.name == "organization.json":
                continue
            remove = await self.should_remove_object(object_path)
            if not remove:
                continue

            display_warning(
                f"Deleting a local object that no longer exists in Rossum or was renamed: {object_path}"
            )
            os.remove(object_path)

    async def should_remove_object(self, object_path: Path):
        object = await read_json(object_path)
        url, id = object.get("url", ""), object.get("id", "")
        # Clearly not a Rossum object, just ignore
        if not url or not id:
            return False

        object_type = determine_object_type_from_url(url)

        if id not in self.id_object_map:
            return True
        remote_object = self.id_object_map[id]

        # Name might have changed
        previous_name, _ = detemplatize_name_id(object_path)
        # Use the same process to create the name (e.g., missing forbidden chars like '/')
        path_from_remote = templatize_name_id(
            remote_object.get("name", ""), remote_object.get("id", "")
        )
        cleaned_name, _ = detemplatize_name_id(path_from_remote)
        # Inboxes and schemas are in the queue folder, but can have a different name than their queue
        # The names are lowercased because some OS's (mainly MacOS) are case-insensitive in their paths
        if cleaned_name.casefold() != previous_name.casefold() and object_type not in [
            Resource.Inbox,
            Resource.Schema,
        ]:
            return True

        return False