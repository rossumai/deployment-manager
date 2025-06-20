import shutil
import subprocess
import sys
from typing import Any
from anyio import Path
import questionary

from deployment_manager.common.git import PullStrategy, get_changed_file_paths
from rossum_api.api_client import Resource

from deployment_manager.common.determine_path import (
    determine_object_type_from_url,
)
from deployment_manager.common.read_write import (
    read_json,
)
from deployment_manager.utils.consts import display_warning, settings, display_info


def replace_code_paths(file_paths: list[Path]):
    """Since only .json files are compared when pulling, this flags the json file as changed if its code (.py/.js) file has changed."""
    replaced_paths = []

    for path in file_paths:
        if path.suffix in [".py", ".js"]:
            if path.parent.name == "hooks":
                path = path.with_suffix(".json")
            elif path.parent.name == settings.FORMULA_DIR_NAME:
                path = path.parent.parent / "schema.json"
        replaced_paths.append(path)

    return replaced_paths



async def get_changed_files(org_path):
    changed_files = get_changed_file_paths(org_path)
    changed_files = list(map(lambda x: x[1], changed_files))
    changed_files = replace_code_paths(changed_files)
    return changed_files



async def get_pull_decision(
    path: Path,
    remote_object: Any,
    changed_files: list,
    type: str,
    parent_dir_reference: "DownloadOrganizationDirectory" = None,

) -> PullStrategy:
    if await path.exists():
        local_file = await read_json(path)

        object_type = determine_object_type_from_url(local_file.get("url", ""))
        # Queues might have their hooks attribute changed. Same for schema.rules
        # This does not update the timestamp in the DB because this change is only done on hooks entities.
        if (
            (local_timestamp := local_file.get("modified_at", ""))
            != (remote_timestamp := remote_object.get("modified_at", ""))
            or (
                object_type == Resource.Queue
                and local_file.get("hooks", []) != remote_object.get("hooks", [])
            )
            or (
                object_type == Resource.Schema
                and local_file.get("rules", []) != remote_object.get("rules", [])
            )
        ):
            # there are some changes in remote
            if path in changed_files:
                # there are some local changes, we need to solve it
                if not parent_dir_reference or parent_dir_reference.pull_strategy == PullStrategy.ask or parent_dir_reference.pull_strategy is None:
                    display_warning(
                        f"File [green]{path}[/green] has local unversioned changes [white](local: {local_timestamp} | remote: {remote_timestamp})[/white]."
                    )
                    strategy = await questionary.text(
                        message="How do you want to handle conflicts?",
                        instruction="(skip/overwrite/merge)",
                    ).ask_async()
                    strategy = PullStrategy(strategy)
                    if parent_dir_reference and parent_dir_reference.pull_strategy is None:
                        all_ = await questionary.confirm(
                            message=f"Do you want to apply it to all conflicts for {type}?",
                            default=True
                        ).ask_async()
                        if all_:
                            parent_dir_reference.pull_strategy = strategy
                        else:
                            parent_dir_reference.pull_strategy = PullStrategy.ask

                    return strategy
                return parent_dir_reference.pull_strategy
            # there are no local changes, just pull remote
            return PullStrategy.overwrite
        # no need to pull, there are no remote changes
        return PullStrategy.skip
    # local file not found, we just write
    return PullStrategy.overwrite

async def should_write_object(
    path: Path,
    remote_object: Any,
    changed_files: list,
    parent_dir_reference: "DownloadOrganizationDirectory",
):
    if await path.exists():
        local_file = await read_json(path)

        object_type = determine_object_type_from_url(local_file.get("url", ""))
        # Queues might have their hooks attribute changed. Same for schema.rules
        # This does not update the timestamp in the DB because this change is only done on hooks entities.
        if (
            (local_timestamp := local_file.get("modified_at", ""))
            != (remote_timestamp := remote_object.get("modified_at", ""))
            or (
                object_type == Resource.Queue
                and local_file.get("hooks", []) != remote_object.get("hooks", [])
            )
            or (
                object_type == Resource.Schema
                and local_file.get("rules", []) != remote_object.get("rules", [])
            )
        ):
            if (
                path in changed_files
                and not parent_dir_reference.ignore_changed_file_warnings
            ):
                display_warning(
                    f"File [green]{path}[/green] has local unversioned changes [white](local: {local_timestamp} | remote: {remote_timestamp})[/white]."
                )
                user_answer = await questionary.text(
                    message="Should the remote version overwrite the local one?",
                    instruction="(y/n/yy)",
                ).ask_async()
                # Disable warnings for all other queues
                if user_answer.casefold() == "yy":
                    parent_dir_reference.ignore_changed_file_warnings = True

                return user_answer == "y" or user_answer == "yy"

            return True

    else:
        return True


async def delete_empty_folders(root: Path):
    deleted = set()

    # Walk through the directories in reverse (bottom-up)
    async for current_dir in root.rglob("*"):
        current_dir = Path(current_dir)

        if await current_dir.is_dir():
            # Check if the directory has subdirectories or files
            subdirs = [
                subdir
                async for subdir in current_dir.iterdir()
                if await subdir.is_dir()
            ]
            files = [
                file async for file in current_dir.iterdir() if await file.is_file()
            ]

            # If no files or valid subdirectories, delete the directory
            if not files and not subdirs:
                shutil.rmtree(current_dir)
                deleted.add(current_dir)

    return deleted


async def delete_empty_formula_dir(ws_root: Path):
    # Iterate over workspaces in the root path
    async for ws_path in ws_root.iterdir():
        if not await ws_path.is_dir():
            continue
        queues_path = ws_path / "queues"
        if not await queues_path.exists():
            continue

        async for queue_path in queues_path.iterdir():
            if not await queue_path.is_dir():
                continue

            contents = [item async for item in queue_path.iterdir()]

            # If the directory only contains a 'formula' folder, delete it
            if len(contents) == 1 and contents[0].name == settings.FORMULA_DIR_NAME:
                shutil.rmtree(queue_path)
