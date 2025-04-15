from anyio import Path

import questionary
from rich.panel import Panel

from rich import print as pprint
import click
from rossum_api import ElisAPIClient

from deployment_manager.commands.deploy.common.helpers import (
    get_directory_from_config,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    get_url_and_credentials,
)

from deployment_manager.commands.purge.directory import (
    ALL_OBJECT_TYPES,
    PurgeOrganizationDirectory,
)
from deployment_manager.common.read_write import read_prd_project_config
from deployment_manager.utils.consts import (
    display_error,
    display_warning,
    settings,
)
from deployment_manager.utils.functions import (
    coro,
)


PURGE_OBJECT_TYPES = [
    *ALL_OBJECT_TYPES,
    settings.ALL_OBJECTS,
    settings.UNUSED_SCHEMAS,
]


@click.command(
    name=settings.PURGE_COMMAND_NAME,
    help="""
Deletes all objects in Rossum based on IDs in the mappping file. This operation is destructive and cannot be undone.""",
)
@click.argument(
    "object_types",
    nargs=-1,
    type=click.Choice(
        choices=PURGE_OBJECT_TYPES,
    ),
)
@coro
async def purge_object_types_wrapper(object_types):
    # To be able to run the command progammatically without the CLI decorators
    await purge_object_types(
        object_types=object_types,
    )


async def purge_object_types(
    object_types: list[str], client: ElisAPIClient = None, project_path: Path = None
):
    try:
        if not object_types:
            display_warning(
                f"No object types specified to {settings.PURGE_COMMAND_NAME}."
            )
            return

        if not project_path:
            project_path = Path("./")

        config = await read_prd_project_config(project_path)

        if not config:
            return ""

        selected_dir = await get_dir_from_user(project_path=project_path, config=config)
        credentials = await get_url_and_credentials(
            project_path=project_path,
            org_name=selected_dir,
        )
        if not credentials:
            return

        client = ElisAPIClient(base_url=credentials.url, token=credentials.token)

        directory_in_config = await get_directory_from_config(
            base_path=project_path, org_name=selected_dir
        )
        selected_subdirs = await get_subdirs_from_user(
            selected_dir=selected_dir, config=config
        )

        if selected_dir:
            org_name = selected_dir
            org_id = directory_in_config.get(settings.CONFIG_KEY_ORG_ID, None)
        # N/A selected -> need to find target org via API
        else:
            target_org_choices = []
            async for org in client.list_all_organizations():
                target_org_choices.append(questionary.Choice(title=org.name, value=org))
            if len(target_org_choices) > 1:
                target_org = await questionary.select(
                    "Select organization:", choices=target_org_choices
                ).ask_async()
            else:
                target_org = target_org_choices[0].value
            org_name = target_org.name
            org_id = target_org.id

        purge_dir = PurgeOrganizationDirectory(
            client=client,
            project_path=project_path,
            name=org_name,
            org_id=org_id,
            purged_object_types=object_types,
            selected_subdirs=selected_subdirs,
            subdirectories=directory_in_config.get(
                settings.CONFIG_KEY_SUBDIRECTORIES, {}
            ),
        )

        await purge_dir.purge_organization()

        pprint(Panel(f"{settings.PURGE_COMMAND_NAME} finished."))

    except Exception as e:
        display_error(f"Error during project {settings.UPLOAD_COMMAND_NAME}: {e}", e)


async def get_dir_from_user(project_path: Path, config: dict):
    dir_candidates = [
        dir_path
        for dir_path in config.get(settings.CONFIG_KEY_DIRECTORIES, {}).keys()
        if await (Path(project_path) / dir_path).exists()
    ]

    dir_choices = [
        questionary.Choice(title=str(Path(project_path / path)))
        for path in dir_candidates
    ]
    dir_choices.append(questionary.Choice(title="N/A", value=""))

    selected_dir = await questionary.select(
        "Select directory to purge:", choices=dir_choices
    ).ask_async()

    return selected_dir


async def get_subdirs_from_user(selected_dir: str, config: dict):
    subdir_candidates = [
        subdir_path
        for subdir_path in config.get(settings.CONFIG_KEY_DIRECTORIES, {})
        .get(selected_dir, {})
        .get(settings.CONFIG_KEY_SUBDIRECTORIES, {})
        .keys()
        if await (Path(selected_dir) / subdir_path).exists()
    ]
    subdir_choices = [questionary.Choice(title=str(path)) for path in subdir_candidates]
    if not subdir_choices:
        return []

    selected_subdirs = await questionary.checkbox(
        f"Select subdir(s) to {settings.PURGE_COMMAND_NAME}: (select all to {settings.PURGE_COMMAND_NAME} everything)",
        choices=subdir_choices,
    ).ask_async()

    return selected_subdirs
