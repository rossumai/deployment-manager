import asyncio
from collections import defaultdict
from typing import Optional
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
    delete_empty_formula_dir,
    replace_code_paths,
    should_write_object,
)
from deployment_manager.commands.download.remover import ObjectRemover
from deployment_manager.commands.download.saver import (
    EmailTemplateSaver,
    HookSaver,
    InboxSaver,
    QueueSaver,
    RuleSaver,
    RuleTemplateSaver,
    SchemaSaver,
    WorkflowSaver,
    WorkflowStepSaver,
    WorkspaceSaver,
)
from deployment_manager.commands.download.subdirectory import (
    SubdirectoriesDict,
    Subdirectory,
)
from deployment_manager.commands.download.types import ObjectSaver
from deployment_manager.common.determine_path import determine_object_type_from_url
from deployment_manager.utils.consts import (
    CustomResource,
    display_error,
    settings,
)

from deployment_manager.common.git import get_changed_file_paths
from deployment_manager.common.read_write import (
    read_object_from_json,
    write_object_to_json,
)
from deployment_manager.utils.functions import (
    find_all_object_paths,
)

from rich.panel import Panel
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource
from rossum_api.models.hook import Hook


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
                object = await read_object_from_json(object_path)
                object_id = object.get("id", None)
                if object_id:
                    object_ids.add(object_id)
            subdir.object_ids = object_ids


# TODO: use display label


class DownloadOrganizationDirectory(OrganizationDirectory):
    id_objects_map: dict[str, dict[int, dict]] = {}
    changed_files: list = []

    download_all: bool = False
    skip_objects_without_subdir: bool = False
    ignore_changed_file_warnings: bool = False

    workspace_saver: Optional["WorkspaceSaver"] = None
    queue_saver: Optional["QueueSaver"] = None
    email_template_saver: Optional["EmailTemplateSaver"] = None
    inbox_saver: Optional["InboxSaver"] = None
    schema_saver: Optional["SchemaSaver"] = None
    rule_saver: Optional["RuleSaver"] = None
    rule_template_saver: Optional["RuleTemplateSaver"] = None
    hook_saver: Optional["HookSaver"] = None
    workflow_saver: Optional["WorkflowSaver"] = None
    workflow_step_saver: Optional["WorkflowStepSaver"] = None

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
                email_templates_for_mapping,
                inboxes_for_mapping,
                schemas_for_mapping,
                rules_for_mapping,
                rule_templates_for_mapping,
                hooks_for_mapping,
                workflows_for_mapping,
                workflow_steps_for_mapping,
            ) = await asyncio.gather(
                *[
                    downloader.download_remote_objects(type=Resource.Workspace),
                    downloader.download_remote_objects(type=Resource.Queue),
                    downloader.download_remote_objects(type=Resource.EmailTemplate),
                    downloader.download_remote_objects(type=Resource.Inbox),
                    downloader.download_remote_objects(type=Resource.Schema),
                    downloader.download_remote_objects(
                        type=CustomResource.Rule, check_access=True
                    ),
                    downloader.download_remote_objects(
                        type=CustomResource.RuleTemplate, check_access=True
                    ),
                    downloader.download_remote_objects(type=Resource.Hook),
                    downloader.download_remote_objects(
                        type=CustomResource.Workflow, check_access=True
                    ),
                    downloader.download_remote_objects(
                        type=CustomResource.WorkflowStep, check_access=True
                    ),
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
        # Assigned outside of the constructor because Pydantic creates a copy - we need a shared reference
        subdirs_by_object_id: dict[int, str] = {}

        try:
            self.workspace_saver = WorkspaceSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=workspaces_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.workspace_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.workspace_saver.save_downloaded_objects()

            self.queue_saver = QueueSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=queues_for_mapping,
                workspaces=workspaces_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.queue_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.queue_saver.save_downloaded_objects()

            self.email_template_saver = EmailTemplateSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=email_templates_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.email_template_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.email_template_saver.save_downloaded_objects()

            # TODO: test inbox without any queue
            self.inbox_saver = InboxSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=inboxes_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.inbox_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.inbox_saver.save_downloaded_objects()

            self.schema_saver = SchemaSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=schemas_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.schema_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.schema_saver.save_downloaded_objects()

            self.rule_saver = RuleSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=rules_for_mapping,
                schemas=schemas_for_mapping,
                workspaces=workspaces_for_mapping,
                queues=queues_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.rule_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.rule_saver.save_downloaded_objects()

            self.rule_template_saver = RuleTemplateSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=rule_templates_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.rule_template_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.rule_template_saver.save_downloaded_objects()

            self.hook_saver = HookSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=hooks_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.hook_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.hook_saver.save_downloaded_objects()

            self.workflow_saver = WorkflowSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=workflows_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.workflow_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.workflow_saver.save_downloaded_objects()

            self.workflow_step_saver = WorkflowStepSaver(
                parent_dir_reference=self,
                base_path=self.project_path / self.name,
                objects=workflow_steps_for_mapping,
                workflows=workflows_for_mapping,
                changed_files=self.changed_files,
                download_all=self.download_all,
                skip_objects_without_subdir=self.skip_objects_without_subdir,
                subdirs=subdir_list,
            )
            self.workflow_step_saver.subdirs_by_object_id = subdirs_by_object_id
            await self.workflow_step_saver.save_downloaded_objects()

            self.id_objects_map = self.create_id_objects_map(
                [
                    *workspaces_for_mapping,
                    *queues_for_mapping,
                    *email_templates_for_mapping,
                    *inboxes_for_mapping,
                    *schemas_for_mapping,
                    *rules_for_mapping,
                    *rule_templates_for_mapping,
                    *hooks_for_mapping,
                    *workflows_for_mapping,
                    *workflow_steps_for_mapping,
                ]
            )

            await self.remove_stale_objects()
            await self.remove_empty_queue_dirs()

            pprint(Panel(f"Finished {settings.DOWNLOAD_COMMAND_NAME} for {self.name}."))
        except Exception as e:
            display_error("Error while saving downloaded objects ^", e)

    async def download_and_save_organization_object(self):
        try:
            organization = await self.client._http_client.fetch_one(
                Resource.Organization, self.org_id
            )
            org_file_path = self.project_path / self.name / "organization.json"
            if self.download_all or await should_write_object(
                org_file_path, organization, self.changed_files, self
            ):
                await write_object_to_json(
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

    def create_id_objects_map(self, objects: list[dict]):
        map = defaultdict(dict)
        for object in objects:
            type = determine_object_type_from_url(object["url"])
            map[type][object["id"]] = object
        return map

    async def remove_stale_objects(self):
        for subdir in self.subdirectories.values():
            if not subdir.include:
                continue

            object_paths = []
            subdir_path = self.project_path / self.name / subdir.name
            object_paths.extend(await find_all_object_paths(subdir_path))

            for object_path in object_paths:
                await self.validate_and_remove_object(object_path, subdir=subdir)

    async def remove_empty_queue_dirs(self):
        for subdir in self.subdirectories.values():
            if not subdir.include:
                continue

            subdir_ws_path = self.project_path / self.name / subdir.name / "workspaces"
            if not await subdir_ws_path.exists():
                continue

            await delete_empty_formula_dir(subdir_ws_path)
            await delete_empty_folders(subdir_ws_path)

    async def validate_and_remove_object(self, object_path: Path, subdir: Subdirectory):
        try:
            if object_path.name == "organization.json":
                return

            object_remover = await ObjectRemover.construct_remover(
                object_path=object_path,
                subdir=subdir,
                id_objects_map=self.id_objects_map,
                path_constructor=self.construct_path_for_remote_object,
                directory=self,
            )

            if not object_remover:
                return

            await object_remover.remove_if_stale()
        except Exception as e:
            display_error(
                f"Error while checking if object [green]{object_path}[/green] should be removed (skipping) ^",
                e,
            )

    def construct_path_for_remote_object(
        self,
        object_type: Resource | CustomResource,
        remote_object: dict,
        subdir: Subdirectory,
    ):
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
            case CustomResource.Rule:
                remote_path = self.rule_saver.construct_object_path(
                    subdir, remote_object
                )
            case CustomResource.RuleTemplate:
                remote_path = self.rule_template_saver.construct_object_path(
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
            case Resource.EmailTemplate:
                remote_path = self.email_template_saver.construct_object_path(
                    subdir, remote_object
                )
            case Resource.Workspace:
                remote_path = self.workspace_saver.construct_object_path(
                    subdir, remote_object
                )
            case CustomResource.Workflow:
                remote_path = self.workflow_saver.construct_object_path(
                    subdir, remote_object
                )
            case CustomResource.WorkflowStep:
                remote_path = self.workflow_step_saver.construct_object_path(
                    subdir, remote_object
                )
            case _:
                return ""

        return remote_path


# Pydantic needs this
ObjectSaver.model_rebuild()
WorkspaceSaver.model_rebuild()
QueueSaver.model_rebuild()
EmailTemplateSaver.model_rebuild()
HookSaver.model_rebuild()
WorkflowSaver.model_rebuild()
WorkflowStepSaver.model_rebuild()
SchemaSaver.model_rebuild()
RuleSaver.model_rebuild()
RuleTemplateSaver.model_rebuild()
InboxSaver.model_rebuild()
