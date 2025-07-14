from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel
from rich import print as pprint
from rich.panel import Panel


if TYPE_CHECKING:
    from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (
        DeployOrchestrator,
    )
from deployment_manager.utils.consts import (
    display_error,
)
from deployment_manager.utils.functions import extract_id_from_url


from rossum_api.api_client import Resource


class HookDependenciesDeployer(BaseModel):
    deploy_file_reference: "DeployOrchestrator" = None

    async def migrate_hook_dependency_graph(self):
        if not len(self.deploy_file_reference.hooks):
            return

        pprint(Panel("Updating hook dependency graph..."))
        for hook_release in self.deploy_file_reference.hooks:
            try:
                for target_hook_index, target_hook in enumerate(hook_release.targets):
                    target_run_after = await self.migrate_target_hook_run_after(
                        target_hook_index=target_hook_index,
                        target_hook_count=len(hook_release.targets),
                        source_run_after=hook_release.data.get("run_after", []),
                    )
                    if self.deploy_file_reference.plan_only:
                        # TODO: visualize deps graphically
                        ...
                    else:
                        await self.deploy_file_reference.client._http_client.update(
                            Resource.Hook,
                            id_=target_hook.id,
                            data={"run_after": target_run_after},
                        )
            except Exception as e:
                display_error(
                    f"Error while migrating dependency graph for hook '{hook_release.name} ({hook_release.id})' ^",
                    e,
                )
        pprint(Panel("Hook dependency graph updated..."))

    async def migrate_target_hook_run_after(
        self,
        source_run_after: dict,
        target_hook_index: int,
        target_hook_count: int,
    ):
        target_run_after = []

        for predecessor_url in source_run_after:
            predecessor_id = extract_id_from_url(predecessor_url)
            predecessor_target_objects = self.deploy_file_reference.lookup_table.get(
                predecessor_id, {}
            ).get(Resource.Hook, [])

            if not len(predecessor_target_objects):
                target_run_after += await self.find_missing_hook_run_after(
                    predecessor_id=predecessor_id,
                    target_hook_index=target_hook_index,
                    target_hook_count=target_hook_count,
                )
            # Assume each newly created hook should have its own run_after
            elif target_hook_count == len(predecessor_target_objects):
                new_url = predecessor_url.replace(
                    str(predecessor_id),
                    str(predecessor_target_objects[target_hook_index].id),
                )
                target_run_after.append(new_url)
            # All hooks will have the same single run_after
            else:
                new_url = predecessor_url.replace(
                    str(predecessor_id),
                    str(predecessor_target_objects[0].id),
                )
                target_run_after.append(new_url)

        return target_run_after

    async def find_missing_hook_run_after(
        self,
        predecessor_id: int,
        target_hook_index: int,
        target_hook_count: int,
    ):
        # The predecessor hook was ignored, it has no targets equivalent
        # Take the predecessor's source and find its predecessor (if none, stop)
        # Find the predecessors' target and put that into run_after for this hook
        # If there is no target, repeat from line one
        try:
            predecessor = await self.deploy_file_reference.client.retrieve_hook(
                predecessor_id
            )
        except Exception as e:
            display_error(
                f'Error while finding predecessor hook with ID "{predecessor_id}" in Rossum.',
                e,
            )
            return []

        return await self.migrate_target_hook_run_after(
            source_run_after=predecessor.run_after,
            target_hook_index=target_hook_index,
            target_hook_count=target_hook_count,
        )
