from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject
from rossum_api.api_client import Resource

# These types are auto-created with every queue and cannot be manually created
NON_CREATABLE_EMAIL_TEMPLATE_TYPES = ["rejection_default", "email_with_no_processable_attachments"]


class EmailTemplateDeployObject(DeployObject):
    type: Resource = Resource.EmailTemplate

    # See NON_CREATABLE_EMAIL_TEMPLATE_TYPES
    non_creatable: bool = False

    async def initialize_deploy_object(self, deploy_file):
        await super().initialize_deploy_object(deploy_file)
        # Organization is set automatically by the API based on queue, shouldn't be sent
        self.ignored_attributes.append("organization")
        # Triggers are queue-specific and auto-created, can't be copied between queues
        self.ignored_attributes.append("triggers")

        # Check if this is a non-creatable type
        if self.data and self.data.get("type") in NON_CREATABLE_EMAIL_TEMPLATE_TYPES:
            self.non_creatable = True

    async def deploy_target_objects(self, data_attribute: str):
        # Non-creatable types are resolved after queue deployment, not deployed directly
        if self.non_creatable:
            return
        await super().deploy_target_objects(data_attribute)

    async def visualize_changes(self):
        # Non-creatable types are not deployed, so don't show them in plan
        if self.non_creatable:
            return
        await super().visualize_changes()

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
        data = getattr(target, data_attribute)

        # Replace queue reference
        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="queue",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Queue,
            use_dummy_references=use_dummy_references,
            allow_empty_reference=True,
        )
