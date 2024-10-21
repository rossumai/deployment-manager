import asyncio
import dataclasses
from anyio import Path
from rich import print as pprint
from rich.panel import Panel
import questionary
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.commands.deploy.subcommands.run.hook_release import (
    HookRelease,
)
from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    ObjectRelease,
)
from project_rossum_deploy.commands.deploy.subcommands.run.organization_release import (
    OrganizationRelease,
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
from rossum_api.models.organization import Organization


# TODO: rename
class ReleaseFile(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    patch_target_org: bool = True
    token_owner_id: str | None = ""
    deployed_org_id: int | None = ""
    last_deployed_at: str | None = ""

    client: ElisAPIClient
    source_dir_path: Path
    yaml: DeployYaml

    source_org: Organization
    target_org: Organization

    workspaces: list[WorkspaceRelease] = []
    queues: list[QueueRelease] = []
    hooks: list[HookRelease] = []
    schemas: list[SchemaRelease] = []

    # TODO: redo if too computationally-heavy
    @property
    def schema_targets(self):
        return self.gather_targets(self.schemas)

    @property
    def hook_targets(self):
        return self.gather_targets(self.hooks)

    @property
    def workspace_targets(self):
        return self.gather_targets(self.workspaces)

    @property
    def queue_targets(self):
        return self.gather_targets(self.queues)

    async def apply_implicit_id_override(self, plan_only: bool = False):
        lookup_table = {
            **self.schema_targets,
            **self.hook_targets,
            **self.workspace_targets,
            **self.queue_targets,
        }

        for release_object in [
            *self.schemas,
            *self.hooks,
            *self.workspaces,
            *self.queues,
        ]:
            await release_object.implicit_override_targets(lookup_table)

    def gather_targets(self, release_objects: list[ObjectRelease]):
        targets = {}
        for object in release_objects:
            targets[object.id] = [
                target.data for target in object.targets if target.data
            ]
        return targets

    async def deploy_organization(self, plan_only: bool = False):
        organization_release = OrganizationRelease(
            id=self.source_org.id,
            name=self.source_org.name,
            data=dataclasses.asdict(self.source_org),
            target_org=self.target_org,
            plan_only=plan_only,
            client=self.client,
        )

        if plan_only:
            pprint(
                Panel(
                    f"{organization_release.create_source_to_target_string(dataclasses.asdict(self.target_org))}"
                )
            )

        await organization_release.deploy()

    async def deploy_schemas(self, plan_only: bool = False):
        await asyncio.gather(
            *[
                schema_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    source_dir_path=self.source_dir_path,
                    plan_only=plan_only,
                )
                for schema_release in self.schemas
            ]
        )

        await asyncio.gather(
            *[schema_release.deploy() for schema_release in self.schemas]
        )

    async def deploy_hooks(self, plan_only: bool = False):
        await asyncio.gather(
            *[
                hook_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    source_dir_path=self.source_dir_path,
                    token_owner_id=self.token_owner_id,
                    plan_only=plan_only,
                )
                for hook_release in self.hooks
            ]
        )

        await asyncio.gather(*[hook_release.deploy() for hook_release in self.hooks])

    async def deploy_workspaces(self, plan_only: bool = False):
        await asyncio.gather(
            *[
                workspaces_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    source_dir_path=self.source_dir_path,
                    target_org_url=self.target_org.url,
                    plan_only=plan_only,
                )
                for workspaces_release in self.workspaces
            ]
        )

        await asyncio.gather(
            *[workspace_release.deploy() for workspace_release in self.workspaces]
        )

    async def deploy_queues(self, plan_only: bool = False):
        await asyncio.gather(
            *[
                queue_release.initialize(
                    yaml=self.yaml,
                    client=self.client,
                    source_dir_path=self.source_dir_path,
                    plan_only=plan_only,
                    schema_targets=self.schema_targets,
                    hook_targets=self.hook_targets,
                    workspace_targets=self.workspace_targets,
                )
                for queue_release in self.queues
            ]
        )

        await asyncio.gather(*[queue_release.deploy() for queue_release in self.queues])

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

    async def migrate_hook_dependency_graph(self, plan_only: bool = False):
        for hook_release in self.hooks:
            try:
                for target_hook_index, target_hook in enumerate(hook_release.targets):
                    target_run_after = await self.migrate_target_hook_run_after(
                        target_hook_index=target_hook_index,
                        target_hook_count=len(hook_release.targets),
                        source_run_after=hook_release.data.get("run_after", []),
                        hook_targets=self.hook_targets,
                    )
                    if plan_only:
                        # TODO: visualize deps graphically
                        ...
                    else:
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
