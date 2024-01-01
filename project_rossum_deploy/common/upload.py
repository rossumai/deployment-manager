import logging
from rossum_api import ElisAPIClient
from rossum_api.models import Schema, Hook, Workspace, Queue, Inbox
from rossum_api.api_client import Resource


async def upload_workspace(client: ElisAPIClient, workspace: Workspace, target: int):
    try:
        if target:
            return await client._http_client.update(
                Resource.Workspace, id_=target, data=workspace
            )
        else:
            return await client._http_client.create(Resource.Workspace, workspace)
    except Exception as e:
        logging.error("Error while uploading workspace:")
        logging.exception(e)


async def upload_queue(client: ElisAPIClient, queue: Queue, target: int):
    try:
        if target:
            return await client._http_client.update(
                Resource.Queue, id_=target, data=queue
            )
        else:
            return await client._http_client.create(Resource.Queue, queue)
    except Exception as e:
        logging.error("Error while uploading queue:")
        logging.exception(e)

async def upload_inbox(client: ElisAPIClient, inbox: Inbox, target: int):
    try:
        if target:
            return await client._http_client.update(
                Resource.Inbox, id_=target, data=inbox
            )
        else:
            return await client._http_client.create(Resource.Inbox, inbox)
    except Exception as e:
        logging.error("Error while uploading inbox:")
        logging.exception(e)


async def upload_schema(client: ElisAPIClient, schema: Schema, target: int):
    try:
        if target:
            return await client._http_client.update(
                Resource.Schema, id_=target, data=schema
            )
        else:
            return await client._http_client.create(Resource.Schema, schema)
    except Exception as e:
        logging.error("Error while uploading schema:")
        logging.exception(e)


async def upload_hook(client: ElisAPIClient, hook: Hook, target: int):
    try:
        if target:
            return await client._http_client.update(
                Resource.Hook, id_=target, data=hook
            )
        else:
            return await client._http_client.create(Resource.Hook, hook)
    except Exception as e:
        logging.error("Error while uploading hook:")
        logging.exception(e)
