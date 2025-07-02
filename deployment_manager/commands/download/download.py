import os
import subprocess

import questionary
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
from deployment_manager.utils.consts import display_error, display_warning, settings, display_info
from deployment_manager.utils.functions import (
    coro,
)

# TODO: fix foreign JSONs in the subdir (mongo.json...)


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
    type=click.Path(path_type=Path),
)
@click.option(
    "--rebase",
    "-r",
    default=False,
    is_flag=True,
    help="Merge local changes with remote changes using git",
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
    "--skip-objects-without-subdir",
    "-s",
    default=False,
    is_flag=True,
    help="If there are objects whose subdir cannot be determined, user is not manually prompted - objects are not downloaded.",
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
    rebase: bool = False,
    commit: bool = False,
    message: str = "",
    all: bool = False,
    skip_objects_without_subdir: bool = False,
):
    await download_destinations(
        destinations=destinations,
        commit_message=message,
        commit=commit,
        download_all=all,
        skip_objects_without_subdir=skip_objects_without_subdir,
        rebase=rebase,
    )


async def download_destinations(
    destinations: tuple[Path],
    project_path: Path = None,
    commit: bool = False,
    commit_message: str = "",
    download_all: bool = False,
    skip_objects_without_subdir: bool = False,
    rebase: bool = False,
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
            name=name,
            project_path=project_path,
            skip_objects_without_subdir=skip_objects_without_subdir,
            download_all=download_all,
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

    for org_dir_name, org_dir_config in configured_directories.items():
        if all(not subdir.include for subdir in org_dir_config.subdirectories.values()):
            continue

        for subdir_name in org_dir_config.subdirectories.keys():
            subdir_path = project_path / org_dir_name / subdir_name
            if not await subdir_path.exists():
                os.makedirs(subdir_path, exist_ok=True)

        stashed = False
        try:
            if rebase:
                # first stash local changes, so there won't be any conflicts during pull
                stash = subprocess.run(["git", "stash", "-u"], capture_output=True, text=True, check=True)
                if stash.stdout.startswith("Saved "):
                    # there were some local changes stashed
                    stashed = True
            await org_dir_config.download_organization()
            if stashed:
                # adding updated files to be able to pop from stash and resolve the conflicts if any
                subprocess.run(["git", "add", "-u"])
                pop = subprocess.run(["git", "stash", "pop"], capture_output=True, text=True, check=False)
                stashed = False
                if pop.returncode != 0:
                    all_unmerged_files = set()
                    status = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
                    while True:
                        if "Unmerged paths" not in status.stdout:
                            break
                        currently_unmerged_changes = []
                        for line in status.stdout.splitlines():
                            if "both modified:" in line:
                                filename = line.replace("both modified:", "").strip()
                                currently_unmerged_changes.append(filename)
                                all_unmerged_files.add(filename)
                        display_warning(
                            f"You need to solve local conflicts using git. Current = pulled from remote vs. Incoming = your local-only changes.\n{'_'*80}"
                            f"\nUnmerged files:\n{'\n'.join(currently_unmerged_changes)}")
                        await questionary.confirm(
                            "Press enter after solving the conflict", default=True
                        ).ask_async()
                        status = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)

                    if await questionary.confirm(
                        "Conflicts were solved successfully. Do you want to automatically push and commit those files where conflict occurred?"
                    ).ask_async():
                        # need to import here to avoid circular imports
                        from deployment_manager.commands.upload.upload import upload_destinations
                        await upload_destinations(
                            destinations=(org_dir_config.org_path, ),
                            include_only_files=[Path(i) for i in all_unmerged_files],
                            show_commit_message=False
                        )
                    else:
                        display_info(f"Important: Do not forget to run `prd2 push` after solving conflicts, before commiting the files locally.\n{'_'*80}"
                                     f"Files with merged changes which need to be pushed before commiting:\n{'\n'.join(all_unmerged_files)}")



        except Exception as e:
            display_error(
                f"Error during the {settings.DOWNLOAD_COMMAND_NAME} of {org_dir_config.display_label}: {e}",
                e,
            )
            if stashed:
                subprocess.run(["git", "stash", "pop"], check=False)


    # TODO: test with deleting objects
    # TODO: test just empty org file (subdirs should not be required then
    # TODO: org_path assumption test

    if commit and not rebase:
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", commit_message])
