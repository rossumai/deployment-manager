from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)
from deployment_manager.utils.consts import display_error

from rossum_api.models.organization import Organization
from rossum_api.api_client import Resource
from copy import deepcopy


class OrganizationRelease(ObjectRelease):
    type: Resource = Resource.Organization
    target_org: Organization

    patch_org: bool = False

    # Override parent object method
    async def initialize(self): ...

    async def deploy(self):
        try:
            org_copy = deepcopy(self.data)
            org_copy["name"] = self.target_org.name

            await self.update_remote(
                target_object=org_copy, target=Target(id=self.target_org.id)
            )
        except Exception as e:
            display_error(
                f'Error while deploying {self.display_type} "{self.name} ({self.id})"  -> "{self.target_org.name} ({self.target_org.id}) ^"',
                e,
            )
            self.deploy_failed = True
