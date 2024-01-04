from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

import click
from project_rossum_deploy.commands.download.helpers import (
    determine_object_destination,
    delete_current_configuration,
    extract_sources_targets,
)
from project_rossum_deploy.commands.download.mapping import (
    create_update_mapping,
    read_mapping,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    extract_id_from_url,
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
    # To be able to run the download command progammatically without the CLI decorators
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

    mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
    previous_sources, previous_targets = extract_sources_targets(mapping)

    workspaces_for_mapping = await download_workspaces(
        client=client,
        org_path=org_path,
        mapping=mapping,
        sources=previous_sources,
        targets=previous_targets,
    )
    schemas_for_mapping = await download_schemas(
        client=client,
        org_path=org_path,
        mapping=mapping,
        sources=previous_sources,
        targets=previous_targets,
    )
    hooks_for_mapping = await download_hooks(
        client=client,
        org_path=org_path,
        mapping=mapping,
        sources=previous_sources,
        targets=previous_targets,
    )

    await create_update_mapping(
        org_path=org_path,
        organization=organization,
        workspaces_for_mapping=workspaces_for_mapping,
        schemas_for_mapping=schemas_for_mapping,
        hooks_for_mapping=hooks_for_mapping,
        old_mapping=mapping,
    )


async def download_workspaces(
    client: ElisAPIClient, org_path: Path, mapping: dict, sources: dict, targets: dict
):
    workspaces = []

    async for workspace in client.list_all_workspaces():
        workspace = await client.retrieve_workspace(workspace.id)
        destination = await determine_object_destination(
            object=workspace,
            object_type="workspace",
            org_path=org_path,
            mapping=mapping,
            sources=sources,
            targets=targets,
        )
        workspace_config_path = (
            org_path
            / destination
            / "workspaces"
            / templatize_name_id(workspace.name, workspace.id)
            / "workspace.json"
        )

        await write_json(workspace_config_path, workspace)

        workspace.queues = await download_queues_for_workspace(
            client, workspace_config_path.parent, workspace.id
        )
        workspaces.append((destination, workspace))

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


# Only schemas actually need to be retrieved individually (since when listing them using GET /schemas, their contents are missing)
async def download_schemas(
    client: ElisAPIClient, org_path: Path, mapping: dict, sources: dict, targets: dict
):
    schemas = []
    async for schema in client.list_all_schemas():
        schema = await client.retrieve_schema(schema.id)
        destination = await determine_object_destination(
            object=schema,
            object_type="schema",
            org_path=org_path,
            mapping=mapping,
            sources=sources,
            targets=targets,
        )
        schema_config_path = (
            org_path
            / destination
            / "schemas"
            / f"{templatize_name_id(schema.name, schema.id)}.json"
        )
        await write_json(schema_config_path, schema)
        schemas.append((destination, schema))

    return schemas


async def download_hooks(
    client: ElisAPIClient, org_path: Path, mapping: dict, sources: dict, targets: dict
):
    hooks = []
    async for hook in client.list_all_hooks():
        hook = await client.retrieve_hook(hook.id)
        destination = await determine_object_destination(
            object=hook,
            object_type="hook",
            org_path=org_path,
            mapping=mapping,
            sources=sources,
            targets=targets,
        )
        hook_config_path = (
            org_path
            / destination
            / 'hooks'
            / f"{templatize_name_id(hook.name, hook.id)}.json"
        )
        await write_json(hook_config_path, hook)
        hooks.append((destination, hook))

    return hooks
