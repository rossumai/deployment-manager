import os
import shutil
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

import click
from project_rossum_deploy.commands.download.mapping import (
    create_empty_mapping,
    create_update_mapping,
    extract_targets,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    extract_id_from_url,
    read_yaml,
    templatize_name_id,
    write_json,
)


@click.command(
    name=settings.DOWNLOAD_COMMAND_NAME,
    help="""
Downloads all Rossum objects from the user's default (first) organization.
Creates a local organization directory structure with the configs of these objects.
In case the directory already exists, it first deletes its contents and then downloads them anew.
               """,
)
@coro
async def download_organization_wrapper():
    # To be able to run the download progammatically without the CLI decorators
    await download_organization()

async def download_organization():
    client = ElisAPIClient(
        base_url=settings.API_URL,
        username=settings.USERNAME,
        password=settings.PASSWORD,
    )

    organization = await client.retrieve_own_organization()

    org_path = Path("./")
    org_config_path = org_path / "organization.json"
    if await org_config_path.exists() and click.confirm(
        f'Project "{(await org_path.absolute()).name}" already has configuration files in it, do you want to replace it with the new configuration?',
        abort=True,
    ):
        await delete_current_configuration(org_path)

    await write_json(org_config_path, organization)

    mapping_path = org_path / settings.MAPPING_FILENAME
    mapping = (
        read_yaml(mapping_path)
        if await mapping_path.exists()
        else create_empty_mapping()
    )
    previous_targets = extract_targets(mapping)

    workspaces_for_mapping = await download_workspaces(client, org_path, previous_targets)
    schemas_for_mapping = await download_schemas(client, org_path, previous_targets)
    hooks_for_mapping = await download_hooks(client, org_path, previous_targets)

    await create_update_mapping(
        org_path=org_path,
        organization=organization,
        workspaces_for_mapping=workspaces_for_mapping,
        schemas_for_mapping=schemas_for_mapping,
        hooks_for_mapping=hooks_for_mapping,
        previous_targets=previous_targets,
    )


async def delete_current_configuration(org_path: Path):
    # We do not delete mapping.yaml on purposes
    os.remove(org_path / "organization.json")
    spaces = [settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]
    paths_to_delete = ["workspaces", "schemas", "hooks"]
    for space in spaces:
        space_path = org_path / space
        if await space_path.exists():
            for path in paths_to_delete:
                path = space_path / path
                if await path.exists():
                    shutil.rmtree(path)


async def download_workspaces(client: ElisAPIClient, parent_dir: Path, targets: dict):
    # workspaces = [ws async for ws in client.list_all_workspaces()]
    workspaces = []

    async for workspace in client.list_all_workspaces():
        workspace = await client.retrieve_workspace(workspace.id)
        workspace_config_path = (
            parent_dir
            / (
                settings.TARGET_DIRNAME
                if workspace.id in targets["workspaces"]
                else settings.SOURCE_DIRNAME
            )
            / "workspaces"
            / templatize_name_id(workspace.name, workspace.id)
            / "workspace.json"
        )

        await write_json(workspace_config_path, workspace)

        workspace.queues = await download_queues_for_workspace(
            client, workspace_config_path.parent, workspace.id
        )
        workspaces.append(workspace)

    return workspaces


async def download_queues_for_workspace(
    client: ElisAPIClient, parent_dir: Path, workspace_id: int
):
    queues = []
    async for queue in client.list_all_queues(workspace=workspace_id):
        queue = await client.retrieve_queue(queue.id)
        queue_path = (
            parent_dir / "queues" / f"{templatize_name_id(queue.name, queue.id)}"
        )
        await write_json(queue_path / "queue.json", queue)

        inbox_id = extract_id_from_url(queue.inbox)
        if inbox_id:
            queue.inbox = await download_inbox(client, queue_path, inbox_id)
        queues.append(queue)

    return queues


async def download_inbox(client: ElisAPIClient, parent_dir: Path, inbox_id: int):
    inbox = await client._http_client.fetch_one(Resource.Inbox, inbox_id)
    inbox = client._deserializer(Resource.Inbox, inbox)
    await write_json(parent_dir / "inbox.json", inbox)
    return inbox


# Only schemas actually need to be retrieved individually (since when only listing them, their contents are missing)
async def download_schemas(client: ElisAPIClient, parent_dir: Path, targets: dict):
    schemas = []
    async for schema in client.list_all_schemas():
        schema = await client.retrieve_schema(schema.id)
        schema_config_path = (
            parent_dir
            / (
                settings.TARGET_DIRNAME
                if schema.id in targets["schemas"]
                else settings.SOURCE_DIRNAME
            )
            / "schemas"
            / f"{templatize_name_id(schema.name, schema.id)}.json"
        )
        await write_json(schema_config_path, schema)
        schemas.append(schema)

    return schemas


async def download_hooks(client: ElisAPIClient, parent_dir: Path, targets: dict):
    hooks = []
    async for hook in client.list_all_hooks():
        hook = await client.retrieve_hook(hook.id)
        hook_config_path = (
            parent_dir
            / (
                settings.TARGET_DIRNAME
                if hook.id in targets["hooks"]
                else settings.SOURCE_DIRNAME
            )
            / "hooks"
            / f"{templatize_name_id(hook.name, hook.id)}.json"
        )
        await write_json(hook_config_path, hook)
        hooks.append(hook)

    return hooks
