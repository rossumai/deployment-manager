from pydantic import BaseModel
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from rich import print
from rich.panel import Panel

from project_rossum_deploy.utils.functions import (
    find_object_by_id,
)
from project_rossum_deploy.common.modified_at import check_modified_timestamp
from project_rossum_deploy.utils.consts import (
    settings,
)


class TargetObjectNotFoundException(Exception):
    def __init__(self, target_id, *args, **kwargs):
        msg = f'Not could not find target object with ID "{target_id}" locally. If it exists only on remote or is in {settings.SOURCE_DIRNAME}, please {settings.DOWNLOAD_COMMAND_NAME} it first.'
        super().__init__(msg, *args, **kwargs)


async def upload_organization(
    client: ElisAPIClient,
    organization: dict,
    local_target_organization: dict = None,
    errors={},
    force=False,
):
    if not local_target_organization:
        return

    target_organization_id = local_target_organization["id"]
    local_remote_timestamp_synced = await check_modified_timestamp(
        client,
        Resource.Organization,
        target_organization_id,
        local_target_organization,
    )
    if not force and not local_remote_timestamp_synced:
        errors[target_organization_id] = (
            Resource.Organization,
            local_target_organization.get("name", ""),
        )
        return local_target_organization

    if organization["id"] == target_organization_id:
        print(
            Panel(
                f"Skipping organization {settings.MIGRATE_COMMAND_NAME} - they are the same."
            )
        )
        return local_target_organization

    # Use only a subset of org fields where it makes sense to migrate
    organization_fields = {k: organization[k] for k in settings.ORGANIZATION_FIELDS}

    return await client._http_client.update(
        Resource.Organization, id_=target_organization_id, data=organization_fields
    )


async def upload_inbox(
    client: ElisAPIClient,
    inbox: dict,
    target_id: int,
    target_objects=[],
    errors={},
    force=False,
):
    if target_id:
        local_object = find_object_by_id(target_id, target_objects)
        if not local_object:
            raise TargetObjectNotFoundException(target_id)

        local_remote_timestamp_synced = await check_modified_timestamp(
            client, Resource.Inbox, target_id, local_object
        )
        if not force and not local_remote_timestamp_synced:
            errors[target_id] = (Resource.Inbox, local_object.get("name", ""))
            return local_object

        result = await client._http_client.update(
            Resource.Inbox, id_=target_id, data=inbox
        )
        print(f'Released (updated) inbox "{inbox['id']}" -> "{target_id}".')
        return result
    else:
        result = await client._http_client.create(Resource.Inbox, inbox)
        print(f'Released (created) inbox "{inbox['id']}" -> "{result['id']}".')
        return result


class Credentials(BaseModel):
    # TODO: username + password support
    token: str
    url: str
