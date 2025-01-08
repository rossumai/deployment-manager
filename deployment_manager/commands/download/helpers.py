import os
import shutil
from typing import Any
from anyio import Path
import anyio
import questionary
from rossum_api.api_client import Resource

from deployment_manager.common.determine_path import (
    determine_object_type_from_path,
)
from deployment_manager.common.read_write import (
    read_json,
)
from deployment_manager.utils.consts import display_warning, settings


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


async def should_write_object(path: Path, remote_object: Any, changed_files: list):
    if await path.exists():
        local_file = await read_json(path)

        object_type = (
            determine_object_type_from_path(path)
            if "organization" not in str(path)
            else ""
        )
        # Queues are always pulled - their hooks/webhooks attribute might have changed.
        # This does not update the timestamp in the DB because this change is only done on hooks entities.
        if (local_timestamp := local_file.get("modified_at", "")) != (
            remote_timestamp := remote_object.get("modified_at", "")
        ) or (
            object_type == Resource.Queue
            and local_file.get("hooks", []) != remote_object.get("hooks", [])
        ):
            if path in changed_files:
                display_warning(
                    f"File [green]{path}[/green] has local unversioned changes [white](local: {local_timestamp} | remote: {remote_timestamp})[/white]."
                )
                return await questionary.confirm(
                    "Should the remote version overwrite the local one?",
                ).ask_async()
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


async def delete_orphaned_formulas(ws_root: Path):
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
            if len(contents) == 1 and contents[0].name == "formulas":
                shutil.rmtree(queue_path)
