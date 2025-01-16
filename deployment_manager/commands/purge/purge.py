import asyncio
from anyio import Path

import questionary
from rich import print as pprint
from rich.panel import Panel
import click
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource

# from project_rossum_deploy.commands.download.download import download_project
from deployment_manager.commands.deploy.common.helpers import (
    get_api_url_from_user,
    get_token_from_user,
    validate_credentials,
)
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from deployment_manager.commands.download.downloader import Downloader
from deployment_manager.utils.consts import (
    display_error,
    display_info,
    display_warning,
    settings,
)
from deployment_manager.utils.functions import (
    coro,
    extract_id_from_url,
)

ALL_OBJECT_TYPES = [
    Resource.Schema.value,
    Resource.Hook.value,
    Resource.Workspace.value,
    Resource.Queue.value,
]

PURGE_OBJECT_TYPES = [
    *ALL_OBJECT_TYPES,
    settings.ALL_OBJECTS,
    settings.UNUSED_SCHEMAS,
]

# Click can only work with strings, not enum objects, but RossumAPIClient expects the enums
OBJECT_TYPE_MAPPING = {
    Resource.Schema.value: Resource.Schema,
    Resource.Hook.value: Resource.Hook,
    Resource.Workspace.value: Resource.Workspace,
    Resource.Queue.value: Resource.Queue,
}

# Queues should be deleted before (used) schemas and workspaces
OBJECT_PRIORITIES = {
    Resource.Queue.value: 0,
    Resource.Schema.value: 1,
    Resource.Workspace.value: 2,
    Resource.Hook.value: 3,
}


@click.command(
    name=settings.PURGE_COMMAND_NAME,
    help="""
Deletes all objects in Rossum based on IDs in the mappping file. This operation is destructive and cannot be undone.""",
)
@click.argument(
    "object_types",
    nargs=-1,
    type=click.Choice(
        choices=PURGE_OBJECT_TYPES,
    ),
)
@coro
async def purge_object_types_wrapper(object_types):
    # To be able to run the command progammatically without the CLI decorators
    await purge_object_types(
        object_types=object_types,
    )


async def purge_object_types(
    object_types: list[str], client: ElisAPIClient = None, project_path: Path = None
):
    try:
        if not object_types:
            display_warning(
                f"No object types specified to {settings.PURGE_COMMAND_NAME}."
            )
            return

        if not project_path:
            project_path = Path("./")

        if not client:
            api_url = await get_api_url_from_user()
            token = await get_token_from_user()
            credentials = Credentials(token=token, url=api_url)
            await validate_credentials(credentials)
            client = ElisAPIClient(base_url=api_url, token=token)

        downloader = Downloader(client=client)
        object_types_ids: list[tuple[Resource, int]] = []

        if settings.ALL_OBJECTS in object_types:
            object_types = ALL_OBJECT_TYPES

        object_types = sorted(
            object_types, key=lambda x: OBJECT_PRIORITIES.get(x, float("inf"))
        )

        for object_type in object_types:
            if object_type == settings.UNUSED_SCHEMAS:
                object_types_ids.extend(
                    [
                        (Resource.Schema, id)
                        for id in await find_unused_schema_ids(client=client)
                    ]
                )
            else:
                object_type_as_enum = OBJECT_TYPE_MAPPING.get(object_type)
                object_types_ids.extend(
                    [
                        (object_type_as_enum, id)
                        for id in await downloader.download_remote_object_ids(
                            type=object_type_as_enum
                        )
                    ]
                )

        target_org_choices = []
        async for org in client.list_all_organizations():
            target_org_choices.append(questionary.Choice(title=org.name, value=org))
        if len(target_org_choices) > 1:
            target_org = await questionary.select(
                "Select target organization:", choices=target_org_choices
            ).ask_async()
        else:
            target_org = target_org_choices[0].value

        pprint(
            Panel(
                f"Running {settings.PURGE_COMMAND_NAME} in [green]{target_org.name}[/green] ([purple]{target_org.id}[/purple])"
            )
        )

        if not await questionary.confirm(
            f"Are you sure you want to delete {object_types} in the above organization? This operation cannot be undone.",
            default=False,
        ).ask_async():
            return

        for type, object_id in object_types_ids:
            try:
                # Queues have a "cooldown" period for deletion which needs to be overriden
                if type == Resource.Queue:
                    (
                        await client._http_client._request(
                            "DELETE",
                            f"queues/{object_id}",
                            params={"delete_after": "0"},
                        ),
                    )
                else:
                    if type == Resource.Schema:
                        schema = await client.retrieve_schema(object_id)
                        queues = extract_id_from_url(schema.queues)
                        if not queues:
                            queues = []

                        queue_deleted_count = 0
                        while queue_deleted_count != len(queues):
                            for queue in queues:
                                queue_id = extract_id_from_url(queue)
                                try:
                                    await client.retrieve_queue(queue_id)
                                except APIClientError as e:
                                    if e.status_code == 404:
                                        queue_deleted_count += 1

                            if queue_deleted_count == len(queues):
                                break
                            # Deleting queues (even when providing 'delete_after': 0) is asynchronous, wait for a short while
                            display_info(
                                "Waiting for queues to be deleted in the API..."
                            )
                            await asyncio.sleep(5)

                    await client._http_client.delete(resource=type, id_=object_id)

                pprint(
                    f"Deleted [yellow]{type.value}[/yellow] [purple]{object_id}[/purple]"
                )
            except Exception as e:
                if isinstance(e, APIClientError) and e.status_code == 404:
                    display_warning(
                        f"{type} [purple]{object_id}[/purple] already does not exist on remote."
                    )
                display_error(f"Error while deleting {type.value} {object_id}: {e}")

        pprint(Panel(f"{settings.PURGE_COMMAND_NAME} finished."))

    except Exception as e:
        display_error(f"Error during project {settings.UPLOAD_COMMAND_NAME}: {e}", e)


async def find_unused_schema_ids(client: ElisAPIClient):
    schema_ids = []
    async for schema in client.list_all_schemas():
        if not len(schema.queues):
            schema_ids.append(schema.id)
    return schema_ids


def display_objects_to_be_deleted(object_types_ids: list[tuple[Resource, str]]):
    for type, id in object_types_ids:
        pprint(f"[yellow]{type.value}[/yellow] {id}")
