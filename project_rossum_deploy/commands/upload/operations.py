import json
import os

from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.upload.helpers import (
    check_modified_timestamp,
    determine_object_type_from_path,
    determine_object_type_from_url,
)
from project_rossum_deploy.utils.consts import GIT_CHARACTERS
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    display_error,
    read_json,
    templatize_name_id,
    write_json,
)


async def update_object(
    client: ElisAPIClient,
    path: Path = None,
    object: dict = None,
    errors: list = None,
    force=False,
):
    try:
        if not object:
            object = await read_json(path)

        id, url = object.get("id", None), object.get("url", None)
        if not id:
            raise Exception("Missing object ID")
        if not url:
            raise Exception("Missing object URL")

        resource = determine_object_type_from_url(url)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, resource, id, object["modified_at"]
        )
        if not force and not local_remote_timestamp_synced:
            return

        # Inboxes are ready-only in Elis API, but we don't ignore them when pulling to distinguish queues with and without inboxes
        if resource == Resource.Queue:
            object.pop("inbox", None)

        result = await client._http_client.update(resource, id, object)

        if path:
            os.remove(path)
            if str(object["id"]) in path.stem:
                # Recreate the path in case the name of object changed
                path = path.with_stem(templatize_name_id(object["name"], object["id"]))
            await write_json(path, object)

        print(f'Successfully updated {resource} with ID "{id}".')
        return result
    except Exception as e:
        if path:
            display_error(f'Error while updating object with path "{path}": {e}', e)
        else:
            id = object.get("id", None)
            descriptor = id if id else json.dump(object)
            display_error(f"Error while updating object {descriptor}: {e}", e)
        errors.append({"op": GIT_CHARACTERS.UPDATED, "path": path})


async def create_object(
    path: Path, client: ElisAPIClient, errors: list = None, force=False
):
    try:
        object = await read_json(path)
        object["id"] = None
        resource = determine_object_type_from_path(path)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, resource, id, object["modified_at"]
        )
        if not force and not local_remote_timestamp_synced:
            return

        created_object = await client._http_client.create(resource, object)

        os.remove(path)
        path = path.with_stem(
            templatize_name_id(created_object["name"], created_object["id"])
        )
        await write_json(path, created_object)
        print(f'Successfully created {resource} with ID "{created_object["id"]}".')
    except Exception as e:
        display_error(f'Error while creating object with path "{path}": {e}', e)
        errors.append({"op": GIT_CHARACTERS.CREATED, "path": path})


async def delete_object(
    path: Path, client: ElisAPIClient, errors: list = None, force=False
):
    try:
        _, id = detemplatize_name_id(path)
        resource = determine_object_type_from_path(path)

        object = await read_json(path)
        local_remote_timestamp_synced = await check_modified_timestamp(
            client, resource, id, object["modified_at"]
        )
        if not force and not local_remote_timestamp_synced:
            return

        await client._http_client.delete(resource, id)

        os.remove(path)
        print(f'Successfully deleted {resource} with ID "{id}".')
    except Exception as e:
        display_error(f'Error while deleting object with path "{path}": {e}', e)
        errors.append({"op": GIT_CHARACTERS.DELETED, "path": path})
