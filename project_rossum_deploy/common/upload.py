from rossum_api import ElisAPIClient
from rossum_api.models import Schema, Hook, Workspace, Queue, Inbox, Organization
from rossum_api.api_client import Resource


async def upload_organization(
    client: ElisAPIClient, organization: Organization, target: int
):
    try:
        if not target:
            return

        return await client._http_client.update(
            Resource.Organization, id_=target, data=organization
        )
    except Exception as e:
        print(f"Error while uploading organization: {e}")


async def upload_workspace(client: ElisAPIClient, workspace: Workspace, target: int):
    if target:
        return await client._http_client.update(
            Resource.Workspace, id_=target, data=workspace
        )
    else:
        return await client._http_client.create(Resource.Workspace, workspace)


async def upload_queue(client: ElisAPIClient, queue: Queue, target: int):
    if target:
        return await client._http_client.update(Resource.Queue, id_=target, data=queue)
    else:
        return await client._http_client.create(Resource.Queue, queue)


async def upload_inbox(client: ElisAPIClient, inbox: Inbox, target: int):
    if target:
        return await client._http_client.update(Resource.Inbox, id_=target, data=inbox)
    else:
        return await client._http_client.create(Resource.Inbox, inbox)


async def upload_schema(client: ElisAPIClient, schema: Schema, target: int):
    if target:
        return await client._http_client.update(
            Resource.Schema, id_=target, data=schema
        )
    else:
        return await client._http_client.create(Resource.Schema, schema)


async def upload_hook(client: ElisAPIClient, hook: Hook, target: int):
    if target:
        return await client._http_client.update(Resource.Hook, id_=target, data=hook)
    else:
        return await client._http_client.create(Resource.Hook, hook)
