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

from project_rossum_deploy.common.determine_path import (
    determine_object_type_from_url,
)
from project_rossum_deploy.common.write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    find_formula_fields_in_schema,
)
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    find_all_object_paths,
    read_json,
    templatize_name_id,
)


class InactiveQueueException(Exception):
    status_code = 404


class DifferentNameException(Exception):
    status_code = 404


class DifferentPathException(Exception):
    status_code = 404


async def should_write_object(path: Path, remote_object: Any, changed_files: list):
    if await path.exists():
        local_file = await read_json(path)

        if (local_timestamp := local_file.get("modified_at", "")) != (
            remote_timestamp := remote_object.get("modified_at", "")
        ):
            if path in changed_files:
                return Confirm.ask(
                    f'File "{path}" has local unversioned changes (local: {local_timestamp} | remote: {remote_timestamp}). Should the remote version overwrite the local one?',
                )
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
                    f"Deleting local formula field code file that no longer exists in Rossum: {path}",
                    style="yellow",
                )
            )
            os.remove(formula_path)


async def remove_local_nonexistent_object(path: Path, client: ElisAPIClient):
    object = await read_json(path)
    url = object.get("url", "")
    object_type = determine_object_type_from_url(url)

    try:
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
        # Inboxes are in the queue folder so they are an edge case (names might not the same for the queue and its inbox)
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
    ) as e:
        if e.status_code == 404:
            print(
                Panel(
                    f"Deleting local object that no longer exists in Rossum: {path}",
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
                custom_hook_code_path = create_custom_hook_code_path(
                    path, previous_name, previous_id
                )
                if custom_hook_code_path:
                    os.remove(custom_hook_code_path)


async def check_queue_existence(client: ElisAPIClient, remote_object: dict, path: Path):
    ws = await client._http_client.request_json(
        method="GET", url=remote_object["workspace"]
    )
    ws_path_part = templatize_name_id(ws["name"], ws["id"])
    queue_path_path = templatize_name_id(remote_object["name"], remote_object["id"])
    path_parts = str(path).split("/")
    latest_path = (
        Path(*path_parts[:-4])
        / ws_path_part
        / "queues"
        / queue_path_path
        / "queue.json"
    )
    if latest_path != path:
        raise DifferentPathException


async def check_inbox_existence(client: ElisAPIClient, remote_object: dict, path: Path):
    queue = await client._http_client.request_json(
        method="GET", url=remote_object["queues"][0]
    )
    ws = await client._http_client.request_json(method="GET", url=queue["workspace"])
    ws_path_part = templatize_name_id(ws["name"], ws["id"])
    queue_path_path = templatize_name_id(queue["name"], queue["id"])
    path_parts = str(path).split("/")
    latest_path = (
        Path(*path_parts[:-4])
        / ws_path_part
        / "queues"
        / queue_path_path
        / "inbox.json"
    )
    if latest_path != path:
        raise DifferentPathException


async def remove_local_nonexistent_objects(client: ElisAPIClient, base_path: Path):
    """
    Checks that the local object still exists in Rossum and removes its local file if not.
    """

    object_paths = await find_all_object_paths(base_path)
    # Ignore the org file, it should never be deleted
    try:
        object_paths.remove(Path(base_path / "organization.json"))
    # The file might not be there for target
    except Exception:
        ...

    await asyncio.gather(
        *[remove_local_nonexistent_object(path, client) for path in object_paths]
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


async def find_object_in_project(object: dict, base_path: Path):
    file_name = templatize_name_id(object["name"], object["id"])
    return (
        await (base_path / file_name).exists()
        or await (base_path / (file_name + ".json")).exists()
    )
