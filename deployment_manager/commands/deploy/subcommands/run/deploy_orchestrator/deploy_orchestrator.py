import asyncio
from collections import defaultdict
import json
from anyio import Path
import pathlib
import questionary
from deployment_manager.commands.deploy.common.helpers import get_token_owner_from_user
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.hook_deploy_object import (
    HookDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.inbox_deploy_object import (
    InboxDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.organization_deploy_object import (
    OrganizationDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.queue_deploy_object import (
    QueueDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.rule_deploy_object import (
    RuleDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.schema_deploy_object import (
    SchemaDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.workspace_deploy_object import (
    WorkspaceDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
)

from deployment_manager.commands.deploy.subcommands.run.models import (
    DeployException,
    LookupTable,
    ReverseLookupTable,
    Target,
)


from deployment_manager.commands.deploy.subcommands.run.merge.state import (
    DeployState,
)

from deployment_manager.utils.consts import (
    CustomResource,
    display_error,
    display_info,
    display_warning,
    settings,
)


from pydantic import BaseModel
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource
from rossum_api.models.organization import Organization


# TODO: dummy refs not in diff -> conflict if org.workspaces is 1 and we are creating another
# TODO: purge should clean up state file as well


class DeployOrchestrator(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    auto_delete: bool = False
    prefer: str = None

    patch_target_org: bool = True
    token_owner_id: int | None = None
    deployed_org_id: int | None = ""
    last_deployed_at: str | None = ""
    secrets_file: str | None = ""
    deploy_state_file: str | None = ""

    secrets: dict | None = {}
    deploy_state: DeployState | None = {}

    client: ElisAPIClient
    source_client: ElisAPIClient
    source_dir_path: Path
    yaml: DeployYaml

    source_org: Organization
    target_org: Organization

    organization: OrganizationDeployObject = None
    workspaces: list[WorkspaceDeployObject] = []
    queues: list[QueueDeployObject] = []
    hooks: list[HookDeployObject] = []

    lookup_table: LookupTable = {}
    reverse_lookup_table: ReverseLookupTable = {}

    unselected_hooks: list[int] = []

    hook_templates: dict = {}
    queue_ignore_warnings: dict = {}

    ignore_all_deploy_warnings: bool = False

    @property
    def is_same_org(self):
        return self.source_org.id == self.target_org.id

    @property
    def deploy_objects(self) -> list[DeployObject]:
        return [
            self.organization,
            *self.hooks,
            *self.workspaces,
            *self.queues,
        ]

    def __init__(self, **data):
        super().__init__(**data)

        if (
            self.secrets_file
            and (secrets_file_path := pathlib.Path(self.secrets_file)).exists()
        ):
            # Read and parse the secrets file
            self.secrets = json.loads(secrets_file_path.read_text())

        self.deploy_state = DeployState.load_deploy_state(
            path=pathlib.Path(self.deploy_state_file)
        )

        self.organization = OrganizationDeployObject(
            id=self.source_org.id,
            name=self.source_org.name,
        )

    async def save_deploy_state(self):
        """Save the last applied config for all deployed resources."""
        if not self.deploy_state_file:
            return

        schemas = [queue.schema_deploy_object for queue in self.queues]
        rules = [rule for schema in schemas for rule in schema.rule_deploy_objects]
        inboxes = [queue.inbox_deploy_object for queue in self.queues]

        deploy_state_objects = [
            (Resource.Organization, [self.organization]),
            (Resource.Hook, self.hooks),
            (Resource.Queue, self.queues),
            (Resource.Schema, schemas),
            (CustomResource.Rule, rules),
            (Resource.Inbox, inboxes),
            (Resource.Workspace, self.workspaces),
        ]

        await self.deploy_state.update_deploy_state(
            objects=deploy_state_objects,
        )

        await self.deploy_state.write_deploy_state(Path(self.deploy_state_file))

    async def initialize_deploy_objects(self):
        await self.ensure_token_owner()

        await asyncio.gather(
            *[
                deploy_object.initialize_deploy_object(deploy_file=self)
                for deploy_object in self.deploy_objects
            ],
        )

        self.detect_phase_exceptions("initialize_failed")

    async def initialize_target_objects(self):
        try:
            await asyncio.gather(
                *[
                    deploy_object.initialize_target_objects()
                    for deploy_object in self.deploy_objects
                ],
            )
        except Exception as e:
            display_error(f"Error during initialization of target objects: {e}")
            raise Exception from e

        try:
            self.lookup_table = self.create_lookup_table()

            await asyncio.gather(
                *[
                    deploy_object.override_references(
                        data_attribute="visualized_plan_data", use_dummy_references=True
                    )
                    for deploy_object in self.deploy_objects
                ]
            )
        except Exception as e:
            display_error(f"Error during overriding references of target objects: {e}")
            raise Exception from e

    # TODO: ignored fields that should not be deployed, but what if user explicitly att overrides them?
    async def compare_object_versions(self):
        try:
            self.reverse_lookup_table = self.create_reverse_lookup_table()

            for object in self.deploy_objects:
                if (
                    isinstance(object, OrganizationDeployObject)
                    and not self.patch_target_org
                ):
                    continue
                await object.compare_target_objects()

            # Need to pause execution of the command so the user can resolve them
            if any(object.conflict_detected for object in self.deploy_objects):
                display_warning(
                    "Conflicts detected: please go to the files listed above and resolve them.\n\n[bold]Do not exit this command, otherwise, you might be prompted to resolve the conflict again when source is compared to remote target.[/bold]"
                )
                if not await questionary.confirm(
                    "Confirm that conflicts were resolved."
                ).ask_async():
                    raise DeployException(
                        "Please rerun the command once conflicts were resolved."
                    )

            # Objects need to be reloaded from source and everything reapplied for them
            for object in self.deploy_objects:
                if not object.conflict_detected and not object.rebase_detected:
                    continue

                await object.initialize_deploy_object(deploy_file=self)
                await object.initialize_target_objects()
                await object.override_references(
                    data_attribute="visualized_plan_data", use_dummy_references=True
                )
        except Exception as e:
            display_error(
                f"Error during comparison of prepared target objects with their remote versions: {e}"
            )
            raise Exception from e

    async def show_deploy_plan(self):
        try:
            for object in self.deploy_objects:
                if (
                    isinstance(object, OrganizationDeployObject)
                    and not self.patch_target_org
                ):
                    continue
                await object.visualize_changes()
        except Exception as e:
            display_error(f"Error during visualization of deploy plan changes: {e}")
            raise Exception from e

    async def run_deploy(self, is_first: bool):
        try:
            data_attribute = "first_deploy_data" if is_first else "second_deploy_data"

            display_info(f'{"First" if is_first else "Second"} deploy started.')

            if self.patch_target_org:
                await self.organization.deploy_target_objects(
                    data_attribute=data_attribute
                )

            await asyncio.gather(
                *[
                    deploy_object.deploy_target_objects(data_attribute=data_attribute)
                    for deploy_object in self.hooks
                ]
            )

            await asyncio.gather(
                *[
                    deploy_object.deploy_target_objects(data_attribute=data_attribute)
                    for deploy_object in self.workspaces
                ]
            )

            await asyncio.gather(
                *[
                    deploy_object.deploy_target_objects(data_attribute=data_attribute)
                    for deploy_object in self.queues
                ]
            )

            display_info(f'{"First" if is_first else "Second"} deploy finished.')

        except Exception as e:
            display_error(
                f'Error during {"first" if is_first else "second"} deploy: {e}'
            )
            raise Exception from e

    # TODO: for perfect safety, comparison should be done after first deploy (what if someone on remote changed something in the middle of deploy?)
    # Compare first_deploy_data vs last_applied (saved after first_deploy) against remote

    async def ensure_token_owner(self):
        if self.source_org.id == self.target_org.id:
            return

        if self.token_owner_id:
            try:
                await self.client.retrieve_user(self.token_owner_id)
            except APIClientError:
                display_warning("Invalid token owner in config.")
                self.token_owner_id = None

        if not self.token_owner_id:
            self.token_owner_id = await get_token_owner_from_user(self.client)

    def detect_phase_exceptions(self, attribute_name: str):
        error_objects = []
        for deploy_object in self.deploy_objects:
            attr = getattr(deploy_object, attribute_name)
            if attr:
                error_objects.append(
                    f"{deploy_object.display_type} {deploy_object.display_label}"
                )

            if error_objects:
                raise DeployException(
                    f"Error occurred for the following deploy objects, see error details above:\n"
                    + "\n".join(error_objects)
                )

    def create_lookup_table(self):
        lookup_table = defaultdict(dict)

        lookup_table[self.organization.id][
            Resource.Organization
        ] = self.organization.targets

        for hook in self.hooks:
            lookup_table[hook.id][Resource.Hook] = hook.targets
        for workspace in self.workspaces:
            lookup_table[workspace.id][Resource.Workspace] = workspace.targets
        for queue in self.queues:
            lookup_table[queue.id][Resource.Queue] = queue.targets

            lookup_table[queue.schema_deploy_object.id][
                Resource.Schema
            ] = queue.schema_deploy_object.targets
            for rule in queue.schema_deploy_object.rule_deploy_objects:
                lookup_table[rule.id][CustomResource.Rule] = rule.targets

            lookup_table[queue.inbox_deploy_object.id][
                Resource.Inbox
            ] = queue.inbox_deploy_object.targets

        return lookup_table

    def create_reverse_lookup_table(self) -> dict[str, int]:
        reverse = defaultdict(dict)
        for source_id, type_dict in self.lookup_table.items():
            for type, targets in type_dict.items():
                for target in targets:
                    reverse[type][target.id] = source_id
        return reverse

    def update_ignore_flags_in_yaml(self):
        ignore_warning_map = {}
        for queue in self.queues:
            ignore_warning_map[queue.id] = queue.ignore_deploy_warnings

        for queue in self.yaml.data.get(settings.DEPLOY_KEY_QUEUES, []):
            if not (queue_id := queue.get("id", None)):
                continue
            queue[settings.DEPLOY_KEY_IGNORE_DEPLOY_WARNINGS] = ignore_warning_map.get(
                queue_id, False
            )


# Pydantic needs this
DeployOrchestrator.model_rebuild()
OrganizationDeployObject.model_rebuild()
HookDeployObject.model_rebuild()
WorkspaceDeployObject.model_rebuild()
QueueDeployObject.model_rebuild()
SchemaDeployObject.model_rebuild()
InboxDeployObject.model_rebuild()
RuleDeployObject.model_rebuild()
Target.model_rebuild()
