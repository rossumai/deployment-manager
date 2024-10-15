import asyncio
from anyio import Path
import click
from pydantic import BaseModel
import questionary
from rossum_api import ElisAPIClient


from project_rossum_deploy.commands.deploy.helpers import DeployYaml
from project_rossum_deploy.commands.deploy.hook_release import HookRelease
from project_rossum_deploy.commands.deploy.queue_release import QueueRelease
from project_rossum_deploy.commands.deploy.schema_release import SchemaRelease
from project_rossum_deploy.commands.deploy.workspace_release import WorkspaceRelease
from project_rossum_deploy.commands.migrate.helpers import get_token_owner
from project_rossum_deploy.common.client import create_and_validate_client

from project_rossum_deploy.utils.consts import (
    display_error,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
)


@click.command(
    name=settings.DEPLOY_COMMAND_NAME,
    help="""
Applies selected changes onto other objects based on the provided release.yaml file.
If these objects don't exist, they get created.
               """,
)
@click.argument("release_file", type=click.Path(path_type=Path))
# @click.option(
#     "--force",
#     "-f",
#     default=False,
#     is_flag=True,
#     help="Ignores newer remote timestamps = overwrites remote with local version of objects.",
# )
# @click.option(
#     "--commit",
#     "-c",
#     default=False,
#     is_flag=True,
#     help="Commits the pushed changes automatically.",
# )
# @click.option(
#     "--message",
#     "-m",
#     default="Released changes to target organization",
#     help="Commit message for pulling.",
# )
@coro
async def deploy_project_wrapper(
    release_file: Path,
    # force: bool,
    # commit: bool,
    # message: str,
):
    await deploy_release_file(
        release_file_path=release_file,
        # force=force,
        # commit=commit,
        # commit_message=message,
    )


class ReleaseFile(BaseModel):
    variables: dict = {}
    workspaces: list[WorkspaceRelease] = []
    queues: list[QueueRelease] = []
    hooks: list[HookRelease] = []
    schemas: list[SchemaRelease] = []


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

    release = ReleaseFile(**yaml.data)

    if not org_path:
        org_path = Path("./")
    source_dir_path = org_path / yaml.data[settings.DEPLOY_SOURCE_DIR_KEY]

    # TODO: same-org release solve

    # TODO: parallelize release API requests

    # TODO: token from other places
    if not client:
        client = await create_and_validate_client(settings.TARGET_DIRNAME)

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

    target_token_owner_id = None
    if not settings.IS_PROJECT_IN_SAME_ORG:
        target_org_token_owner = await get_token_owner(client)
        if not target_org_token_owner:
            target_token_owner_id = await questionary.text(
                "Please input user ID of the hook token owner (e.g., 938382):"
            ).ask_async()
        else:
            target_token_owner_id = target_org_token_owner.id

    ### Hooks
    await asyncio.gather(
        *[
            hook_release.initialize(
                source_dir_path=source_dir_path,
                yaml=yaml,
                client=client,
                token_owner_id=target_token_owner_id,
            )
            for hook_release in release.hooks
        ]
    )
    hook_targets = {}
    for hook_release in release.hooks:
        await hook_release.deploy()
        hook_targets[hook_release.id] = [target.data for target in hook_release.targets]

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

    # TODO: ??? How to solve name changes? (path and name will be different and won't locate the object)
    # During planning, show error that it cannot be found
    # Eventually, create utility to update a release file (template --update or whatever)

    # TODO: log all messages to stdout and into a separate file as well


def check_required_keys(release: dict):
    required_keys = [settings.DEPLOY_SOURCE_DIR_KEY, settings.DEPLOY_TARGET_URL_KEY]
    missing_keys = []

    for req_key in required_keys:
        if req_key not in release:
            missing_keys.append(req_key)

    if missing_keys:
        display_error(f"Release is missing the following required keys: {missing_keys}")
        return False
    else:
        return True
