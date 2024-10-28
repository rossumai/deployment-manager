import os
import subprocess
from anyio import Path

import click
from project_rossum_deploy.commands.download.directory import OrganizationDirectory


from project_rossum_deploy.common.read_write import read_yaml
from project_rossum_deploy.utils.consts import display_warning, settings
from project_rossum_deploy.utils.functions import (
    coro,
)

# TODO: update purge and push commands

# TODO: pull for any number of dirs with any name
# With different orgs, this is already working, only mapping.yaml should be simplified (no need for RHS)
# For same-org source and targets created via release, you could keep them in a single dir too
# For deploying, you have a deploy file with the pairs specified, for pushing you would push only what changed, the same for pulling
# TODO: one config file including object IDs (instead of mapping)
# TODO: one credentials file (optional)

# TODO: root project config file specifying folders
# Each folder has a URL specified + the org ID
# In the folder, there are credentials (this differentiates different orgs)
# ??? In case of the same org, it will be enough to have credentials in the default folder
# Each folder can have multiple regexes, one folder is default
# Based on this, objects are sorted into this or that folder
# ?? How to recognize if the org has all objects or just some (based on the regex naively?)
# TODO: check org ID unique for each main directory
# TODO: optional subdirectories (sandbox/uat, sandbox/dev)

# TODO: migration of mapping into deploy file and config file
# Cross-org will create 2 directories (named after orgs)
# Same org will have 1 directory merged together
# Do not delete any folders automatically though

# TODO: handling of just root dir destination specification (sandbox/ -> sandbox/uat and sandbox/dev)

# TODO: init command will create basic directory structure based on a few questions

# TODO: allow a non-existent path: create it and let user input credentials


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
    org_path: Path = None,
    commit: bool = False,
    commit_message: str = "",
    download_all: bool = False,
):
    if not org_path:
        org_path = Path("./")

    project_config = read_yaml(org_path / settings.CONFIG_FILENAME)
    # TODO: const keys for stuff like 'directories'
    configured_directories = {
        name: OrganizationDirectory(
            name=name, org_path=org_path, download_all=download_all, **value
        )
        for name, value in project_config.get("directories", {}).items()
    }

    # TODO: extract into function
    unique_org_ids = set(
        dir_config.org_id for dir_config in configured_directories.values()
    )
    if len(unique_org_ids) != len(configured_directories.values()):
        display_warning(
            "Configured directories do not have unique org IDs. If you want to have multiple directories for the same organization, use subdirectories."
        )
        return

    # TODO: extract into function
    expanded_destinations = []
    for destination in destinations:
        dir_name = (
            str(destination.name)
            if destination.parent == org_path
            else str(destination.parent)
        )
        if dir_name not in configured_directories:
            display_warning(
                f'Destination "{destination}" not configured in {settings.CONFIG_FILENAME}. Skipping.'
            )
            continue

        # Only the "org-level" destination was specified
        # Go through configured subdirectories and add them as destinations
        if destination.parent == org_path:
            dir_config = configured_directories.get(destination.name, {})
            expanded_destinations.extend(
                [
                    str(org_path / destination / subdir)
                    for subdir in dir_config.subdirectories.keys()
                ]
            )

        else:
            expanded_destinations.append(str(destination))

    # TODO: extract into function
    for dir_name, dir_config in configured_directories.items():
        for subdir_name, subdir_config in dir_config.subdirectories.items():
            if f"{dir_name}/{subdir_name}" in expanded_destinations:
                subdir_config.download = True
            subdir_path = org_path / dir_name / subdir_name
            if not await subdir_path.exists():
                os.mkdir(subdir_path)

    # TODO: better key/value naming
    for org_dir in configured_directories.values():
        if all(not subdir.download for subdir in org_dir.subdirectories.values()):
            continue

        await org_dir.download_organization()

    # TODO: test if no subdirs were specified
    # TODO: test with deleting objects
    # TODO: test just empty org file (subdirs should not be required then
    # TODO: org_path assumption test

    if commit:
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", commit_message])
