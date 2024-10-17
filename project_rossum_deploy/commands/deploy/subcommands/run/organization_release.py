from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
)
from project_rossum_deploy.utils.consts import display_error

from rossum_api.models.organization import Organization
from rossum_api.api_client import Resource
from copy import deepcopy


class OrganizationRelease(ObjectRelease):
    type: Resource = Resource.Organization
    target_org: Organization

    # Override parent object method
    async def initialize(self): ...

    async def deploy(self):
        if self.data["id"] == self.target_org.id:
            return

        try:
            org_copy = deepcopy(self.data)
            org_copy["name"] = self.target_org.name

            await self.client._http_client.update(
                self.type, id=self.target_org.id, data=org_copy
            )
        except Exception as e:
            display_error(
                f'Error while updating {self.display_type} "{self.name} ({self.id})"  -> "{self.target_org.name} ({self.target_org.id})"',
                e,
            )
