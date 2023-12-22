import os
import shutil
from anyio import Path
from rossum_api import ElisAPIClient

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
