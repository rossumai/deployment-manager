import os
from typing import Any
from anyio import Path
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
                    f'File "{path}" has local unversioned changes (local: {local_timestamp} | remote: {remote_timestamp}).'
                )
                return await questionary.confirm(
                    "Should the remote version overwrite the local one?",
                ).ask_async()
            return True

    else:
        return True


def delete_empty_folders(root: Path):
    deleted = set()

    for current_dir, subdirs, files in os.walk(root, topdown=False):
        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
                break

        if not any(files) and not still_has_subdirs:
            os.rmdir(current_dir)
            deleted.add(current_dir)

    return deleted
