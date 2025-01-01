import asyncio
import dataclasses
from anyio import Path
from rich import print as pprint
from rich.panel import Panel
import questionary
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.run.hook_release import (
    HookRelease,
)
from deployment_manager.commands.deploy.subcommands.run.object_release import (
    DeployException,
    ObjectRelease,
    Target,
)
from deployment_manager.commands.deploy.subcommands.run.organization_release import (
    OrganizationRelease,
)
from deployment_manager.commands.deploy.subcommands.run.queue_release import (
    QueueRelease,
)
from deployment_manager.commands.deploy.subcommands.run.workspace_release import (
    WorkspaceRelease,
)
from deployment_manager.commands.migrate.helpers import get_token_owner
from deployment_manager.utils.consts import display_error, display_warning, settings
from deployment_manager.utils.functions import extract_id_from_url


from pydantic import BaseModel
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource
from rossum_api.models.organization import Organization
from rossum_api.models.user import User
from rossum_api.models.group import Group


# TODO: rename
class ReleaseFile(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    plan_only: bool = False

    force_deploy: bool = False
    auto_delete: bool = False

    patch_target_org: bool = True
    token_owner_id: int | None = None
    deployed_org_id: int | None = ""
    last_deployed_at: str | None = ""

    client: ElisAPIClient
    source_client: ElisAPIClient
    source_dir_path: Path
    yaml: DeployYaml

    source_org: Organization
    target_org: Organization

    workspaces: list[WorkspaceRelease] = []
    queues: list[QueueRelease] = []
    hooks: list[HookRelease] = []

    hook_templates: dict = {}
    queue_ignore_warnings: dict = {}

    ignore_timestamp_mismatches: dict = {}

    hook_targets: list[Target] = []
    workspace_targets: list[Target] = []
    queue_targets: list[Target] = []

    @property
    def is_same_org(self):
        return self.source_org.id == self.target_org.id

    async def apply_implicit_id_override(self):
        if not self.plan_only:
            pprint(Panel("Applying implicit ID override"))

        lookup_table = {
            **self.hook_targets,
            **self.workspace_targets,
            **self.queue_targets,
        }

        release_objects: list[ObjectRelease] = [
            *self.hooks,
            *self.workspaces,
            *self.queues,
        ]
        for release_object in release_objects:
            await release_object.implicit_override_targets(lookup_table)

    def gather_targets(self, release_objects: list[ObjectRelease]):
        targets = {}
        for object in release_objects:
            targets[object.id] = [
                target.data for target in object.targets if target.data
            ]
        return targets

    async def deploy_organization(self):
        organization_release = OrganizationRelease(
            id=self.source_org.id,
            name=self.source_org.name,
            data=dataclasses.asdict(self.source_org),
            target_org=self.target_org,
            plan_only=self.plan_only,
            client=self.client,
            source_client=self.source_client,
            last_deploy_timestamp=self.last_deployed_at,
            ignore_timestamp_mismatch=self.force_deploy
            or self.ignore_timestamp_mismatches.get(self.source_org.id, False),
        )

        if self.plan_only:
            pprint(
                Panel(
                    f"{organization_release.create_source_to_target_string(dataclasses.asdict(self.target_org))}"
                )
            )

        if self.patch_target_org and not self.is_same_org:
            await organization_release.deploy()
            self.ignore_timestamp_mismatches[organization_release.id] = (
                organization_release.ignore_timestamp_mismatch
            )
            self.detect_deploy_phase_exceptions([organization_release])

    async def deploy_hooks(self):
        await self.ensure_token_owner()

        await asyncio.gather(
            *[
                hook_release.initialize(
                    auto_delete=self.auto_delete,
                    yaml=self.yaml,
                    client=self.client,
                    source_client=self.source_client,
                    source_dir_path=self.source_dir_path,
                    token_owner_id=self.token_owner_id,
                    plan_only=self.plan_only,
                    is_same_org_deploy=self.is_same_org,
                    hook_template_url=self.hook_templates.get(hook_release.id, None),
                    last_deploy_timestamp=self.last_deployed_at,
                    ignore_timestamp_mismatch=self.force_deploy
                    or self.ignore_timestamp_mismatches.get(hook_release.id, False),
                )
                for hook_release in self.hooks
            ]
        )
        self.detect_initialize_phase_exceptions(self.hooks)

        # Run sequentially when planning because user may have to input things in the CLI
        if self.plan_only:
            for hook_release in self.hooks:
                await hook_release.deploy()
                self.ignore_timestamp_mismatches[hook_release.id] = (
                    hook_release.ignore_timestamp_mismatch
                )
                self.hook_templates[hook_release.id] = hook_release.hook_template_url
        else:
            await asyncio.gather(
                *[hook_release.deploy() for hook_release in self.hooks]
            )
        self.detect_deploy_phase_exceptions(self.hooks)
        self.hook_targets = self.gather_targets(self.hooks)

    async def deploy_workspaces(self):
        await asyncio.gather(
            *[
                workspace_release.initialize(
                    auto_delete=self.auto_delete,
                    yaml=self.yaml,
                    client=self.client,
                    source_client=self.source_client,
                    source_dir_path=self.source_dir_path,
                    target_org_url=self.target_org.url,
                    plan_only=self.plan_only,
                    is_same_org_deploy=self.is_same_org,
                    last_deploy_timestamp=self.last_deployed_at,
                    ignore_timestamp_mismatch=self.force_deploy
                    or self.ignore_timestamp_mismatches.get(
                        workspace_release.id, False
                    ),
                )
                for workspace_release in self.workspaces
            ]
        )
        self.detect_initialize_phase_exceptions(self.workspaces)

        # Run sequentially when planning because user may have to input things in the CLI
        if self.plan_only:
            for workspace_release in self.workspaces:
                await workspace_release.deploy()
                self.ignore_timestamp_mismatches[workspace_release.id] = (
                    workspace_release.ignore_timestamp_mismatch
                )

        else:
            await asyncio.gather(
                *[workspace_release.deploy() for workspace_release in self.workspaces]
            )
        self.detect_deploy_phase_exceptions(self.workspaces)
        self.workspace_targets = self.gather_targets(self.workspaces)

    async def deploy_queues(self):
        await asyncio.gather(
            *[
                queue_release.initialize(
                    auto_delete=self.auto_delete,
                    yaml=self.yaml,
                    client=self.client,
                    source_client=self.source_client,
                    source_dir_path=self.source_dir_path,
                    plan_only=self.plan_only,
                    is_same_org_deploy=self.is_same_org,
                    hook_targets=self.hook_targets,
                    workspace_targets=self.workspace_targets,
                    last_deploy_timestamp=self.last_deployed_at,
                    ignore_timestamp_mismatch=self.force_deploy
                    or self.ignore_timestamp_mismatches.get(queue_release.id, False),
                    schema_ignore_timestamp_mismatch=self.force_deploy
                    or self.ignore_timestamp_mismatches.get(
                        queue_release.schema_release.id, False
                    ),
                    inbox_ignore_timestamp_mismatch=self.force_deploy
                    or self.ignore_timestamp_mismatches.get(
                        queue_release.inbox_release.id, False
                    ),
                )
                for queue_release in self.queues
            ]
        )
        self.detect_initialize_phase_exceptions(self.queues)

        # Run sequentially when planning because user may have to input things in the CLI
        if self.plan_only:
            for queue_release in self.queues:
                await queue_release.deploy()
                self.queue_ignore_warnings[queue_release.id] = (
                    queue_release.ignore_deploy_warnings
                )
                self.ignore_timestamp_mismatches[queue_release.id] = (
                    queue_release.ignore_timestamp_mismatch
                )
                self.ignore_timestamp_mismatches[queue_release.schema_release.id] = (
                    queue_release.schema_release.ignore_timestamp_mismatch
                )
                self.ignore_timestamp_mismatches[queue_release.inbox_release.id] = (
                    queue_release.inbox_release.ignore_timestamp_mismatch
                )
        else:
            await asyncio.gather(
                *[queue_release.deploy() for queue_release in self.queues]
            )
        self.detect_deploy_phase_exceptions(self.queues)
        self.queue_targets = self.gather_targets(self.queues)

    async def ensure_token_owner(self):
        if self.source_org.id == self.target_org.id:
            return

        if self.token_owner_id:
            try:
                await self.client.retrieve_user(self.token_owner_id)
            except APIClientError:
                display_warning("Invalid token owner in config.")
                self.token_owner_id = None

        if not self.token_owner_id:
            target_token_owner_from_remote = await get_token_owner(self.client)
            if target_token_owner_from_remote:
                self.token_owner_id = target_token_owner_from_remote.id
            else:
                users = [user async for user in self.client.list_all_users()]
                user_roles = [role async for role in self.client.list_all_user_roles()]
                user_choices = [
                    questionary.Choice(title=user.username, value=user.id)
                    for user in users
                    if self.is_user_admin(user=user, user_roles=user_roles)
                ]
                self.token_owner_id = await questionary.select(
                    "Please choose target hook token owner:", choices=user_choices
                ).ask_async()

    @classmethod
    def is_user_admin(cls, user: User, user_roles: list[Group]):
        admin_urls = [
            role.url
            for role in user_roles
            if role.name in ["admin", "organization_group_admin"]
        ]
        for user_role_url in user.groups:
            if user_role_url in admin_urls:
                return True
        return False

    def detect_initialize_phase_exceptions(self, releases: list[ObjectRelease]):
        for release in releases:
            if release.initialize_failed:
                raise DeployException(
                    f"Initialize of {release.display_type} {release.display_label} failed, see error details above."
                )

    def detect_deploy_phase_exceptions(self, releases: list[ObjectRelease]):
        for release in releases:
            if release.deploy_failed:
                raise DeployException(
                    f"Deploy of {release.display_type} {release.display_label} failed, see error details above."
                )

    # TODO: branch out into separate file
    async def migrate_hook_dependency_graph(self):
        if not len(self.hooks):
            return

        pprint(
            Panel(
                f"{settings.PLAN_PRINT_STR if self.plan_only else ""} Updating hook dependency graph..."
            )
        )
        for hook_release in self.hooks:
            try:
                for target_hook_index, target_hook in enumerate(hook_release.targets):
                    target_run_after = await self.migrate_target_hook_run_after(
                        target_hook_index=target_hook_index,
                        target_hook_count=len(hook_release.targets),
                        source_run_after=hook_release.data.get("run_after", []),
                        hook_targets=self.hook_targets,
                    )
                    if self.plan_only:
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
        pprint(
            Panel(
                f"{settings.PLAN_PRINT_STR  if self.plan_only else ""} Hook dependency graph updated..."
            )
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
