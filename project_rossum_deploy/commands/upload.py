import json
import logging
from anyio import Path
import subprocess

import click
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from project_rossum_deploy.commands.download.download import download_organization
from project_rossum_deploy.commands.download.mapping import read_mapping
from project_rossum_deploy.commands.migrate.helpers import is_org_targetting_itself

from project_rossum_deploy.utils.consts import (
    GIT_CHARACTERS,
    PUSH_IGNORED_FIELDS,
    settings,
)
from project_rossum_deploy.utils.functions import coro, detemplatize_name_id


@click.command(
    name=settings.UPLOAD_COMMAND_NAME,
    help="""
Updates local files that were changed into Rossum.
Only source files are taken into account by default.
               """,
)
@click.argument(
    "destination",
    default=settings.SOURCE_DIRNAME,
    type=click.Choice([settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]),
)
@coro
async def upload_project(destination):
    org_path = Path("./")
    mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)

    if destination == settings.SOURCE_DIRNAME or is_org_targetting_itself(mapping):
        client = ElisAPIClient(
            base_url=settings.API_URL,
            token=settings.TOKEN,
            username=settings.USERNAME,
            password=settings.PASSWORD,
        )
    else:
        raise click.ClickException(
            "Cannot use push if target is a different organization. Go to that project and run the command there."
        )

    # Check both the destination dir and and the project root (e.g., organization.json)
    git_destination_diff = subprocess.run(
        ["git", "status", destination, ".", "-s"], capture_output=True, text=True
    )
    changes = git_destination_diff.stdout.split("\n")

    for change in changes:
        change = change.strip()
        if not change:
            continue

        op, path = tuple(change.split(" ", maxsplit=1))
        if path in PUSH_IGNORED_FIELDS:
            continue

        path = path.strip('"')
        match op:
            case GIT_CHARACTERS.CREATED:
                click.echo("Creating new objects is currently not supported, ignoring.")
            case GIT_CHARACTERS.DELETED:
                await delete_object(org_path / path, client)
            case GIT_CHARACTERS.UPDATED:
                await update_object(org_path / path, client)
            case _:
                raise click.ClickException(f'Unrecognized operator "{op}".')

    if is_org_targetting_itself(mapping):
        click.echo(f"Running {settings.DOWNLOAD_COMMAND_NAME} for new target objects.")
        await download_organization()


async def update_object(path: Path, client: ElisAPIClient):
    try:
        object = json.loads(await path.read_text())
        id = object["id"]
        resource = determine_object_type_from_path(path)
        await client._http_client.update(resource, id, object)
        click.echo(f'Successfully updated {resource} with ID "{id}".')
    except Exception as e:
        logging.error(f'Error while updating object with path "{path}": {e}')


async def delete_object(path: Path, client: ElisAPIClient):
    try:
        _, id = detemplatize_name_id(path.stem)
        resource = determine_object_type_from_path(path)
        await client._http_client.delete(resource, id)
        click.echo(f'Successfully deleted {resource} with ID "{id}".')
    except Exception as e:
        logging.error(f'Error while deleting object with path "{path}": {e}')


def determine_object_type_from_path(path: Path) -> Resource:
    split_path = str(path).split("/")
    type = split_path[1] if len(split_path) > 1 else path.stem + "s"
    allowed_types = set(resource.value for resource in Resource)
    if type in allowed_types:
        return Resource(type)
    else:
        raise Exception(f'Unknown resource "{type}".')
