from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object import (
    DeployObject,
)

from deployment_manager.commands.deploy.subcommands.run.models import Target
from rossum_api.domain_logic.resources import Resource


class OrganizationDeployObject(DeployObject):
    type: Resource = Resource.Organization

    @property
    def path(self) -> Path:
        return Path(self.deploy_file.source_dir_path.parent) / "organization.json"

    async def initialize_deploy_object(self, deploy_file):
        await super().initialize_deploy_object(deploy_file)

        org_target = Target(
            id=self.deploy_file.target_org.id,
            index=0,
        )
        self.targets = [org_target]

    async def initialize_target_object_data(self, data, target):
        data["name"] = self.deploy_file.target_org.name

    async def override_references_in_target_object_data(
        self, data_attribute, target, use_dummy_references
    ):
        data = getattr(target, data_attribute)
        self.ref_replacer.replace_list_of_reference_urls(
            object=data,
            target_index=target.index,
            target_objects_count=len(self.targets),
            dependency_name="workspaces",
            lookup_table=self.deploy_file.lookup_table,
            reverse_lookup_table=self.deploy_file.reverse_lookup_table,
            object_type=Resource.Workspace,
            use_dummy_references=use_dummy_references,
        )
        await self.persist_target_only_references(
            target=target, data_attribute=data_attribute, dependency_name="workspaces"
        )

    # Override method to do nothing
    def update_targets(self): ...
