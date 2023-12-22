import os
import shutil
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.models import Organization, Workspace, Hook, Schema, Queue
import click

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    templatize_name_id,
    write_json,
    write_yaml,
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
        delete_current_configuration(org_path)

    await write_json(org_config_path, organization)

    workspace_mappings = await download_workspaces(client, org_path)
    schema_mappings = await download_schemas(client, org_path)
    hook_mappings = await download_hooks(client, org_path)

    await create_update_mapping(
        org_path=org_path,
        organization=organization,
        workspace_mappings=workspace_mappings,
        schema_mappings=schema_mappings,
        hook_mappings=hook_mappings,
    )


async def create_update_mapping(
    org_path: Path,
    organization: Organization,
    workspace_mappings: list[Workspace],
    hook_mappings: list[Hook],
    schema_mappings: list[Schema],
):
    mapping = {
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "target": "",
            "workspaces": [],
            "hooks": [get_attributes_for_mapping(h) for h in hook_mappings],
            "schemas": [get_attributes_for_mapping(s) for s in schema_mappings],
        }
    }

    for workspace in workspace_mappings:
        ws_mapping = {
            **get_attributes_for_mapping(workspace),
            "queues": [get_attributes_for_mapping(q) for q in workspace.queues],
        }
        mapping["organization"]["workspaces"].append(ws_mapping)

    await write_yaml(org_path / settings.MAPPING_FILENAME, mapping)


def get_attributes_for_mapping(object: Organization | Queue | Hook | Schema):
    return {"id": object.id, "name": object.name, "target": ""}


def delete_current_configuration(org_path: Path):
    os.remove(org_path / "organization.json")
    paths_to_delete = ["workspaces", "schemas", "hooks"]
    for path in paths_to_delete:
        shutil.rmtree(org_path / path)


async def download_workspaces(client: ElisAPIClient, parent_dir: Path):
    workspaces = [ws async for ws in client.list_all_workspaces()]
    for workspace in workspaces:
        workspace_config_path = (
            parent_dir
            / "workspaces"
            / templatize_name_id(workspace.name, workspace.id)
            / "workspace.json"
        )

        await write_json(workspace_config_path, workspace)

        workspace.queues = await download_queues_for_workspace(
            client, workspace.id, workspace_config_path.parent
        )

    return workspaces


async def download_queues_for_workspace(
    client: ElisAPIClient, workspace_id: str, parent_dir: Path
):
    queues = [queue async for queue in client.list_all_queues()]
    for queue in queues:
        queue_config_path = (
            parent_dir / "queues" / f"{templatize_name_id(queue.name, queue.id)}.json"
        )
        await write_json(queue_config_path, queue)

    return queues


async def download_schemas(client: ElisAPIClient, parent_dir: Path):
    schemas = [schema async for schema in client.list_all_schemas()]
    async for schema in client.list_all_schemas():
        schema_config_path = (
            parent_dir
            / "schemas"
            / f"{templatize_name_id(schema.name, schema.id)}.json"
        )
        await write_json(schema_config_path, schema)

    return schemas


async def download_hooks(client: ElisAPIClient, parent_dir: Path):
    hooks = [hook async for hook in client.list_all_hooks()]
    async for hook in client.list_all_hooks():
        hook_config_path = (
            parent_dir / "hooks" / f"{templatize_name_id(hook.name, hook.id)}.json"
        )
        await write_json(hook_config_path, hook)

    return hooks
