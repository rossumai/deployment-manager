from typing import Optional

import questionary
from anyio import Path
from pydantic import Field

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
    EmptyDeployObject,
)
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.inbox_deploy_object import InboxDeployObject
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.schema_deploy_object import SchemaDeployObject
from deployment_manager.commands.deploy.subcommands.run.helpers import remove_queue_attributes_for_cross_org
from deployment_manager.commands.deploy.subcommands.run.models import SubObjectException, Target
from deployment_manager.utils.consts import QUEUE_ENGINE_ATTRIBUTES, display_error, display_warning
from deployment_manager.utils.functions import extract_id_from_url, templatize_name_id
from rossum_api.api_client import Resource


class QueueDeployObject(DeployObject):
    base_path: str
    type: Resource = Resource.Queue
    keep_hook_dependencies_without_equivalent: bool = False

    ignore_deploy_warnings: bool = False
    pending_warnings: list[str] = Field(default_factory=list)

    overwrite_ignored_fields: bool = False

    schema_deploy_object: SchemaDeployObject = Field(alias="schema")
    inbox_deploy_object: Optional[InboxDeployObject] = Field(
        default_factory=lambda: EmptyDeployObject(type=Resource.Inbox), alias="inbox"
    )

    unselected_hooks: list[int] = []

    async def initialize_deploy_object(
        self,
        deploy_file,
    ):
        await super().initialize_deploy_object(deploy_file)

        # Ignore read-only 'rules' field
        self.ignored_attributes.append("rules")

        await self.schema_deploy_object.initialize_deploy_object(
            deploy_file=self.deploy_file,
            parent_queue=self,
        )
        await self.inbox_deploy_object.initialize_deploy_object(
            deploy_file=self.deploy_file,
            parent_queue=self,
        )

        self.verify_queue_settings_are_compatible()
        await self.verify_subobjects_have_same_target_count()
        self.pending_warnings = []
        self.collect_unassigned_hooks_warning()
        self.collect_workflow_warning()
        self.collect_engine_warnings()

        if self.schema_deploy_object.initialize_failed or self.inbox_deploy_object.initialize_failed:
            self.initialize_failed = True

    @property
    def path(self) -> Path:
        return Path(self.base_path) / "queues" / templatize_name_id(self.name, self.id) / "queue.json"

    # Overrides the parent method
    async def initialize_target_objects(self):
        await super().initialize_target_objects()

        await self.schema_deploy_object.initialize_target_objects()
        await self.inbox_deploy_object.initialize_target_objects()

    async def initialize_target_object_data(self, data: dict, target: Target):
        if not self.deploy_file.is_same_org:
            remove_queue_attributes_for_cross_org(queue_copy=data)

        # Remove read-only 'rules' field
        data.pop("rules", None)

        if not self.overwrite_ignored_fields:
            # Ignore should preceed attribute override, so that override can win if it is defined
            await self.ignore_ai_fields(queue=data, target=target)

    async def override_references(self, data_attribute, use_dummy_references):
        await super().override_references(data_attribute, use_dummy_references)

        await self.schema_deploy_object.override_references(
            data_attribute=data_attribute, use_dummy_references=use_dummy_references
        )
        await self.inbox_deploy_object.override_references(
            data_attribute=data_attribute, use_dummy_references=use_dummy_references
        )

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
        data = getattr(target, data_attribute)
        # previous_workspace_url = data["workspace"]
        # previous_schema_url = data["schema"]

        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="workspace",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Workspace,
            # Workspace can theoretically be shared between source/target if in the same org
            keep_dependency_without_equivalent=self.deploy_file.is_same_org,
            use_dummy_references=use_dummy_references,
        )

        # if (
        #     previous_workspace_url == data["workspace"]
        #     and not target.exists_on_remote
        # ):
        #     raise Exception(
        #         f'Cannot create target for {self.display_type} "{target.display_label}" - there is no target workspace to put it into.'
        #     )

        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="schema",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Schema,
            # Schema can theoretically be shared between source/target if in the same org
            keep_dependency_without_equivalent=self.deploy_file.is_same_org,
            use_dummy_references=use_dummy_references,
        )

        # TODO: handle inbox not specified in deploy file (should not be replicated) but exists on source vs source inbox has no target ID (error)
        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="inbox",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Inbox,
            # Inbox cannot be assigned to multiple queues
            keep_dependency_without_equivalent=False,
            use_dummy_references=use_dummy_references,
            # Inbox needs queue reference, so queue must be created first
            # But this means we do not know the inbox ID yet
            allow_empty_reference=True,
        )

        # if previous_schema_url == data["schema"] and not target.exists_on_remote:
        #     raise Exception(
        #         f'Cannot create target for {self.display_type} "{target.display_label}" - there is no target schema to use it with.'
        #     )

        # Both should be updated, otherwise Elis API uses 'webhooks' in case of a mismatch even though it is deprecated
        self.ref_replacer.replace_list_of_reference_urls(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="hooks",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Hook,
            keep_dependencies_without_equivalent=self.keep_hook_dependencies_without_equivalent,
            use_dummy_references=use_dummy_references,
        )
        self.ref_replacer.replace_list_of_reference_urls(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="webhooks",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Hook,
            keep_dependencies_without_equivalent=self.keep_hook_dependencies_without_equivalent,
            use_dummy_references=use_dummy_references,
        )

        await self.persist_target_only_references(target=target, data_attribute=data_attribute, dependency_name="hooks")
        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="webhooks"
        )

        for engine_attr in QUEUE_ENGINE_ATTRIBUTES:
            self.ref_replacer.replace_reference_url(
                object=data,
                target_index=target.index,
                target_objects_count=len(self.targets),
                dependency_name=engine_attr,
                lookup_table=self.deploy_file.lookup_table,
                reverse_lookup_table=self.deploy_file.reverse_lookup_table,
                object_type=Resource.Engine,
                keep_dependency_without_equivalent=self.deploy_file.is_same_org,
                use_dummy_references=use_dummy_references,
                allow_empty_reference=True,
            )

    async def visualize_changes(self):
        await super().visualize_changes()

        await self.schema_deploy_object.visualize_changes()
        await self.inbox_deploy_object.visualize_changes()

    async def deploy_target_objects(self, data_attribute):
        try:
            await self.schema_deploy_object.deploy_target_objects(data_attribute=data_attribute)

            if self.schema_deploy_object.deploy_failed:
                raise SubObjectException()

            await super().deploy_target_objects(data_attribute)

            await self.inbox_deploy_object.deploy_target_objects(data_attribute=data_attribute)

            if self.inbox_deploy_object.deploy_failed:
                raise SubObjectException()
        except SubObjectException:
            self.deploy_failed = True
        except Exception as e:
            display_error(
                f"Error while deploying {self.display_type} {self.display_label}: {e}",
                e,
            )
            self.deploy_failed = True

    def verify_queue_settings_are_compatible(self):
        if self.keep_hook_dependencies_without_equivalent and not self.deploy_file.is_same_org:
            raise Exception(
                f'{self.display_type} {self.display_label} Cannot use "keep_hook_dependencies_without_equivalent: true" if source/target organizations are different.'
            )

    async def verify_subobjects_have_same_target_count(self):
        mismatch_found = False

        queue_targets_len = len(self.targets)
        schema_targets_len = len(self.schema_deploy_object.targets)

        if queue_targets_len != schema_targets_len:
            display_error(
                f"{self.display_type} {self.display_label} has {queue_targets_len} targets while its {self.schema_deploy_object.display_type} has {schema_targets_len}. Please make the target counts equal."
            )
            mismatch_found = True

        inbox_targets_len = len(self.inbox_deploy_object.targets)
        queue_has_inbox = bool(self.data.get("inbox", "")) and self.inbox_deploy_object.id
        if queue_has_inbox and queue_targets_len != inbox_targets_len:
            display_error(
                f"{self.display_type} {self.display_label} has {queue_targets_len} targets while its {self.inbox_deploy_object.display_type} has {inbox_targets_len}. Please make the target counts equal."
            )
            mismatch_found = True

        if mismatch_found:
            raise SubObjectException("Incorrect inbox/schema target count vs queue target count")

    def collect_unassigned_hooks_warning(self):
        if self.deploy_file.ignore_all_deploy_warnings or self.ignore_deploy_warnings:
            return

        queue_hook_urls = self.data.get("hooks", [])
        queue_hook_ids = [extract_id_from_url(url) for url in queue_hook_urls]

        deployed_hook_ids = set(hook.id for hook in self.deploy_file.hooks) | set(self.deploy_file.unselected_hooks)

        for queue_hook_id in queue_hook_ids:
            if queue_hook_id not in deployed_hook_ids:
                self.pending_warnings.append(
                    f"{self.display_type} {self.display_label} depends on hook [purple]{queue_hook_id}[/purple] that is not in the deploy file - is this a new hook created after the deploy file?"
                )
                return

    def collect_workflow_warning(self):
        if self.deploy_file.ignore_all_deploy_warnings or self.ignore_deploy_warnings or self.deploy_file.is_same_org:
            return

        if self.data.get("workflows", []):
            self.pending_warnings.append(
                f"{self.display_type} {self.display_label} has 'workflows' defined. Please make sure to create and assign them manually for the target."
            )

    def collect_engine_warnings(self):
        if self.deploy_file.ignore_all_deploy_warnings or self.ignore_deploy_warnings or self.deploy_file.is_same_org:
            return

        for attr in QUEUE_ENGINE_ATTRIBUTES:
            if self.data.get(attr, None):
                self.pending_warnings.append(
                    f"{self.display_type} {self.display_label} has '{attr}' defined. Please make sure to create and assign it manually for the target."
                )
                return

    async def prompt_pending_warnings(self):
        if not self.pending_warnings or self.deploy_file.ignore_all_deploy_warnings:
            return

        for warning in self.pending_warnings:
            if self.deploy_file.ignore_all_deploy_warnings:
                self.ignore_deploy_warnings = True
                return

            display_warning(warning)

            user_answer = await questionary.text(
                message="Do you want to disable warnings like this for this queue?",
                instruction="(y/n/yy)",
            ).ask_async()

            if user_answer.casefold() == "yy":
                self.deploy_file.ignore_all_deploy_warnings = True
                self.ignore_deploy_warnings = True
                return
            elif user_answer.casefold() == "y":
                return

    async def ignore_ai_fields(self, queue: dict, target: Target):
        # Object was not deployed to this target yet -> no AI fields to preserve in target
        if not target.exists_on_remote:
            return

        try:
            target_queue = await self.deploy_file.client.retrieve_queue(target.id)
            queue["automation_enabled"] = target_queue.automation_enabled
            queue["automation_level"] = target_queue.automation_level
            queue["default_score_threshold"] = target_queue.default_score_threshold

            queue.get("settings", {})["columns"] = target_queue.settings.get("columns", [])
            queue.get("settings", {})["annotation_list_table"] = target_queue.settings.get("annotation_list_table", {})

        except Exception as e:
            raise Exception("Error while ignoring queue AI fields") from e
