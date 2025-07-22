from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)
from deployment_manager.utils.consts import CustomResource


from deployment_manager.utils.functions import templatize_name_id
from rossum_api.api_client import Resource


class RuleDeployObject(DeployObject):
    type: CustomResource = CustomResource.Rule

    parent_schema: DeployObject = None

    async def initialize_deploy_object(self, deploy_file, parent_schema):
        # Must come first
        self.parent_schema = parent_schema
        await super().initialize_deploy_object(deploy_file)

    @property
    def path(self) -> Path:
        return (
            self.parent_schema.path.parent
            / "rules"
            / f"{templatize_name_id(self.name, self.id)}.json"
        )

    def get_object_in_yaml(self):
        parent_yaml_reference = self.parent_schema.yaml_reference
        rules = parent_yaml_reference.get("rules", [])
        for rule in rules:
            if rule.get("id", None) == self.id:
                return rule
        return None

    async def override_references_in_target_object_data(
        self, data_attribute, target, use_dummy_references
    ):
        data = getattr(target, data_attribute)
        # previous_schema_url = data["schema"]

        # Elis API does not accept fake IDs for rules unlike other objects
        data.pop('id', None)

        self.ref_replacer.replace_reference_url(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="schema",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Schema,
            use_dummy_references=use_dummy_references,
        )

        # if previous_schema_url == data["schema"] and not target.id:
        #     raise Exception(
        #         f'Cannot create target for {self.display_type} "{self.display_label}" - there is no target schema to use it with.'
        #     )
