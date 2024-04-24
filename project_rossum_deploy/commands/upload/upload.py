from anyio import Path
import subprocess
from rich import print
from rich.panel import Panel
from rich.progress import track

import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.download.download import (
    download_project,
)

from project_rossum_deploy.commands.upload.operations import (
    create_object,
    update_object,
)
from project_rossum_deploy.utils.consts import (
    GIT_CHARACTERS,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
    display_error,
    find_all_object_paths,
    merge_formula_changes,
    merge_hook_changes,
    evaluate_create_dependencies,
)


@click.command(
    name=settings.UPLOAD_COMMAND_NAME,
    help="""
Updates local files that were changed into Rossum.
Only source files are taken into account by default.
               """,
)
@click.argument(
    "destination",
    default=settings.SOURCE_DIRNAME,
    type=click.Choice([settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]),
)
@click.option(
    "--all",
    default=False,
    is_flag=True,
    help="Uploads all local files in the selected destination (source/target) and not just files that were locally modified.",
)
@coro
async def upload_project_wrapper(destination, all):
    # To be able to run the command progammatically without the CLI decorators
    await upload_project(destination=destination, upload_all=all)


async def upload_project(
    destination: str, client: ElisAPIClient = None, upload_all=False
):
    try:
        org_path = Path("./")

        if not client:
            match destination:
                case settings.SOURCE_DIRNAME:
                    client = ElisAPIClient(
                        base_url=settings.SOURCE_API_URL,
                        token=settings.SOURCE_TOKEN,
                        username=settings.SOURCE_USERNAME,
                        password=settings.SOURCE_PASSWORD,
                    )
                case settings.TARGET_DIRNAME:
                    client = ElisAPIClient(
                        base_url=settings.TARGET_API_URL,
                        token=settings.TARGET_TOKEN,
                        username=settings.TARGET_USERNAME,
                        password=settings.TARGET_PASSWORD,
                    )
                case _:
                    raise click.ClickException(
                        f'Unrecognized destination "{destination}" to use {settings.UPLOAD_COMMAND_NAME}.'
                    )

        # The -s flag is there to show a simplified list of changes
        # The -u flag is there to show each individual file (and not a subdir)
        # The change in git config is because of potential 'unusual' (non-ASCII) characters in paths
        subprocess.run(["git", "config", "core.quotePath", "false"])
        git_destination_diff = subprocess.run(
            ["git", "status", destination, "-s", "-u"],
            capture_output=True,
            text=True,
        )
        subprocess.run(["git", "config", "core.quotePath", "true"])
        # print(git_destination_diff.stdout.split('\n'))
        changes_raw = git_destination_diff.stdout.split("\n")
        changes = []
        for change in changes_raw:
            change = change.strip()
            if not change:
                continue
            op, path = tuple(change.split(" ", maxsplit=1))
            path = Path(path.strip().strip('"'))
            path
            changes.append((op, path))

        if changes:
            changes = await merge_hook_changes(changes, org_path)
            # changes = await evaluate_delete_dependencies(changes, org_path)
            changes = await merge_formula_changes(changes)
            changes = await evaluate_create_dependencies(changes, org_path, client)

        if upload_all:
            await include_unmodified_files(Path(org_path) / destination, changes)

        for change in track(changes, description="Pushing changes to Rossum..."):
            op, path = change
            match op:
                case GIT_CHARACTERS.CREATED:
                    await create_object(org_path / path, client)
                case GIT_CHARACTERS.CREATED_STAGED:
                    await create_object(org_path / path, client)
                # case GIT_CHARACTERS.DELETED:
                #    await delete_object(org_path / path, client)
                case GIT_CHARACTERS.UPDATED:
                    result = await update_object(client=client, path=org_path / path)
                    if not result and upload_all:
                        print(f'Recreating object with path "{path}".')
                        await create_object(org_path / path, client)
                case _:
                    raise click.ClickException(f'Unrecognized operator "{op}".')

        print(
            Panel(
                f"Finished {settings.UPLOAD_COMMAND_NAME}. Please commit the changes before running this command again."
            )
        )
        print(
            Panel(
                f"Running {settings.DOWNLOAD_COMMAND_NAME} for {destination} because of potential changes to names and mapping."
            )
        )
        # Repulling is done to update mapping and (potentially) different filenames.
        await download_project(client=client, org_path=org_path)

    except Exception as e:
        display_error(f"Error during project {settings.UPLOAD_COMMAND_NAME}: {e}", e)


async def include_unmodified_files(
    destination_path: Path, changes: list[tuple[str, Path]]
):
    all_files = await find_all_object_paths(destination_path)

    changes_paths = set(map(lambda x: x[1], changes))
    for file_path in all_files:
        if file_path not in changes_paths:
            changes.append((GIT_CHARACTERS.UPDATED.value, file_path))
