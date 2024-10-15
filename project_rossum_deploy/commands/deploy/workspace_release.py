import asyncio
from copy import deepcopy
from anyio import Path
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.deploy.attribute_override import (
    override_attributes_v2,
)
from project_rossum_deploy.commands.deploy.object_release import ObjectRelease
from project_rossum_deploy.utils.consts import (
    display_error,
)
from project_rossum_deploy.utils.functions import templatize_name_id


class WorkspaceRelease(ObjectRelease):
    type: Resource = Resource.Workspace
    target_org_url: str = None

    async def initialize(self, yaml, client, target_org_url, source_dir_path):
        await super().initialize(yaml, client, source_dir_path)
        self.target_org_url = target_org_url

    @property
    def path(self) -> Path:
        return (
            Path(self.base_path)
            / self.type.value
            / templatize_name_id(self.name, self.id)
            / "workspace.json"
        )

    async def deploy(self):
        try:
            self.data["queues"] = []
            self.data["organization"] = self.target_org_url

            release_requests = []
            for target in self.targets:
                ws_copy = deepcopy(self.data)
                override_attributes_v2(
                    object=ws_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(object=ws_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)
            # asyncio.gather returns results in the same order as they were put in
            for index, (result, target) in enumerate(zip(results, self.targets)):
                target.id = result.get("id", None)
                target.data = result
                self.yaml_reference["targets"][index]["id"] = target.id

        except Exception as e:
            display_error(
                f"Error while migrating hook {self.name} ({self.path}): {e}", e
            )
