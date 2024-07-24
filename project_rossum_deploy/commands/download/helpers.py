import asyncio
import os
import shutil
from typing import Any
from anyio import Path
from rich.prompt import Confirm
from rich import print
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource
from rich.panel import Panel

from project_rossum_deploy.utils.functions import (
    find_object_by_key,
)
from project_rossum_deploy.common.determine_path import (
    determine_object_type_from_path,
    determine_object_type_from_url,
)
from project_rossum_deploy.common.mapping import extract_flat_lookup_table
from project_rossum_deploy.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    find_formula_fields_in_schema,
    read_json,
)
from project_rossum_deploy.utils.consts import display_warning, settings
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    find_object_in_project,
    find_all_object_paths,
    flatten,
    templatize_name_id,
)


class ObjectMovedBetweenSourceTargetException(Exception):
    status_code = 404


class InactiveQueueException(Exception):
    status_code = 404


class DifferentNameException(Exception):
    status_code = 404


class DifferentPathException(Exception):
    status_code = 404


class MissingParentObjectException(Exception):
    status_code = 404


def replace_code_paths(file_paths: list[Path]):
    """Since only .json files are compared when pulling, this flags the json file as changed if its code (.py/.js) file has changed."""
    replaced_paths = []

    for path in file_paths:
        if path.suffix in [".py", ".js"]:
            if path.parent.name == "hooks":
                path = path.with_suffix(".json")
            elif settings.FORMULA_DIR_PREFIX in path.parent.name:
                only_schema_name = path.parent.name.split(":")[1]
                path = path.parent.with_name(only_schema_name).with_suffix(".json")
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
                return Confirm.ask(
                    f'File "{path}" has local unversioned changes (local: {local_timestamp} | remote: {remote_timestamp}). Should the remote version overwrite the local one?',
                )
            return True

    else:
        return True


def is_within_git_dir(path: Path) -> bool:
    """
    Check if the given path is within a .git directory.
    """
    for parent in path.parents:
        if parent.name == '.git':
            return True
    return False


def delete_empty_folders(root: Path):
    deleted = set()

    for current_dir, subdirs, files in os.walk(root, topdown=False):
        current_dir_path = Path(current_dir)

        # Skip if the current directory is within a .git directory
        if is_within_git_dir(current_dir_path):
            continue

        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
                break

        if not any(files) and not still_has_subdirs:
            os.rmdir(current_dir)
            deleted.add(current_dir)

    return deleted


async def check_schema_formula_fields_existence(remote_object: dict, path: Path):
    formula_fields = find_formula_fields_in_schema(remote_object["content"])
    formula_field_ids = [f[0] for f in formula_fields]
    formula_directory_path = create_formula_directory_path(
        path, remote_object.get("name", ""), remote_object.get("id", "")
    )
    if not await formula_directory_path.exists():
        return

    async for formula_path in formula_directory_path.iterdir():
        if formula_path.stem not in formula_field_ids:
            print(
                Panel(
                    f"Deleting a local formula field code file that no longer exists in Rossum: {path}",
                    style="yellow",
                )
            )
            os.remove(formula_path)


async def remove_local_nonexistent_object(
    path: Path,
    client: ElisAPIClient,
    destination: str,
    source_ids: list[int],
    target_ids: list[int],
):
    object = await read_json(path)
    url, id = object.get("url", ""), object.get("id", "")
    object_type = determine_object_type_from_url(url)

    try:
        # Source object was put on a right hand side in mapping and became target
        # The left hand side was deleted
        # This object should not be in the source directory anymore
        if (
            destination == settings.SOURCE_DIRNAME
            and id in target_ids
            and id not in source_ids
        ):
            raise ObjectMovedBetweenSourceTargetException
        # The mirror case - delete from target if it is not referenced as a right hand side in mapping
        elif (
            destination == settings.TARGET_DIRNAME
            and id not in target_ids
            and id in source_ids
        ):
            raise ObjectMovedBetweenSourceTargetException
        # ID not found because it was deleted from Rossum
        remote_object = await client._http_client.request_json(method="GET", url=url)

        # Special queue edge case (they are deleted after some period)
        if remote_object.get("status", "") == "deletion_requested":
            raise InactiveQueueException

        # Name might have changed
        previous_name, _ = detemplatize_name_id(path)
        # Use the same process to create the name (e.g., missing forbidden chars like '/')
        path_from_remote = templatize_name_id(
            remote_object.get("name", ""), remote_object.get("id", "")
        )
        cleaned_name, _ = detemplatize_name_id(path_from_remote)
        # Inboxes are in the queue folder, but can have a different name than their queue
        if cleaned_name != previous_name and object_type != Resource.Inbox:
            raise DifferentNameException

        # Workspace name might have changed, remove queue and inbox files inside
        if object_type == Resource.Queue:
            await check_queue_existence(client, remote_object, path)
        elif object_type == Resource.Inbox:
            await check_inbox_existence(client, remote_object, path)
        elif object_type == Resource.Schema:
            await check_schema_formula_fields_existence(remote_object, path)

    except (
        APIClientError,
        InactiveQueueException,
        DifferentNameException,
        DifferentPathException,
        MissingParentObjectException,
        ObjectMovedBetweenSourceTargetException,
    ) as e:
        if e.status_code != 404:
            raise e

        print(
            Panel(
                f"Deleting a local object that no longer exists in Rossum or was moved between {settings.SOURCE_DIRNAME}/{settings.TARGET_DIRNAME} ({str(e.__class__.__name__)}): {path}",
                style="yellow",
            )
        )
        os.remove(path)

        previous_name, previous_id = detemplatize_name_id(path)
        if object_type == Resource.Schema:
            formula_directory_path = create_formula_directory_path(
                path, previous_name, previous_id
            )
            if await formula_directory_path.exists():
                shutil.rmtree(formula_directory_path)
        elif object_type == Resource.Hook:
            object["name"] = previous_name
            custom_hook_code_path = create_custom_hook_code_path(path, object)
            if custom_hook_code_path:
                os.remove(custom_hook_code_path)


async def check_queue_existence(client: ElisAPIClient, remote_object: dict, path: Path):
    try:
        ws = await client._http_client.request_json(
            method="GET", url=remote_object["workspace"]
        )
    except APIClientError as e:
        if e.status_code != 404:
            raise e

        raise MissingParentObjectException

    compare_paths(original_path=path, ws=ws, queue=remote_object, suffix="queue.json")


async def check_inbox_existence(client: ElisAPIClient, remote_object: dict, path: Path):
    try:
        queue = await client._http_client.request_json(
            method="GET", url=remote_object["queues"][0]
        )
        if not queue["workspace"]:
            raise MissingParentObjectException
        ws = await client._http_client.request_json(
            method="GET", url=queue["workspace"]
        )
    except (APIClientError, MissingParentObjectException) as e:
        if e.status_code != 404:
            raise e

        raise MissingParentObjectException

    compare_paths(original_path=path, ws=ws, queue=queue, suffix="inbox.json")


def compare_paths(original_path: Path, ws, queue, suffix):
    """Verifies that the path of the local object is the same as the path of that objects downloaded from Rossum. Covers cases of names changing for workspaces, queues, and inboxes.

    Raises:
        DifferentPathException
    """
    ws_path_part = templatize_name_id(ws["name"], ws["id"])
    queue_path_path = templatize_name_id(queue["name"], queue["id"])
    path_parts = str(original_path).split("/")
    latest_path = (
        Path(*path_parts[:-4]) / ws_path_part / "queues" / queue_path_path / suffix
    )

    # If the original path was absollut
    if original_path.is_absolute():
        latest_path = Path("/" + str(latest_path))
    if latest_path != original_path:
        raise DifferentPathException


async def remove_local_nonexistent_objects(
    client: ElisAPIClient, base_path: Path, destination: str, mapping: dict
):
    """
    Checks that the local object still exists in Rossum and removes its local file if not.
    """

    object_paths = await find_all_object_paths(base_path / destination)
    # Ignore the org file, it should never be deleted
    try:
        object_paths.remove(Path(base_path / destination / "organization.json"))
    # The file might not be there for target
    except Exception:
        ...

    lookup_table = extract_flat_lookup_table(mapping)
    source_ids = list(lookup_table.keys())
    target_ids = flatten(list(lookup_table.values()))
    await asyncio.gather(
        *[
            remove_local_nonexistent_object(
                path, client, destination, source_ids, target_ids
            )
            for path in object_paths
        ]
    )

    delete_empty_folders(base_path)


async def determine_object_destination(
    object: dict,
    object_type: str,
    org_path: Path,
    mapping: dict,
    sources: dict,
    targets: dict,
):
    if object["id"] in targets[object_type + "s"] or await find_object_in_project(
        object, org_path / settings.TARGET_DIRNAME / (object_type + "s")
    ):
        destination = settings.TARGET_DIRNAME
    # Cross-org migration means that there is no target dir in this project
    # Both organizations = projects only have the source dir
    elif (
        not settings.IS_PROJECT_IN_SAME_ORG
        or object["id"] in sources[object_type + "s"]
    ):
        destination = settings.SOURCE_DIRNAME
    else:
        object_name, object_id = object["name"], object["id"]
        user_decision = Confirm(
            f'Should the {object_type} "{object_name}" ({object_id}) be in {settings.SOURCE_DIRNAME}? Otherwise, it will be understood as {settings.TARGET_DIRNAME}.'
        )
        destination = (
            settings.SOURCE_DIRNAME if user_decision else settings.TARGET_DIRNAME
        )

    return destination


async def get_all_objects_for_destination(org_path: Path, destination: str) -> tuple:
    """Find all .json objects stored locally for the given destination.

    Args:
        org_path (Path): Base project path, usually simply `"./"`
        destination (str): Either source or target

    Returns:
        tuple: The same tuple of objects as a download of a single organization (source/target) would
    """
    organization, workspaces, schemas, hooks, queues, inboxes = {}, [], [], [], [], []

    object_paths = await find_all_object_paths(org_path / destination)
    for object_path in object_paths:
        object = await read_json(object_path)
        if object_path.name == "organization.json":
            organization = object
            continue

        object_url = object.get("url", None)
        if not object_url:
            display_warning(f"Object with path '{object_path}' has no url - skipping.")
        type = determine_object_type_from_url(object_url)
        match type:
            case Resource.Workspace:
                # Get rid of URLs, the actual objects will be 'sideloaded' in the next step
                object["queues"] = []
                workspaces.append(object)
            case Resource.Schema:
                schemas.append(object)
            case Resource.Hook:
                hooks.append(object)
            case Resource.Queue:
                # Get rid of URLs, the actual objects will be 'sideloaded' in the next step
                object["inbox"] = None
                queues.append(object)
            case Resource.Inbox:
                inboxes.append(object)
            case _:
                display_warning(f"Unrecognized type '{type}' - skipping.")
                continue

    # Put queues and inboxes into the corresponding parent object
    for queue in queues:
        ws_url = queue.get("workspace", None)
        if not ws_url:
            display_warning(
                f"Queue '{queue.get('id', 'missing_id')}' has no workspace URL - skipping."
            )
            continue
        workspace = find_object_by_key("url", ws_url, workspaces)
        if not workspace:
            display_warning(f"Could not find workspace with URL '{ws_url}' - skipping.")
            continue
        workspace["queues"] = workspace["queues"] if workspace["queues"] else []
        workspace["queues"].append(queue)

    for inbox in inboxes:
        queue_url = inbox.get("queues", [None])[0]
        if not queue_url:
            display_warning(
                f"Inbox '{inbox.get('id', 'missing_id')}' has no queue URL - skipping."
            )
            continue

        queue = find_object_by_key("url", queue_url, queues)
        if not queue:
            display_warning(f"Could not find queue with URL '{queue_url}' - skipping.")
            continue
        queue["inbox"] = inbox

    return (
        organization,
        [(destination, workspace) for workspace in workspaces],
        [(destination, schema) for schema in schemas],
        [(destination, hook) for hook in hooks],
    )
