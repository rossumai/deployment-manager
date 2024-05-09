from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.consts import (
    settings,
)
from project_rossum_deploy.utils.functions import display_error


def determine_object_type_from_path(path: Path) -> Resource:
    split_path = str(path).split("/")
    type = split_path[-2] if len(split_path) > 1 else path.stem + "s"
    allowed_types = set(resource.value for resource in Resource)
    if type in allowed_types:
        return Resource(type)
    else:
        type = split_path[-3] if len(split_path) > 1 else path.stem + "s"
        allowed_types = set(resource.value for resource in Resource)
        if type in allowed_types:
            return Resource(type)
        else:
            raise Exception(f'Unknown resource "{type}".')


def determine_object_type_from_url(url: str) -> Resource:
    split_path = url.split("/")
    type = split_path[-2]
    allowed_types = set(resource.value for resource in Resource)
    if type in allowed_types:
        return Resource(type)
    else:
        raise Exception(f'Unknown resource "{type}".')


async def check_modified_timestamp(
    client: ElisAPIClient, resource: Resource, id: int, local_timestamp: str
):
    object = await client._http_client.fetch_one(resource, id)
    if object['modified_at'] != local_timestamp:
        display_error(
            f'WARNING: Could not {settings.UPLOAD_COMMAND_NAME} {resource} with ID "{id}". Rossum has a version with a different timestamp.\n This means that the object was updated without PRD. Please stash your changes for these objects and run {settings.DOWNLOAD_COMMAND_NAME} first.'
        )
        return False

    return True
