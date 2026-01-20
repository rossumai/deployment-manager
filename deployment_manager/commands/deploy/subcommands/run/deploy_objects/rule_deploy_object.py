from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject
from deployment_manager.utils.consts import CustomResource, display_warning
from rossum_api.api_client import Resource


class RuleDeployObject(DeployObject):
    type: CustomResource = CustomResource.Rule

    skipped: bool = False

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

    async def compare_target_objects(self):
        if self.skipped:
            return
        await super().compare_target_objects()

    async def visualize_changes(self):
        if self.skipped:
            return
        await super().visualize_changes()

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
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
