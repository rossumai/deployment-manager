from rossum_api import ElisAPIClient
import click

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import coro


@click.command(
    name="download",
    help="""
Downloads all Rossum objects from the user's default (first) organization.
Creates a local directory structure with the configs of these objects.
If such a directory already exists, it gets overwritten.
               """,
)
@coro
async def download_project():
    client = ElisAPIClient(
        base_url=settings.API_URL,
        username=settings.USERNAME,
        password=settings.PASSWORD,
    )

    organization = await client.retrieve_own_organization()

    # TODO: migrate organization metadata (like features) and ui settings?

