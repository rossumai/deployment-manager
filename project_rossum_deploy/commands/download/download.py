import os
import shutil
from anyio import Path
from rossum_api import ElisAPIClient

import click
from project_rossum_deploy.commands.download.mapping import (
    create_empty_mapping,
    create_update_mapping,
    extract_targets,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    read_yaml,
    templatize_name_id,
    write_json,
)


@click.command(
    name="download",
    help="""
Downloads all Rossum objects from the user's default (first) organization.
Creates a local organization directory structure with the configs of these objects.
In case the directory already exists, it first deletes its contents and then downloads them anew.
               """,
)
@coro
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

    workspace_mappings = await download_workspaces(client, org_path, previous_targets)
    schema_mappings = await download_schemas(client, org_path, previous_targets)
    hook_mappings = await download_hooks(client, org_path, previous_targets)

    await create_update_mapping(
        org_path=org_path,
        organization=organization,
        workspace_mappings=workspace_mappings,
        schema_mappings=schema_mappings,
        hook_mappings=hook_mappings,
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
    workspaces = [ws async for ws in client.list_all_workspaces()]

    for workspace in workspaces:
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
            client, workspace_config_path.parent
        )

    return workspaces


async def download_queues_for_workspace(client: ElisAPIClient, parent_dir: Path):
    queues = [queue async for queue in client.list_all_queues()]
    for queue in queues:
        queue_config_path = (
            parent_dir / "queues" / f"{templatize_name_id(queue.name, queue.id)}.json"
        )
        await write_json(queue_config_path, queue)

    return queues


async def download_schemas(client: ElisAPIClient, parent_dir: Path, targets: dict):
    schemas = [schema async for schema in client.list_all_schemas()]
    async for schema in client.list_all_schemas():
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

    return schemas


async def download_hooks(client: ElisAPIClient, parent_dir: Path, targets: dict):
    hooks = [hook async for hook in client.list_all_hooks()]
    async for hook in client.list_all_hooks():
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

    return hooks
