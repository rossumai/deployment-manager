import asyncio
import functools
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from rich import print
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress

import click
from project_rossum_deploy.commands.download.helpers import (
    determine_object_destination,
    delete_current_configuration,
)
from project_rossum_deploy.commands.download.mapping import (
    create_empty_mapping,
    create_update_mapping,
    read_mapping,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    extract_id_from_url,
    extract_sources_targets,
    retrieve_with_progress,
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
    # To be able to run the command progammatically without the CLI decorators
    await download_organization()


async def download_organization(client: ElisAPIClient = None, org_path: Path = None):
    if not client:
        client = ElisAPIClient(
            base_url=settings.API_URL,
            token=settings.TOKEN,
            username=settings.USERNAME,
            password=settings.PASSWORD,
        )

    organizations = [org async for org in client.list_all_organizations()]
    if not len(organizations):
        raise click.ClickException("No organization found.")
    organization = await client.retrieve_organization(organizations[0].id)

    if not org_path:
        org_path = Path("./")

    org_config_path = org_path / "organization.json"
    if await org_config_path.exists():
        if not Confirm.ask(
            f'Project "{(await org_path.absolute()).name}" already has configuration files in it, do you want to replace it with the new configuration?',
        ):
            return
        await delete_current_configuration(org_path)

    await write_json(org_config_path, organization)

    mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
    if not mapping:
        mapping = create_empty_mapping()
    previous_sources, previous_targets = extract_sources_targets(mapping)

    with Progress() as progress:
        (
            workspaces_for_mapping,
            schemas_for_mapping,
            hooks_for_mapping,
        ) = await asyncio.gather(
            *[
                download_workspaces(
                    client=client,
                    org_path=org_path,
                    mapping=mapping,
                    sources=previous_sources,
                    targets=previous_targets,
                    progress=progress,
                ),
                download_schemas(
                    client=client,
                    org_path=org_path,
                    mapping=mapping,
                    sources=previous_sources,
                    targets=previous_targets,
                    progress=progress,
                ),
                download_hooks(
                    client=client,
                    org_path=org_path,
                    mapping=mapping,
                    sources=previous_sources,
                    targets=previous_targets,
                    progress=progress,
                ),
            ]
        )

    await create_update_mapping(
        org_path=org_path,
        organization=organization,
        workspaces_for_mapping=workspaces_for_mapping,
        schemas_for_mapping=schemas_for_mapping,
        hooks_for_mapping=hooks_for_mapping,
        old_mapping=mapping,
    )

    print(Panel(f"Finished {settings.DOWNLOAD_COMMAND_NAME}."))


async def download_workspaces(
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict,
    sources: dict,
    targets: dict,
    progress: Progress,
):
    workspaces = []

    paginated_workspaces = [
        workspace async for workspace in client.list_all_workspaces()
    ]
    # Progress is split between downloading the workspace itself and downloading its queues
    task = progress.add_task(
        "Downloading workspaces and queues...", total=2 * len(paginated_workspaces)
    )

    # Refetch in case the paginated fields don't include everything
    full_workspaces = await asyncio.gather(
        *[
            retrieve_with_progress(
                functools.partial(client.retrieve_workspace, ws.id), progress, task
            )
            for ws in paginated_workspaces
        ]
    )

    for workspace in full_workspaces:
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
        progress.update(task, advance=1)

    return workspaces


async def download_queues_for_workspace(
    client: ElisAPIClient, parent_dir: Path, workspace_id: int
):
    queues = []

    paginated_queues = [q async for q in client.list_all_queues(workspace=workspace_id)]
    # Refetch in case the paginated fields don't include everything
    full_queues = await asyncio.gather(
        *[client.retrieve_queue(q.id) for q in paginated_queues]
    )

    for queue in full_queues:
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


async def download_schemas(
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict,
    sources: dict,
    targets: dict,
    progress: Progress,
):
    schemas = []

    paginated_schemas = [schema async for schema in client.list_all_schemas()]
    task = progress.add_task("Downloading schemas...", total=len(paginated_schemas))

    # Refetch because schema fields are not fully listed
    full_schemas = await asyncio.gather(
        *[
            retrieve_with_progress(
                functools.partial(client.retrieve_schema, schema.id), progress, task
            )
            for schema in paginated_schemas
        ]
    )

    for schema in full_schemas:
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
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict,
    sources: dict,
    targets: dict,
    progress: Progress,
):
    hooks = []

    paginated_hooks = [hook async for hook in client.list_all_hooks()]
    task = progress.add_task("Downloading hooks...", total=len(paginated_hooks))

    full_hooks = await asyncio.gather(
        *[
            retrieve_with_progress(
                functools.partial(client.retrieve_hook, hook.id), progress, task
            )
            for hook in paginated_hooks
        ]
    )

    for hook in full_hooks:
        # Refetch in case the paginated fields don't include everything
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
            / "hooks"
            / f"{templatize_name_id(hook.name, hook.id)}.json"
        )
        await write_json(hook_config_path, hook)
        hooks.append((destination, hook))

    return hooks
