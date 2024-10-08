import json

from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.common.modified_at import (
    check_modified_timestamp,
)
from project_rossum_deploy.common.determine_path import determine_object_type_from_url
from project_rossum_deploy.common.read_write import (
    determine_object_type_from_path,
    read_json,
    write_json,
)
from project_rossum_deploy.utils.consts import create_mismatch_warning, display_error
from project_rossum_deploy.utils.consts import GIT_CHARACTERS
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
)


async def update_object(
    client: ElisAPIClient,
    path: Path = None,
    errors: list = None,
    force=False,
):
    try:
        object = await read_json(path)

        id, url = object.get("id", None), object.get("url", None)
        if not id:
            raise Exception("Missing object ID")
        if not url:
            raise Exception("Missing object URL")

        resource = determine_object_type_from_url(url)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, resource, id, object
        )
        if not force and not local_remote_timestamp_synced:
            display_error(create_mismatch_warning(resource, id))
            errors.append({"op": GIT_CHARACTERS.UPDATED, "path": path})
            return "timestamp"

        # Inboxes are ready-only in Elis API, but we don't ignore them when pulling to distinguish queues with and without inboxes
        if resource == Resource.Queue:
            object.pop("inbox", None)

        result = await client._http_client.update(resource, id, object)

        # Just to update the timestamp
        await write_json(
            path, result, resource, log_message=f"Updating timestamp for {path}"
        )

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

        result = await client._http_client.create(resource, object)

        # Just to update the timestamp
        await write_json(
            path, result, resource, log_message=f"Updating timestamp for {path}"
        )

        print(f'Successfully created {resource} with ID "{result["id"]}".')
        return result
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
            client, resource, id, object
        )
        if not force and not local_remote_timestamp_synced:
            display_error(create_mismatch_warning(resource, id))
            return

        await client._http_client.delete(resource, id)

        print(f'Successfully deleted {resource} with ID "{id}".')
    except Exception as e:
        display_error(f'Error while deleting object with path "{path}": {e}', e)
        errors.append({"op": GIT_CHARACTERS.DELETED, "path": path})
