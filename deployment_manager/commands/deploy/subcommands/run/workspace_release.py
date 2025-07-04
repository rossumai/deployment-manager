import asyncio
from copy import deepcopy
from anyio import Path
from rossum_api.api_client import Resource

from deployment_manager.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
    PathNotFoundException,
)
from deployment_manager.utils.consts import (
    display_error,
)
from deployment_manager.utils.functions import templatize_name_id


class WorkspaceRelease(ObjectRelease):
    type: Resource = Resource.Workspace
    target_org_url: str = None

    async def initialize(self, target_org_url, **kwargs):
        try:
            await super().initialize(**kwargs)
            self.target_org_url = target_org_url
        except Exception as e:
            display_error(
                f"Error while initializing {self.display_type} {self.display_label}: {e}",
                None if isinstance(e, PathNotFoundException) else e,
            )
            self.initialize_failed = True

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
                    object=ws_copy, attribute_overrides=target.attribute_override, global_overrides=target.global_override
                )

                request = self.upload(target_object=ws_copy, target=target)
                release_requests.append(request)

            if self.plan_only:
                results = []
                # Run sequentially when planning because user may have to input things in the CLI
                for request in release_requests:
                    results.append(await request)
            else:
                results = await asyncio.gather(*release_requests)

            self.update_targets(results)
        except Exception as e:
            display_error(
                f"Error while deploying {self.display_type} {self.display_label}: {e}",
                e,
            )
            self.deploy_failed = True
