import asyncio
from copy import deepcopy
from anyio import Path
from rossum_api.api_client import Resource

from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
)
from deployment_manager.utils.consts import (
    display_error,
)
from deployment_manager.utils.functions import templatize_name_id


class WorkspaceRelease(ObjectRelease):
    type: Resource = Resource.Workspace
    target_org_url: str = None

    async def initialize(
        self,
        yaml,
        client,
        target_org_url,
        source_dir_path,
        plan_only,
        is_same_org_deploy,
    ):
        await super().initialize(
            yaml=yaml,
            client=client,
            source_dir_path=source_dir_path,
            plan_only=plan_only,
            is_same_org_deploy=is_same_org_deploy,
        )
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
            release_requests = []
            for target in self.targets:
                ws_copy = deepcopy(self.data)
                ws_copy["queues"] = []
                ws_copy["organization"] = self.target_org_url
                self.overrider.override_attributes_v2(
                    object=ws_copy, attribute_overrides=target.attribute_override
                )

                request = self.upload(target_object=ws_copy, target=target)
                release_requests.append(request)

            results = await asyncio.gather(*release_requests)

            self.update_targets(results)
        except Exception as e:
            display_error(
                f"Error while migrating {self.display_type} {self.name} ({self.id}) ^",
                e,
            )
