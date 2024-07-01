from anyio import Path

from rich import print
from rich.panel import Panel
from rich.prompt import Confirm
import click
from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.migrate_mapping import migrate_mapping
from project_rossum_deploy.commands.purge.delete_objects import (
    delete_all_objects_with_ids,
)
from project_rossum_deploy.common.client import create_and_validate_client
from project_rossum_deploy.common.mapping import extract_sources_targets, read_mapping
from project_rossum_deploy.utils.consts import (
    display_error,
    display_warning,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
)


@click.command(
    name=settings.PURGE_COMMAND_NAME,
    help="""
Deletes all objects in Rossum based on IDs in the mappping file. This operation is destructive and cannot be undone.""",
)
@click.argument(
    "destination",
    type=click.Choice([settings.TARGET_DIRNAME]),
)
@coro
async def purge_project_wrapper(destination):
    # To be able to run the command progammatically without the CLI decorators
    await purge_project(
        destination=destination,
    )


async def purge_project(
    destination: str,
    client: ElisAPIClient = None,
):
    try:
        display_warning(
            "This operation cannot be undone, the objects will be deleted from the database."
        )
        if not Confirm.ask("Are you sure you want to continue?"):
            return

        org_path = Path("./")

        # Make the previous mapping conform in structure
        await migrate_mapping("mapping.yaml", print_result=False)
        mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
        if not mapping:
            print(Panel("No mappping file found."))
            return

        if not client:
            client = await create_and_validate_client(destination)

        sources, targets = extract_sources_targets(mapping)

        if destination == settings.SOURCE_DIRNAME:
            await delete_all_objects_with_ids(sources, client)
        else:
            await delete_all_objects_with_ids(targets, client)

        print(
            Panel(
                f"{settings.PURGE_COMMAND_NAME} finished. Please run {settings.DOWNLOAD_COMMAND_NAME} before making further changes since local and remote are now out of sync."
            )
        )

    except Exception as e:
        display_error(f"Error during project {settings.UPLOAD_COMMAND_NAME}: {e}", e)
