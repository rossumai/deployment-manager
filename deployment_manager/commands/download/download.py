import os
import subprocess
from anyio import Path

import click
from deployment_manager.commands.download.directory import (
    DownloadOrganizationDirectory,
)


from deployment_manager.common.read_write import read_prd_project_config
from deployment_manager.common.upload_download_setup import (
    check_unique_org_ids,
    expand_destinations,
    mark_subdirectories_to_include,
)
from deployment_manager.utils.consts import display_error, display_warning, settings
from deployment_manager.utils.functions import (
    coro,
)

# TODO: update purge and push commands

# TODO: fix foreign JSONs in the subdir (mongo.json...)

# TODO: handle case of 1 schema being assigned to multiple queues:
# Assign it to the first one, the others should get robust checks during deploy etc.

# TODO: migration of mapping into deploy file and config file
# Cross-org will create 2 directories (named after orgs)
# Same org will have 1 directory merged together
# Do not delete any folders automatically though


@click.command(
    name=settings.DOWNLOAD_COMMAND_NAME,
    help="""
Downloads all Rossum objects from the user's default (first) organization.
Creates a local organization directory structure with the configs of these objects.
In case the directory already exists, it first deletes its contents and then downloads them anew.
               """,
)
@click.argument(
    "destinations",
    nargs=-1,
    type=click.Path(path_type=Path, exists=True),
)
@click.option(
    "--commit",
    "-c",
    default=False,
    is_flag=True,
    help="Commits the pulled changes automatically.",
)
@click.option(
    "--all",
    "-a",
    default=False,
    is_flag=True,
    help="Downloads all remote files and overwrites the local ones in the selected destinations.",
)
@click.option(
    "--message",
    "-m",
    default="Sync changes to local",
    help="Commit message for pulling.",
)
@coro
# To be able to run the command progammatically without the CLI decorators
async def download_project_wrapper(
    destinations: tuple[Path],
    commit: bool = False,
    message: str = "",
    all: bool = False,
):
    await download_destinations(
        destinations=destinations,
        commit_message=message,
        commit=commit,
        download_all=all,
    )


async def download_destinations(
    destinations: tuple[Path],
    project_path: Path = None,
    commit: bool = False,
    commit_message: str = "",
    download_all: bool = False,
):
    if not destinations:
        display_warning(
            f"No destinations specified to {settings.DOWNLOAD_COMMAND_NAME}."
        )
        return

    if not project_path:
        project_path = Path("./")

    project_config = await read_prd_project_config(project_path)
    # TODO: const keys for stuff like 'directories'
    configured_directories = {
        name: DownloadOrganizationDirectory(
            name=name, project_path=project_path, download_all=download_all, **value
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

    for org_dir_name, org_dir_config in configured_directories.items():
        if all(not subdir.include for subdir in org_dir_config.subdirectories.values()):
            continue

        for subdir_name in org_dir_config.subdirectories.keys():
            subdir_path = project_path / org_dir_name / subdir_name
            if not await subdir_path.exists():
                os.mkdir(subdir_path)

        try:
            await org_dir_config.download_organization()
        except Exception as e:
            display_error(
                f"Error during the {settings.DOWNLOAD_COMMAND_NAME} of {org_dir_config.display_label}: {e}",
                e,
            )

    # TODO: test if no subdirs were specified
    # TODO: test with deleting objects
    # TODO: test just empty org file (subdirs should not be required then
    # TODO: org_path assumption test

    if commit:
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", commit_message])
