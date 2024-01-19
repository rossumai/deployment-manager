import logging
import re
from anyio import Path
import subprocess
from rich import print
from rich.panel import Panel
from rich.progress import track

import click
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from project_rossum_deploy.commands.download.download import (
    download_project,
)

from project_rossum_deploy.utils.consts import (
    GIT_CHARACTERS,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
    detemplatize_name_id,
    read_json,
    merge_hook_changes,
)

GIT_STATUS_REGEX = re.compile(r'(\w+)(\s{1,2})(.*)')

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
async def upload_project_wrapper(destination):
    # To be able to run the command progammatically without the CLI decorators
    await upload_project(destination)


async def upload_project(destination: str, client: ElisAPIClient = None):
    org_path = Path("./")

    if not client:
        match destination:
            case settings.SOURCE_DIRNAME:
                client = ElisAPIClient(
                    base_url=settings.SOURCE_API_URL,
                    token=settings.SOURCE_TOKEN,
                    username=settings.SOURCE_USERNAME,
                    password=settings.SOURCE_PASSWORD,
                )
            case settings.TARGET_DIRNAME:
                client = ElisAPIClient(
                    base_url=settings.TARGET_API_URL,
                    token=settings.TARGET_TOKEN,
                    username=settings.TARGET_USERNAME,
                    password=settings.TARGET_PASSWORD,
                )
            case _:
                raise click.ClickException(
                    f'Unrecognized destination "{destination}" to use {settings.UPLOAD_COMMAND_NAME}.'
                )

    git_destination_diff = subprocess.run(
        ["git", "status", destination, "-s"],
        capture_output=True,
        text=True,
    )
    changes = git_destination_diff.stdout.split("\n")
    changes = await merge_hook_changes(changes, org_path)

    for change in track(changes, description="Pushing changes to Rossum..."):
        if not change:
            continue

        splits = re.findall(GIT_STATUS_REGEX, change)
        if len(splits) != 1:
            continue

        op, is_staged_whitespace, path = splits[0]
        # This is relying on git status semantics
        if len(is_staged_whitespace) != 2:
            continue

        path = path.strip('"')
        match op:
            case GIT_CHARACTERS.CREATED | GIT_CHARACTERS.CREATED_STAGED:
                click.echo("Creating new objects is currently not supported, ignoring.")
            case GIT_CHARACTERS.DELETED:
                await delete_object(org_path / path, client)
            case GIT_CHARACTERS.UPDATED:
                await update_object(client=client, path=org_path / path)
            case _:
                raise click.ClickException(f'Unrecognized operator "{op}".')

    print(
        Panel(
            f"Finished {settings.UPLOAD_COMMAND_NAME}. Please commit the changes before running this command again."
        )
    )
    print(
        Panel(
            f"Running {settings.DOWNLOAD_COMMAND_NAME} for {destination} because of potential changes to names and mapping."
        )
    )

    # Repulling is done to update mapping and (potentially) different filenames.
    await download_project(client=client, org_path=org_path)


async def update_object(client: ElisAPIClient, path: Path = None, object: dict = None):
    try:
        if not object:
            object = await read_json(path)
        id = object["id"]
        resource = determine_object_type_from_url(object["url"])
        result = await client._http_client.update(resource, id, object)
        print(f'Successfully updated {resource} with ID "{id}".')
        return result
    except Exception as e:
        logging.error(f'Error while updating object with path "{path}": {e}')


async def delete_object(path: Path, client: ElisAPIClient):
    try:
        _, id = detemplatize_name_id(path.stem)
        resource = determine_object_type_from_path(path)
        await client._http_client.delete(resource, id)
        print(f'Successfully deleted {resource} with ID "{id}".')
    except Exception as e:
        logging.error(f'Error while deleting object with path "{path}": {e}')


def determine_object_type_from_path(path: Path) -> Resource:
    split_path = str(path).split("/")
    type = split_path[-2] if len(split_path) > 1 else path.stem + "s"
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
