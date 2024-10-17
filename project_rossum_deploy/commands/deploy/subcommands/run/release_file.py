import questionary
from project_rossum_deploy.commands.deploy.subcommands.run.hook_release import (
    HookRelease,
)
from project_rossum_deploy.commands.deploy.subcommands.run.queue_release import (
    QueueRelease,
)
from project_rossum_deploy.commands.deploy.subcommands.run.schema_release import (
    SchemaRelease,
)
from project_rossum_deploy.commands.deploy.subcommands.run.workspace_release import (
    WorkspaceRelease,
)
from project_rossum_deploy.commands.migrate.helpers import get_token_owner
from project_rossum_deploy.utils.consts import display_error
from project_rossum_deploy.utils.functions import extract_id_from_url
from project_rossum_deploy.utils.consts import settings


from pydantic import BaseModel
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource


class ReleaseFile(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    patch_target_org: bool = True
    token_owner_id: str = ""
    deployed_org_id: int = None

    client: ElisAPIClient

    workspaces: list[WorkspaceRelease] = []
    queues: list[QueueRelease] = []
    hooks: list[HookRelease] = []
    schemas: list[SchemaRelease] = []

    async def ensure_token_owner(self):
        if not settings.IS_PROJECT_IN_SAME_ORG:
            if not self.token_owner_id:
                token_owner_from_remote = await get_token_owner(self.client)
                if token_owner_from_remote:
                    self.token_owner_id = token_owner_from_remote.id
                else:
                    self.token_owner_id = await questionary.text(
                        "Please input user ID of the hook token owner (e.g., 938382):"
                    ).ask_async()

    async def migrate_hook_dependency_graph(
        self,
        hook_targets: dict[int, list],
    ):
        for hook_release in self.hooks:
            try:
                for target_hook_index, target_hook in enumerate(hook_release.targets):
                    target_run_after = await self.migrate_target_hook_run_after(
                        target_hook_index=target_hook_index,
                        target_hook_count=len(hook_release.targets),
                        source_run_after=hook_release.data.get("run_after", []),
                        hook_targets=hook_targets,
                    )
                    await self.client._http_client.update(
                        Resource.Hook,
                        id_=target_hook.id,
                        data={"run_after": target_run_after},
                    )
            except Exception as e:
                display_error(
                    f"Error while migrating dependency graph for hook '{hook_release.name} ({hook_release.id})' ^",
                    e,
                )

    async def migrate_target_hook_run_after(
        self,
        source_run_after: dict,
        target_hook_index: int,
        target_hook_count: int,
        hook_targets: dict[int, list],
    ):
        target_run_after = []

        for predecessor_url in source_run_after:
            predecessor_id = extract_id_from_url(predecessor_url)
            predecessor_target_objects = hook_targets.get(predecessor_id, [])

            if not len(predecessor_target_objects):
                target_run_after += await self.find_missing_hook_run_after(
                    predecessor_id=predecessor_id,
                    target_hook_index=target_hook_index,
                    target_hook_count=target_hook_count,
                    hook_targets=hook_targets,
                )
            # Assume each newly created hook should have its own run_after
            elif target_hook_count == len(predecessor_target_objects):
                new_url = predecessor_url.replace(
                    str(predecessor_id),
                    str(predecessor_target_objects[target_hook_index]["id"]),
                )
                target_run_after.append(new_url)
            # All hooks will have the same single run_after
            else:
                new_url = predecessor_url.replace(
                    str(predecessor_id),
                    str(predecessor_target_objects[0]["id"]),
                )
                target_run_after.append(new_url)

        return target_run_after

    async def find_missing_hook_run_after(
        self,
        predecessor_id: int,
        source_run_after: dict,
        target_hook_index: int,
        target_hook_count: int,
        hook_targets: dict[int, list],
    ):
        # The predecessor hook was ignored, it has no targets equivalent
        # Take the predecessor's source and find its predecessor (if none, stop)
        # Find the predecessors' target and put that into run_after for this hook
        # If there is no target, repeat from line one
        try:
            predecessor = await self.client.retrieve_hook(predecessor_id)
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
            hook_targets=hook_targets,
        )
