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
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.hook_run_after import (
    HookDependenciesDeployer,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
)

from deployment_manager.commands.deploy.subcommands.run.models import (
    LookupTable,
    ReverseLookupTable,
)
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    DeployException,
    ObjectRelease,
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
)


from pydantic import BaseModel
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource
from rossum_api.models.organization import Organization


# Strategy class with either plan or deploy methods
# Passed into release objects and just call them with their arguments
# The release objects can be shared, the actions are different

# Object layers
# 1. Deploy file: only attributes that are actually in it
# 2. ReleaseOrchestrator: deploy file + logic that works with it
# 2a. load everything
# 2a. plan
# Let user confirm or exit
# 2c. deploy

# Objects with a single representation
# Original source, deploy state, yaml file, user-provided input
# First deploy object (plan and real are the same)

# Objects with different versions
# Second deploy object (plan vs real)

# Object states based on the flow
# 1. Raw object loaded from local
# 2. Object prepared for first deploy  (missing references, e.g., hook.queues)
# 3. Object with references added in (dummy refs)
# 4. Object with real references (only one-way: queue.hooks but not hook.queues)

# Relevant methods for each object
# Load/initialize (+ validate nothing is missing)
# Prepare first deploy object
# Replace references in plan mode (both-way)
# Replace references in deploy mode (one-way)
# Plan (diff + visualize)
# Deploy (API call)

# Order of objects and their operations
# 1. Load everything
# 2. Prepare everything
# 3. Replace plan refs and show plan
# 4. Upload first deploy: org -> workspaces -> hooks -> queues -> ...
# 5. Replace deploy refs
# 6. Reupload (order does not matter)

# Operation flow
# 1. Load YAML objects, find their JSONs, load deploy state
# 2. Prepare first deploy objects (attribute override) - keep references as they are everywhere
# (Deploy needs two steps because some refs can be resolved only once objects are created)
# 3. Create dummy dependency resolution table: nonexistent objects get dummy refs
# ! Need to do dummy refs in the targets
# 4. Apply the table on the plan deploy objects (copy)
# ! (References need to be replaced in both places: queue.workspace and workspace.queues)
# 5. Visualize final state + show diffs between second deploy objects and target objects (on remote)
# (There might be conflicts and rebase prompts - if user did any rebase or conflict, the deploy command should be rerun)
# ? Rebase of reference fields will require a reverse table - but this will only be possible for existing objects - if the object does not exist in source, create it?
# (List only the final state, the fact that two updates need to happen is a detail)

# 6. User confirms/rejects plan, reacts to warnings, etc.
# (Context like warnings ignored must be passed around, alternatively, the deploy state can just run since warnings would be stopped before real deploy by checking for any warnings being raise during plan)

# 7. First upload (using object data without dummy refs)
# ! Queue needs things like workspace and schema to be created first
# 8. Create real dep resolution table
# 9. Apply the table on the first deploy objects (real)
# (One-way replacing only)
# 10. Run another wave of updates
# 11. Save deploy state (ideally after each deploy), repull
# TODO: Save deploy state after first deploy as well?

# Diffing
# Non-diffed attributes that are deployed (but wouldn't have to be): id, url
# Non-diffed attribtues that can be ignored (not deployed): generic_engine, workflows
# ! But some of those fields should be versioned in source and target, just not compared: generic_engine, queue and schema AI fields and thresholds
# org.users, modified_at, modified_by, org.org_group, org.creator

# Diffed attributes that are not deployed? Probably makes no sense to diff if not deployed...
# Diffed attribute that are deployed (default)


# TODO: error handling
# TODO: different error flag for each stage failure

# TODO: reverse deploy (PROD->UAT)

# TODO: keep references to non-deploy objects (e.g., queue.hooks should not empty hook.queues = [], keep what is unknown)

# TODO: check that all target IDs from deploy file actually (still) exist on remote

#! TODO: what about derived fields?

# TODO: --ours and --theirs params for merge


# TODO: release -> deploy
class DeployOrchestrator(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    plan_only: bool = False

    force_deploy: bool = False
    auto_delete: bool = False

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

    lookup_table: LookupTable = None
    reverse_lookup_table: ReverseLookupTable = None

    unselected_hooks: list[int] = []

    hook_templates: dict = {}
    queue_ignore_warnings: dict = {}

    ignore_all_deploy_warnings: bool = False

    hook_dep_deployer: HookDependenciesDeployer = None

    @property
    def is_same_org(self):
        return self.source_org.id == self.target_org.id

    @property
    def release_objects(self) -> list[DeployObject]:
        return [
            self.organization,
            *self.hooks,
            *self.workspaces,
            *self.queues,
        ]

    def __init__(self, **data):
        super().__init__(**data)

        self.hook_dep_deployer = HookDependenciesDeployer(deploy_file_reference=self)

        if (
            self.secrets_file
            and (secrets_file_path := pathlib.Path(self.secrets_file)).exists()
        ):
            # Read and parse the secrets file
            self.secrets = json.loads(secrets_file_path.read_text())

        # TODO: if YAML does not have the path, create it and update YAML with it when saving deploy file
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

        # TODO: direction
        # direction = "forward" if self.source_org.id < self.target_org.id else "reverse"

        schemas = [queue.schema_release for queue in self.queues]
        rules = [rule for schema in schemas for rule in schema.rule_releases]
        inboxes = [queue.inbox_release for queue in self.queues]

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

        # TODO: catch initialize exceptions
        await asyncio.gather(
            *[
                deploy_object.initialize_deploy_object(release_file=self)
                for deploy_object in self.release_objects
            ]
        )

        self.detect_initialize_phase_exceptions(self.workspaces)

    async def initialize_target_objects(self):
        await asyncio.gather(
            *[
                deploy_object.initialize_target_objects()
                for deploy_object in self.release_objects
            ]
        )

        self.lookup_table = self.create_lookup_table()

        # TODO: dummy references can be strings including the names of the objects for better diffs
        await asyncio.gather(
            *[
                deploy_object.override_references(
                    data_attribute="visualized_plan_data", use_dummy_references=True
                )
                for deploy_object in self.release_objects
            ]
        )

        # TODO: hook run after

    # TODO: ignored fields that should not be deployed, but what if user explicitly att overrides them?
    # TODO: if not patch_target_org -> do not compare, visualize and deploy, the deploy object must be there though for references etc.
    async def compare_object_versions(self):
        self.reverse_lookup_table = self.create_reverse_lookup_table()

        for object in self.release_objects:
            await object.compare_target_objects()

        # Need to pause execution of the command so the user can resolve them
        if any(object.conflict_detected for object in self.release_objects):
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
        for object in self.release_objects:
            if not object.conflict_detected and not object.rebase_detected:
                continue

            await object.initialize_deploy_object(release_file=self)
            await object.initialize_target_objects()
            await object.override_references(
                data_attribute="visualized_plan_data", use_dummy_references=True
            )

    async def show_deploy_plan(self):
        for object in self.release_objects:
            await object.visualize_changes()

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

            await self.hook_dep_deployer.migrate_hook_dependency_graph()

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

            # TODO: deploy errors should lead to deploy finishing in the middle or should we check only after everything was run?

            # TODO: Mark derived fields like run_after or queues
            # mark_derived_fields(
            #     deploy_state=self.deploy_state,
            #     resource_type="hooks",
            #     source_id=self.id,
            #     target_objs=self.targets,
            #     fields=["run_after", "queues"],
            # )
        except Exception as e:
            display_error(
                f'Error during {"first" if is_first else "second"} deploy: {e}', e
            )
            raise Exception from e

    # TODO: for perfect safety, comparison should be done after first deploy (what if someone on remote changed something in the middle of deploy?)
    # Compare first_deploy_data vs last_applied (saved after first_deploy) against remote

    # TODO: we have several versions of objects - should we just run ref replace again to catch what we did not the first time (i.e., objects that had to be created on target?)
    # ! Second deploy should not be a copy of first where refs were replaced - we will loose unknown source refs
    # ? Idea: second deploy is just literally initial_data (past attr override before ref replace) with another lookup applied
    # You do not need to update lookup table, just look into a different target property/use updated ID (dummy ID replaced by real ID)
    # ! Update dummy IDs to be real IDs after first deploy in targets
    # ! All refs should be known by now, otherwise -> error

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

    def detect_initialize_phase_exceptions(self, releases: list[ObjectRelease]):
        for release in releases:
            if release.initialize_failed:
                raise DeployException(
                    f"Initialize of {release.display_type} {release.display_label} failed, see error details above."
                )

    def detect_deploy_phase_exceptions(self, releases: list[ObjectRelease]):
        for release in releases:
            if release.deploy_failed:
                raise DeployException(
                    f"Deploy of {release.display_type} {release.display_label} failed, see error details above."
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

            lookup_table[queue.schema_release.id][
                Resource.Schema
            ] = queue.schema_release.targets
            for rule in queue.schema_release.rule_releases:
                lookup_table[rule.id][CustomResource.Rule] = rule.targets

            lookup_table[queue.inbox_release.id][
                Resource.Inbox
            ] = queue.inbox_release.targets

        return lookup_table

    def create_reverse_lookup_table(self) -> dict[str, int]:
        reverse = defaultdict(dict)
        for source_id, type_dict in self.lookup_table.items():
            for type, targets in type_dict.items():
                for target in targets:
                    reverse[type][target.id] = source_id
        return reverse


# Pydantic needs this
DeployOrchestrator.model_rebuild()
OrganizationDeployObject.model_rebuild()
HookDeployObject.model_rebuild()
WorkspaceDeployObject.model_rebuild()
QueueDeployObject.model_rebuild()
SchemaDeployObject.model_rebuild()
InboxDeployObject.model_rebuild()
RuleDeployObject.model_rebuild()
HookDependenciesDeployer.model_rebuild()
Target.model_rebuild()
