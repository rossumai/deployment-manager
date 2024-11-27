import subprocess
from anyio import Path

import click
from rich import print as pprint
from rich.panel import Panel

# from project_rossum_deploy.commands.download.download import download_project
from project_rossum_deploy.commands.download.download import download_destinations
from project_rossum_deploy.commands.upload.directory import UploadOrganizationDirectory
from project_rossum_deploy.common.read_write import read_prd_project_config
from project_rossum_deploy.common.upload_download_setup import (
    check_unique_org_ids,
    expand_destinations,
    mark_subdirectories_to_include,
)
from project_rossum_deploy.utils.consts import (
    display_error,
    display_warning,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
)


@click.command(
    name=settings.UPLOAD_COMMAND_NAME,
    help="""
Updates local files that were changed into Rossum.
Only source files are taken into account by default.
               """,
)
@click.argument(
    "destinations",
    nargs=-1,
    type=click.Path(path_type=Path, exists=True),
)
@click.option(
    "--all",
    "-a",
    default=False,
    is_flag=True,
    help="Uploads all local files in the selected destination (source/target) and not just files that were locally modified.",
)
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Ignores newer remote timestamps = overwrites remote with local version of objects.",
)
@click.option(
    "--indexed-only",
    "-io",
    default=False,
    is_flag=True,
    help="Pushes only files added to git index (using `git add <path>`).",
)
@click.option(
    "--commit",
    "-c",
    default=False,
    is_flag=True,
    help="Commits the pushed changes automatically.",
)
@click.option(
    "--message",
    "-m",
    default="Pushed changes to remote",
    help="Commit message for pulling.",
)
@coro
async def upload_project_wrapper(
    destinations, all, force, indexed_only, commit, message
):
    # To be able to run the command progammatically without the CLI decorators
    await upload_destinations(
        destinations=destinations,
        upload_all=all,
        force=force,
        indexed_only=indexed_only,
        commit=commit,
        commit_message=message,
    )


async def upload_destinations(
    destinations: tuple[Path],
    project_path: Path = None,
    upload_all: bool = False,
    force: bool = False,
    indexed_only: bool = False,
    commit: bool = False,
    commit_message: str = "",
):
    if not destinations:
        display_warning("No destinations specified to pull.")
        return

    if not project_path:
        project_path = Path("./")

    project_config = await read_prd_project_config(project_path)

    configured_directories = {
        name: UploadOrganizationDirectory(
            name=name,
            project_path=project_path,
            upload_all=upload_all,
            force=force,
            indexed_only=indexed_only,
            **value,
        )
        for name, value in project_config.get("directories", {}).items()
    }

    if not check_unique_org_ids(configured_directories=configured_directories):
        return

    expanded_destinations = expand_destinations(
        destinations=destinations,
        project_path=project_path,
        configured_directories=configured_directories,
    )

    mark_subdirectories_to_include(
        configured_directories=configured_directories,
        expanded_destinations=expanded_destinations,
    )

    errors_encountered = False
    for dir_config in configured_directories.values():
        if all(not subdir.include for subdir in dir_config.subdirectories.values()):
            continue

        try:
            await dir_config.upload_organization()
            if dir_config.request_errors:
                errors_encountered = True
                display_error(
                    f'Error(s) while uploading {dir_config.display_label}:\n{'\n'.join(dir_config.request_errors)}'
                )
        except Exception as e:
            display_error(
                f"Error during the {settings.UPLOAD_COMMAND_NAME} of {dir_config.display_label}: {e}",
                e,
            )

    if not errors_encountered:
        await download_destinations(destinations=destinations)

    if commit:
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", commit_message])

    pprint(
        Panel(
            f"Finished {settings.UPLOAD_COMMAND_NAME}.{ ' Please commit the changes before running this command again.' if not commit else ''}"
        )
    )
