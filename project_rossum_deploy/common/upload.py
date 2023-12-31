import logging
import os
import shutil
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.models import Schema, Hook, Workspace, Queue, Inbox
from rossum_api.api_client import Resource

import click
from project_rossum_deploy.commands.download.mapping import create_update_mapping

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    templatize_name_id,
    write_json,
)


async def download_organization(client: ElisAPIClient):
    organization = await client.retrieve_own_organization()


async def upload_workspaces(client: ElisAPIClient):
    await client.create_new_workspace()

    # await client._http_client.update()


async def upload_schema(client: ElisAPIClient, schema: Schema, target: int):
    try:    
        if target:
            return await client._http_client.upload(Resource.Schema, schema, target)
        else:
            return await client._http_client.create(Resource.Schema, schema)
    except Exception as e:
        logging.error('Error while uploading schema:')
        logging.exception(e)