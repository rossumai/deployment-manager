from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import DeployObject
from rossum_api.api_client import Resource


class LabelDeployObject(DeployObject):
    type: Resource = Resource.Label

    async def initialize_deploy_object(self, deploy_file):
        await super().initialize_deploy_object(deploy_file)
        # Organization is set automatically by the API, shouldn't be sent
        self.ignored_attributes.append("organization")

    async def override_references_in_target_object_data(self, data_attribute, target, use_dummy_references):
        # Labels only have organization reference which is ignored (auto-set by API)
        pass
