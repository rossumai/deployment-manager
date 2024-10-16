import asyncio
from anyio import Path
from pydantic import BaseModel
import questionary
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource


from project_rossum_deploy.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
)
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
from project_rossum_deploy.common.client import create_and_validate_client

from project_rossum_deploy.utils.consts import (
    display_error,
    settings,
)
from project_rossum_deploy.utils.functions import extract_id_from_url


class ReleaseFile(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    patch_target_org: bool = True
    token_owner_id: str = ""

    client: ElisAPIClient

    workspaces: list[WorkspaceRelease] = []
    queues: list[QueueRelease] = []
    hooks: list[HookRelease] = []
    schemas: list[SchemaRelease] = []

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


async def deploy_release_file(
    release_file_path: Path,
    org_path: Path = None,
    client: ElisAPIClient = None,
    # force: bool = False,
    # commit: bool = False,
    # commit_message: str = "",
):
    release_file = await release_file_path.read_text()

    yaml = DeployYaml(release_file)

    if not check_required_keys(yaml.data):
        return

    if not org_path:
        org_path = Path("./")
    source_dir_path = org_path / yaml.data[settings.DEPLOY_KEY_SOURCE_DIR]

    # TODO: same-org release solve

    # TODO: parallelize release API requests

    # TODO: token from other places

    # TODO: enable other non-target destinations
    if not client:
        client = await create_and_validate_client(settings.TARGET_DIRNAME)

    release = ReleaseFile(**yaml.data, client=client)

    ### Schemas
    await asyncio.gather(
        *[
            schema_release.initialize(
                yaml=yaml,
                client=client,
                source_dir_path=source_dir_path,
            )
            for schema_release in release.schemas
        ]
    )
    schema_targets = {}
    for schema_release in release.schemas:
        await schema_release.deploy()
        schema_targets[schema_release.id] = [
            target.data for target in schema_release.targets
        ]

    ### Hooks
    await asyncio.gather(
        *[
            hook_release.initialize(
                source_dir_path=source_dir_path,
                yaml=yaml,
                client=client,
                token_owner_id=release.token_owner_id,
            )
            for hook_release in release.hooks
        ]
    )
    hook_targets = {}
    for hook_release in release.hooks:
        await hook_release.deploy()
        hook_targets[hook_release.id] = [target.data for target in hook_release.targets]
    await release.migrate_hook_dependency_graph(hook_targets=hook_targets)

    ### Workspaces
    organization_choices = []
    async for org in client.list_all_organizations():
        organization_choices.append(questionary.Choice(title=org.name, value=org.url))
    if len(organization_choices) > 1:
        target_org_url = await questionary.select(
            "Select target organization:", choices=organization_choices
        ).ask_async()
    else:
        target_org_url = organization_choices[0].value

    await asyncio.gather(
        *[
            workspace_release.initialize(
                yaml=yaml,
                client=client,
                target_org_url=target_org_url,
                source_dir_path=source_dir_path,
            )
            for workspace_release in release.workspaces
        ]
    )
    workspace_targets = {}
    for workspace_release in release.workspaces:
        await workspace_release.deploy()
        workspace_targets[workspace_release.id] = [
            target.data for target in workspace_release.targets
        ]

    ### Queues
    await asyncio.gather(
        *[
            queue_release.initialize(
                yaml=yaml,
                client=client,
                source_dir_path=source_dir_path,
                workspace_targets=workspace_targets,
                hook_targets=hook_targets,
                schema_targets=schema_targets,
            )
            for queue_release in release.queues
        ]
    )
    queue_targets = {}
    for queue_release in release.queues:
        await queue_release.deploy()
        queue_targets[queue_release.id] = [
            target.data for target in queue_release.targets
        ]

    yaml.save_to_file(str(release_file_path))

    lookup_table = {
        **schema_targets,
        **hook_targets,
        **workspace_targets,
        **queue_targets,
    }

    for release_object in [
        *release.schemas,
        *release.hooks,
        *release.workspaces,
        *release.queues,
    ]:
        release_object.implicit_override(lookup_table)

    return

    # TODO: check if remote was not modified when updating?

    # TODO: Show plan first, then ask for confirmation
    # Plan should include org names
    # Plan should check the files exist locally...
    # check if queue has its WS being deployed or it is a queue with an existing target_id

    # TODO: better representation of the deploy process

    # TODO: migrate org
    # TODO: inboxes

    # TODO: ??? How to solve name changes? (path and name will be different and won't locate the object)
    # During planning, show error that it cannot be found
    # Eventually, create utility to update a release file (template --update or whatever)

    # TODO: log all messages to stdout and into a separate file as well

    # TODO: make purge work with deploy files as well
