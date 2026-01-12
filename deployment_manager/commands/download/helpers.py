import json
import shutil
from typing import Any
from anyio import Path
import questionary
from rossum_api.domain_logic.resources import Resource

from deployment_manager.common.determine_path import (
    determine_object_type_from_url,
)
from deployment_manager.common.read_write import (
    read_object_from_json,
    NON_VERSIONED_ATTRIBUTES_FILE_LOCK,
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


async def should_write_object(
    path: Path,
    remote_object: Any,
    changed_files: list,
    parent_dir_reference: "DownloadOrganizationDirectory",
):
    if await path.exists():
        local_file = await read_object_from_json(path)

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


async def delete_objects_non_versioned_attributes(path: Path):
    # this method deletes the object's data in non_versioned_attributes file

    if len(path.parents) < 3:
        # outside subdirectory, no non_versioned_attribute allowed at this level
        return

    subdir_path: Path = path.parents[-3] ## path to dir/subdir, resp. org/suborg
    file_path_parts_from_subdir: tuple[str, ...] = path.parts[2:] # parts of path from dir/subdir, in list
    non_versioned_file = subdir_path/settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME
    if await non_versioned_file.exists():
        async with NON_VERSIONED_ATTRIBUTES_FILE_LOCK:
            with open(non_versioned_file, 'r') as f:
                data = json.load(f)

            # searching for the key in json
            parent = data
            for path_part in file_path_parts_from_subdir[:-1]:  # Go up to the second-to-last key. For the last one, del will be called later.
                if path_part in parent:
                    parent = parent[path_part]
                else:
                    return

            # The last key in the list is the one to delete
            key_to_delete = file_path_parts_from_subdir[-1]

            # Delete the key from the parent dictionary
            if key_to_delete in parent:
                del parent[key_to_delete]
            else:
                return

            # if the key was found and deleted, write updated non_versioned_attributes file
            with open(non_versioned_file, 'w') as f:
                json.dump(data, f, indent=4)


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
                await delete_objects_non_versioned_attributes(current_dir)

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
