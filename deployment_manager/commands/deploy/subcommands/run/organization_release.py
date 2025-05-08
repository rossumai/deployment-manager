from anyio import Path
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    Target,
)
from deployment_manager.utils.consts import display_error

from deployment_manager.utils.functions import templatize_name_id
from rossum_api.models.organization import Organization
from rossum_api.api_client import Resource
from copy import deepcopy


class OrganizationRelease(ObjectRelease):
    type: Resource = Resource.Organization
    target_org: Organization

    patch_org: bool = False

    @property
    def path(self) -> Path:
        return Path(self.base_path) / "organization.json"

    async def deploy(self):
        try:
            self.targets = [Target(id=self.target_org.id)]

            org_copy = deepcopy(self.data)
            org_copy["name"] = self.target_org.name

            result = await self.update_remote(
                target_object=org_copy, target=self.targets[0]
            )

            self.targets[0].data = result
        except Exception as e:
            display_error(
                f'Error while deploying {self.display_type} "{self.name} ({self.id})"  -> "{self.target_org.name} ({self.target_org.id}) ^"',
                e,
            )
            self.deploy_failed = True
