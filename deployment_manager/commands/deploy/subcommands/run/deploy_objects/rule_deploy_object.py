from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.email_template_deploy_object import (
    EmailTemplateDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.label_deploy_object import LabelDeployObject
from deployment_manager.commands.deploy.subcommands.run.models import TargetWithDefault
from deployment_manager.common.read_write import read_object_from_json
from deployment_manager.utils.consts import CustomResource, display_warning, settings
from deployment_manager.utils.functions import extract_id_from_url, find_local_object_path_by_id


class RuleDeployObject(DeployObject):
    type: Resource = Resource.Rule

    skipped: bool = False
    # Track if second_deploy_data references have been overridden
    # (happens in orchestrator after queues/email_templates are deployed)
    second_deploy_references_overridden: bool = False

    async def initialize_deploy_object(self, deploy_file):
        await super().initialize_deploy_object(deploy_file)

        # Ignore deprecated fields
        self.ignored_attributes.extend(["rule_template", "synchronized_from_template"])

        # Skip schema-based rules
        if self.data.get("schema"):
            display_warning(
                f"Rule {self.display_label} uses deprecated schema-based assignment and will be skipped. "
                "Please update the rule to use queue-based assignment."
            )
            self.skipped = True
            return

        # Remove deprecated fields
        self.data.pop("rule_template", None)
        self.data.pop("synchronized_from_template", None)

        # Auto-detect and load label/email_template dependencies
        await self.auto_load_action_dependencies()

    async def initialize_target_objects(self):
        if self.skipped:
            return
        await super().initialize_target_objects()

    async def deploy_target_objects(self, data_attribute: str):
        if self.skipped:
            return
        await super().deploy_target_objects(data_attribute)

    async def override_references(self, data_attribute: str, use_dummy_references: bool):
        if self.skipped:
            return
        await super().override_references(data_attribute, use_dummy_references)
        # Mark that second_deploy_data references have been explicitly overridden
        # This prevents redundant override in deploy_target_objects
        if data_attribute == "second_deploy_data" and not use_dummy_references:
            self.second_deploy_references_overridden = True

    async def compare_target_objects(self):
        if self.skipped:
            return
        await super().compare_target_objects()

    async def visualize_changes(self):
        if self.skipped:
            return
        await super().visualize_changes()

    def get_target_ids_from_auto_mappings(self, resource_type: Resource, source_id: int) -> list[int]:
        """Get target IDs for a source ID from auto-mappings or deploy state."""
        # Check auto-mappings first (stored in .auto/{deploy_file}.yaml)
        # Mappings are stored globally (not per-rule) so shared dependencies work
        # even when rules are added/removed
        resource_mappings = self.deploy_file.auto_mappings.get(resource_type.value, {})
        target_id = resource_mappings.get(source_id)
        if target_id:
            return [target_id]

        # Fallback to deploy state for backwards compatibility
        state_map = getattr(self.deploy_file.deploy_state, resource_type.value, {})
        resource_deployments = state_map.get(source_id)
        if resource_deployments:
            return list(resource_deployments.deployments.keys())

        return []

    async def auto_load_action_dependencies(self):
        """Automatically detect and load labels and email templates referenced in rule actions.

        Normally the referenced objects are fetched from the source organization. Under local
        deploy (--ld) they are instead read from the locally pulled files (see _get_label_data /
        _get_email_template_data), so no source-organization API call is made.
        """
        label_ids = set()
        email_template_ids = set()

        # Scan all actions for dependencies
        for action in self.data.get("actions", []):
            payload = action.get("payload", {})
            action_type = action.get("type", "")

            # Extract label references
            if action_type in ["add_label", "add_remove_label"]:
                for label_url in payload.get("labels", []):
                    label_id = extract_id_from_url(label_url)
                    if label_id:
                        label_ids.add(label_id)

            # Extract email_template references
            elif action_type == "send_email":
                email_template_url = payload.get("email_template")
                if email_template_url:
                    email_template_id = extract_id_from_url(email_template_url)
                    if email_template_id:
                        email_template_ids.add(email_template_id)

        # Fetch and create label deploy objects
        for label_id in label_ids:
            # Check at fetch time to handle concurrent rule initialization
            if any(label.id == label_id for label in self.deploy_file.labels):
                continue
            try:
                label_data = await self._get_label_data(label_id)
                if not label_data:
                    display_warning(
                        f"Could not load label {label_id} referenced in rule {self.display_label}. "
                        "The reference may not be replaced correctly."
                    )
                    continue

                # Re-check after async fetch to reduce duplicates from concurrent rules
                if any(label.id == label_id for label in self.deploy_file.labels):
                    continue

                # Check if this label was previously deployed
                target_ids = self.get_target_ids_from_auto_mappings(CustomResource.Label, label_id)
                if target_ids:
                    # Use existing target IDs from previous deployments
                    targets = [TargetWithDefault(id=target_id) for target_id in target_ids]
                else:
                    # Create new on target
                    targets = [TargetWithDefault(id=None)]

                label_deploy_obj = LabelDeployObject(
                    id=label_id,
                    name=label_data.get("name", f"label-{label_id}"),
                    data=label_data,
                    targets=targets,
                )
                await label_deploy_obj.initialize_deploy_object(deploy_file=self.deploy_file)
                self.deploy_file.labels.append(label_deploy_obj)
            except Exception as e:
                display_warning(
                    f"Could not load label {label_id} referenced in rule {self.display_label}: {e}. "
                    "The reference may not be replaced correctly."
                )

        # Fetch and create email template deploy objects
        for email_template_id in email_template_ids:
            # Check at fetch time to handle concurrent rule initialization
            if any(et.id == email_template_id for et in self.deploy_file.email_templates):
                continue
            try:
                email_template_data = await self._get_email_template_data(email_template_id)
                if not email_template_data:
                    display_warning(
                        f"Could not load email template {email_template_id} referenced in rule {self.display_label}. "
                        "The reference may not be replaced correctly."
                    )
                    continue

                # Re-check after async fetch to reduce duplicates from concurrent rules
                if any(et.id == email_template_id for et in self.deploy_file.email_templates):
                    continue

                # Check if this email template was previously deployed
                target_ids = self.get_target_ids_from_auto_mappings(Resource.EmailTemplate, email_template_id)
                if target_ids:
                    # Use existing target IDs from previous deployments
                    targets = [TargetWithDefault(id=target_id) for target_id in target_ids]
                else:
                    # Match the parent queue's target count
                    target_count = 1
                    source_queue_url = email_template_data.get("queue")
                    if source_queue_url:
                        source_queue_id = extract_id_from_url(source_queue_url)
                        for queue in self.deploy_file.queues:
                            if queue.id == source_queue_id:
                                target_count = len(queue.targets)
                                break
                    targets = [TargetWithDefault(id=None) for _ in range(target_count)]

                email_template_deploy_obj = EmailTemplateDeployObject(
                    id=email_template_id,
                    name=email_template_data.get("name", f"email-template-{email_template_id}"),
                    data=email_template_data,
                    targets=targets,
                )
                await email_template_deploy_obj.initialize_deploy_object(deploy_file=self.deploy_file)
                self.deploy_file.email_templates.append(email_template_deploy_obj)
            except Exception as e:
                display_warning(
                    f"Could not load email template {email_template_id} referenced in rule {self.display_label}: {e}. "
                    "The reference may not be replaced correctly."
                )

    async def _get_label_data(self, label_id: int) -> dict | None:
        """Resolve a label referenced by a rule action.

        Local deploy (--ld) reads it from the locally pulled `labels/` folder; otherwise it is
        fetched from the source organization.
        """
        if self.deploy_file.local_deploy:
            labels_dir = self.deploy_file.source_dir_path / settings.LABELS_DIR_NAME
            return await self._find_local_object_data_by_id(labels_dir, label_id)
        return await self.deploy_file.source_client._http_client.fetch_one(CustomResource.Label, label_id)

    async def _get_email_template_data(self, email_template_id: int) -> dict | None:
        """Resolve an email template referenced by a rule action.

        Local deploy (--ld) reads it from the locally pulled
        `workspaces/<workspace>/queues/<queue>/email_templates/` folders; otherwise it is fetched
        from the source organization.
        """
        if self.deploy_file.local_deploy:
            return await self._find_local_object_data_by_id(
                self.deploy_file.source_dir_path,
                email_template_id,
                glob_pattern=f"workspaces/*/queues/*/{settings.EMAIL_TEMPLATES_DIR_NAME}/*.json",
            )
        return await self.deploy_file.source_client._http_client.fetch_one(Resource.EmailTemplate, email_template_id)

    async def _find_local_object_data_by_id(
        self, search_dir, object_id: int, glob_pattern: str = "*.json"
    ) -> dict | None:
        """Read a locally pulled object by its id (used by local deploy --ld). ``None`` if not found."""
        path = await find_local_object_path_by_id(search_dir, object_id, glob_pattern)
        if not path:
            return None
        return await read_object_from_json(path, False)

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
        # Already overridden by orchestrator
        if data_attribute == "second_deploy_data" and self.second_deploy_references_overridden:
            return

        data = getattr(target, data_attribute)

        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="organization",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Organization,
            use_dummy_references=use_dummy_references,
        )

        self.ref_replacer.replace_list_of_reference_urls(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="queues",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Queue,
            use_dummy_references=use_dummy_references,
        )
        await self.persist_target_only_references(
            target=target,
            data_attribute=data_attribute,
            dependency_name="queues",
        )
