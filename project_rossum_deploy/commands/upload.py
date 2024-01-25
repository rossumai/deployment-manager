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
from project_rossum_deploy.commands.download.mapping import read_mapping
from project_rossum_deploy.common.attribute_override import find_mapping_section

from project_rossum_deploy.utils.consts import (
    GIT_CHARACTERS,
    settings,
)
from project_rossum_deploy.utils.functions import coro, detemplatize_name_id, read_json, merge_hook_changes, evaluate_delete_dependencies, evaluate_create_dependencies, write_json

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
    changes_raw = git_destination_diff.stdout.split("\n")
    changes = []
    for change in changes_raw:
        change = change.strip()
        if not change:
            continue
        op, path = tuple(change.split(" ", maxsplit=1))
        path = Path(path.strip().strip('"'))
        changes.append((op,path))
        
    if changes:
        print ("1" + str(changes))
        changes = await merge_hook_changes(changes, org_path)
        print ("2" + str(changes))
        changes = await evaluate_delete_dependencies(changes, org_path)
        print ("3" + str(changes))
        changes = await evaluate_create_dependencies(changes, org_path, client)
        print ("4" + str(changes))

    
    for change in track(changes, description="Pushing changes to Rossum..."):
        op, path = change
        match op:
            case GIT_CHARACTERS.CREATED:
                await create_object(org_path / path, client)
            case GIT_CHARACTERS.CREATED_STAGED:
                await create_object(org_path / path, client)
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
    await download_project(
        client=client, org_path=org_path
    )


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


async def create_object(path: Path, client: ElisAPIClient):
    try:
        object = await read_json(path)
        object["id"] = None
        resource = determine_object_type_from_path(path)
        created_object = await client._http_client.create(resource, object)
        await write_json(path, created_object)
        print(f'Successfully create {resource} with ID "{created_object["id"]}".')
    except Exception as e:
        logging.error(f'Error while creating object with path "{path}": {e}')


async def delete_object(path: Path, client: ElisAPIClient):
    try:
        _, id = detemplatize_name_id(path)
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
