import json
import pathlib
from collections import defaultdict

import questionary
from anyio import Path
from pydantic import BaseModel
from ruamel.yaml import YAML

from deployment_manager.commands.deploy.common.helpers import get_token_owner_from_user
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.email_template_deploy_object import (
    EmailTemplateDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.hook_deploy_object import (
    HookDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.inbox_deploy_object import (
    InboxDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.label_deploy_object import (
    LabelDeployObject,
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
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.run.merge.state import DeployState
from deployment_manager.commands.deploy.subcommands.run.models import (
    DeployException,
    LookupTable,
    ReverseLookupTable,
    Target,
    TargetWithDefault,
)
from deployment_manager.utils.consts import (
    CustomResource,
    display_error,
    display_info,
    display_warning,
    settings,
)
from deployment_manager.utils.functions import extract_id_from_url, gather_with_concurrency
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
    no_rebase: bool = False

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
    deploy_file_path: Path

    source_org: Organization
    target_org: Organization

    organization: OrganizationDeployObject = None
    workspaces: list[WorkspaceDeployObject] = []
    queues: list[QueueDeployObject] = []
    hooks: list[HookDeployObject] = []
    labels: list[LabelDeployObject] = []
    email_templates: list[EmailTemplateDeployObject] = []
    rules: list[RuleDeployObject] = []

    lookup_table: LookupTable = {}
    reverse_lookup_table: ReverseLookupTable = {}

    unselected_hooks: list[int] = []

    hook_templates: dict = {}
    queue_ignore_warnings: dict = {}

    ignore_all_deploy_warnings: bool = False

    # Auto-loaded dependency mappings (source_id -> target_id)
    auto_mappings: dict = {}

    @property
    def is_same_org(self):
        return self.source_org.id == self.target_org.id

    @property
    def deploy_objects(self) -> list[DeployObject]:
        return [
            self.organization,
            *self.hooks,
            *self.labels,
            *self.email_templates,
            *self.rules,
            *self.workspaces,
            *self.queues,
        ]

    def __init__(self, **data):
        super().__init__(**data)

        if self.secrets_file and (secrets_file_path := pathlib.Path(self.secrets_file)).exists():
            # Read and parse the secrets file
            self.secrets = json.loads(secrets_file_path.read_text())

        self.deploy_state = DeployState.load_deploy_state(path=pathlib.Path(self.deploy_state_file))

        # Load auto-mappings for auto-loaded dependencies
        self.auto_mappings = self.load_auto_mappings()

        self.organization = OrganizationDeployObject(
            id=self.source_org.id,
            name=self.source_org.name,
        )

    def get_auto_mappings_path(self) -> pathlib.Path:
        """Get path to the .auto/{deploy_file_name}.yaml file."""
        # Convert anyio.Path to pathlib.Path for sync operations
        deploy_path = pathlib.Path(str(self.deploy_file_path))
        auto_dir = deploy_path.parent / ".auto"
        auto_file = auto_dir / deploy_path.name
        return auto_file

    def load_auto_mappings(self) -> dict:
        """Load auto-dependency mappings from .auto/{deploy_file_name}.yaml."""
        auto_file = self.get_auto_mappings_path()
        try:
            if not auto_file.exists():
                return {}

            yaml = YAML()
            with open(auto_file, "r") as f:
                mappings = yaml.load(f) or {}
            return mappings
        except FileNotFoundError:
            return {}
        except Exception as e:
            display_warning(f"Could not load auto-mappings from {auto_file}: {e}")
            return {}

    async def save_auto_mappings(self):
        """Save auto-loaded dependency mappings to .auto/{deploy_file_name}.yaml."""
        # Build global mappings from auto-loaded labels and email_templates
        # Using global mappings (not per-rule) so that if rules are added/removed,
        # the target IDs are still found for shared dependencies
        mappings = {"labels": {}, "email_templates": {}}

        # Collect all label mappings
        for label in self.labels:
            if label.targets and label.targets[0].id:
                mappings["labels"][label.id] = label.targets[0].id

        # Collect all email_template mappings
        for email_template in self.email_templates:
            if email_template.targets and email_template.targets[0].id:
                mappings["email_templates"][email_template.id] = email_template.targets[0].id

        # Save to file if there are any mappings
        if mappings["labels"] or mappings["email_templates"]:
            auto_file = self.get_auto_mappings_path()
            auto_dir = auto_file.parent

            # Create .auto directory if it doesn't exist
            auto_dir.mkdir(exist_ok=True)

            try:
                yaml = YAML()
                yaml.indent(mapping=2, sequence=4, offset=2)
                with open(auto_file, "w") as f:
                    yaml.dump(mappings, f)
            except Exception as e:
                display_warning(f"Could not save auto-mappings to {auto_file}: {e}")

    async def save_deploy_state(self):
        """Save the last applied config for all deployed resources."""
        if not self.deploy_state_file:
            return

        schemas = [queue.schema_deploy_object for queue in self.queues]
        inboxes = [queue.inbox_deploy_object for queue in self.queues]

        deploy_state_objects = [
            (Resource.Organization, [self.organization]),
            (Resource.Hook, self.hooks),
            (Resource.Label, self.labels),
            (Resource.EmailTemplate, self.email_templates),
            (Resource.Queue, self.queues),
            (Resource.Schema, schemas),
            (CustomResource.Rule, self.rules),
            (Resource.Inbox, inboxes),
            (Resource.Workspace, self.workspaces),
        ]

        await self.deploy_state.update_deploy_state(
            objects=deploy_state_objects,
        )

        await self.deploy_state.write_deploy_state(Path(self.deploy_state_file))

    async def resolve_non_creatable_email_templates(self):
        """Resolve target IDs for non-creatable email template types.

        Non-creatable types (rejection_default, email_with_no_processable_attachments)
        are auto-created with every queue. After queues are deployed, we need to:
        1. Query the target queue's email templates
        2. Find the one matching by type
        3. Update our email template target with that ID
        4. Update the lookup table for rule reference replacement
        """
        for email_template in self.email_templates:
            if not email_template.non_creatable:
                continue

            source_queue_url = email_template.data.get("queue")
            if not source_queue_url:
                display_warning(
                    f"Non-creatable email template {email_template.display_label} has no queue reference, skipping"
                )
                continue

            source_queue_id = extract_id_from_url(source_queue_url)
            email_type = email_template.data.get("type")

            # Find the queue deploy object for this source queue
            queue_deploy_obj = None
            for queue in self.queues:
                if queue.id == source_queue_id:
                    queue_deploy_obj = queue
                    break

            if not queue_deploy_obj:
                display_warning(
                    f"Could not find queue {source_queue_id} for email template {email_template.display_label}. "
                    "The email template reference may not be replaced correctly."
                )
                continue

            # For each target queue, find the matching email template by type
            for i, queue_target in enumerate(queue_deploy_obj.targets):
                target_queue_id = queue_target.id
                if not target_queue_id:
                    display_warning(
                        f"Target queue ID not available for email template {email_template.display_label}, skipping"
                    )
                    continue

                try:
                    # Query target queue's email templates (fetch_all returns async generator)
                    target_template_id = None
                    async for template in self.client._http_client.fetch_all(
                        Resource.EmailTemplate,
                        params={"queue": target_queue_id},
                    ):
                        if template.get("type") == email_type:
                            target_template_id = template["id"]
                            break

                    if target_template_id:
                        # Update the email template target
                        if i < len(email_template.targets):
                            email_template.targets[i].id = target_template_id
                        else:
                            # Add new target if needed
                            email_template.targets.append(TargetWithDefault(id=target_template_id))

                        display_info(
                            f"Resolved non-creatable email template {email_template.display_label} "
                            f"(type: {email_type}) -> target ID {target_template_id}"
                        )
                    else:
                        display_warning(
                            f"Could not find email template with type '{email_type}' on target queue {target_queue_id}"
                        )

                except Exception as e:
                    display_warning(f"Could not fetch email templates for target queue {target_queue_id}: {e}")

    async def initialize_deploy_objects(self):
        await self.ensure_token_owner()

        await gather_with_concurrency(
            *[deploy_object.initialize_deploy_object(deploy_file=self) for deploy_object in self.deploy_objects],
        )

        for deploy_object in self.deploy_objects:
            if isinstance(deploy_object, QueueDeployObject):
                await deploy_object.prompt_pending_warnings()

        self.detect_phase_exceptions("initialize_failed")

    async def initialize_target_objects(self):
        try:
            await gather_with_concurrency(
                *[deploy_object.initialize_target_objects() for deploy_object in self.deploy_objects],
            )
        except Exception as e:
            display_error(f"Error during initialization of target objects: {e}")
            raise

        try:
            self.lookup_table = self.create_lookup_table()

            await gather_with_concurrency(
                *[
                    deploy_object.override_references(data_attribute="visualized_plan_data", use_dummy_references=True)
                    for deploy_object in self.deploy_objects
                ]
            )
        except Exception as e:
            display_error(f"Error during overriding references of target objects: {e}")
            raise

    async def compare_object_versions(self):
        try:
            self.reverse_lookup_table = self.create_reverse_lookup_table()

            for object in self.deploy_objects:
                if isinstance(object, OrganizationDeployObject) and not self.patch_target_org:
                    continue
                await object.compare_target_objects()

            # Need to pause execution of the command so the user can resolve them
            if any(object.conflict_detected for object in self.deploy_objects):
                display_warning(
                    "Conflicts detected: please go to the files listed above and resolve them.\n\n[bold]Do not exit this command, otherwise, you might be prompted to resolve the conflict again when source is compared to remote target.[/bold]"
                )
                if not await questionary.confirm("Confirm that conflicts were resolved.").ask_async():
                    raise DeployException("Please rerun the command once conflicts were resolved.")

            # Objects need to be reloaded from source and everything reapplied for them
            for object in self.deploy_objects:
                if not object.conflict_detected and not object.rebase_detected:
                    continue

                await object.initialize_deploy_object(deploy_file=self)
                await object.initialize_target_objects()
                await object.override_references(data_attribute="visualized_plan_data", use_dummy_references=True)
        except Exception as e:
            display_error(f"Error during comparison of prepared target objects with their remote versions: {e}")
            raise

    async def show_deploy_plan(self):
        try:
            for object in self.deploy_objects:
                if isinstance(object, OrganizationDeployObject) and not self.patch_target_org:
                    continue
                await object.visualize_changes()
        except Exception as e:
            display_error(f"Error during visualization of deploy plan changes: {e}")
            raise

    async def run_deploy(self, is_first: bool):
        try:
            data_attribute = "first_deploy_data" if is_first else "second_deploy_data"

            display_info(f"{'First' if is_first else 'Second'} deploy started.")

            if self.patch_target_org:
                await self.organization.deploy_target_objects(data_attribute=data_attribute)

            await gather_with_concurrency(
                *[deploy_object.deploy_target_objects(data_attribute=data_attribute) for deploy_object in self.hooks]
            )

            await gather_with_concurrency(
                *[deploy_object.deploy_target_objects(data_attribute=data_attribute) for deploy_object in self.labels]
            )

            await gather_with_concurrency(
                *[
                    deploy_object.deploy_target_objects(data_attribute=data_attribute)
                    for deploy_object in self.workspaces
                ]
            )

            await gather_with_concurrency(
                *[deploy_object.deploy_target_objects(data_attribute=data_attribute) for deploy_object in self.queues]
            )

            # After queues are deployed (first phase), resolve non-creatable email template targets
            if is_first:
                await self.resolve_non_creatable_email_templates()
                # Re-override email template references with the updated lookup table (queue refs)
                await gather_with_concurrency(
                    *[
                        et.override_references(data_attribute="second_deploy_data", use_dummy_references=False)
                        for et in self.email_templates
                    ]
                )

            # Email templates must be deployed AFTER queues (they require queue reference)
            await gather_with_concurrency(
                *[
                    deploy_object.deploy_target_objects(data_attribute=data_attribute)
                    for deploy_object in self.email_templates
                ]
            )

            # After email templates are deployed (first phase), re-override rule references
            # Now the email template targets have their IDs from deployment
            if is_first:
                await gather_with_concurrency(
                    *[
                        rule.override_references(data_attribute="second_deploy_data", use_dummy_references=False)
                        for rule in self.rules
                    ]
                )

            await gather_with_concurrency(
                *[deploy_object.deploy_target_objects(data_attribute=data_attribute) for deploy_object in self.rules]
            )

            display_info(f"{'First' if is_first else 'Second'} deploy finished.")

        except Exception as e:
            display_error(f"Error during {'first' if is_first else 'second'} deploy: {e}")
            raise

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
                error_objects.append(f"{deploy_object.display_type} {deploy_object.display_label}")

            if error_objects:
                raise DeployException(
                    "Error occurred for the following deploy objects, see error details above:\n"
                    + "\n".join(error_objects)
                )

    def create_lookup_table(self):
        lookup_table = defaultdict(dict)

        lookup_table[self.organization.id][Resource.Organization] = self.organization.targets

        for hook in self.hooks:
            lookup_table[hook.id][Resource.Hook] = hook.targets

        for label in self.labels:
            lookup_table[label.id][Resource.Label] = label.targets

        for email_template in self.email_templates:
            lookup_table[email_template.id][Resource.EmailTemplate] = email_template.targets

        for rule in self.rules:
            lookup_table[rule.id][CustomResource.Rule] = rule.targets

        for workspace in self.workspaces:
            lookup_table[workspace.id][Resource.Workspace] = workspace.targets

        for queue in self.queues:
            lookup_table[queue.id][Resource.Queue] = queue.targets

            lookup_table[queue.schema_deploy_object.id][Resource.Schema] = queue.schema_deploy_object.targets

            lookup_table[queue.inbox_deploy_object.id][Resource.Inbox] = queue.inbox_deploy_object.targets

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
            queue[settings.DEPLOY_KEY_IGNORE_DEPLOY_WARNINGS] = ignore_warning_map.get(queue_id, False)


# Pydantic needs this
DeployOrchestrator.model_rebuild()
OrganizationDeployObject.model_rebuild()
HookDeployObject.model_rebuild()
LabelDeployObject.model_rebuild()
EmailTemplateDeployObject.model_rebuild()
WorkspaceDeployObject.model_rebuild()
QueueDeployObject.model_rebuild()
SchemaDeployObject.model_rebuild()
InboxDeployObject.model_rebuild()
RuleDeployObject.model_rebuild()
Target.model_rebuild()
