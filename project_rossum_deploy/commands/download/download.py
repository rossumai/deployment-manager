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
    create_formula_file,
    determine_object_destination,
    delete_current_configuration,
    find_formula_fields_in_schema,
)
from project_rossum_deploy.commands.download.mapping import (
    create_empty_mapping,
    create_update_mapping,
    read_mapping,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    display_error,
    extract_id_from_url,
    extract_sources_targets,
    retrieve_with_progress,
    templatize_name_id,
    write_json,
    write_str,
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
async def download_project_wrapper():
    # To be able to run the command progammatically without the CLI decorators
    await download_project()


async def download_project(client: ElisAPIClient = None, org_path: Path = None):
    try:
        if settings.IS_PROJECT_IN_SAME_ORG:
            return await download_organization_combined(client, org_path)

        if not org_path:
            org_path = Path("./")

        if len([path async for path in org_path.iterdir()]):
            if not Confirm.ask(
                f'Project "{(await (org_path).absolute()).name}" already has configuration files in it, do you want to replace it with the new configuration (both source and target)?',
            ):
                return
            await delete_current_configuration(org_path)

        mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
        if not mapping:
            mapping = create_empty_mapping()

        source_client = ElisAPIClient(
            base_url=settings.SOURCE_API_URL,
            token=settings.SOURCE_TOKEN,
            username=settings.SOURCE_USERNAME,
            password=settings.SOURCE_PASSWORD,
        )
        (
            source_organization,
            source_workspaces,
            source_schemas,
            source_hooks,
        ) = await download_organization_single(
            client=source_client,
            org_path=org_path,
            destination=settings.SOURCE_DIRNAME,
        )

        target_client = ElisAPIClient(
            base_url=settings.TARGET_API_URL,
            token=settings.TARGET_TOKEN,
            username=settings.TARGET_USERNAME,
            password=settings.TARGET_PASSWORD,
        )
        (
            _,
            target_workspaces,
            target_schemas,
            target_hooks,
        ) = await download_organization_single(
            client=target_client,
            org_path=org_path,
            destination=settings.TARGET_DIRNAME,
        )

        await create_update_mapping(
            org_path=org_path,
            organization=source_organization,
            workspaces_for_mapping=[*source_workspaces, *target_workspaces],
            schemas_for_mapping=[*source_schemas, *target_schemas],
            hooks_for_mapping=[*source_hooks, *target_hooks],
            old_mapping=mapping,
        )
    except Exception as e:
        display_error(f"Error during project {settings.DOWNLOAD_COMMAND_NAME}: {e}", e)


async def download_organization_single(
    client: ElisAPIClient, org_path: Path, destination: str
):
    organizations = [org async for org in client.list_all_organizations()]
    if not len(organizations):
        raise click.ClickException("No organization found.")
    organization = await client._http_client.fetch_one(
        Resource.Organization, organizations[0].id
    )

    org_config_path = org_path / destination / "organization.json"
    await write_json(org_config_path, organization, "organization")

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
                    destination=destination,
                    progress=progress,
                ),
                download_schemas(
                    client=client,
                    org_path=org_path,
                    destination=destination,
                    progress=progress,
                ),
                download_hooks(
                    client=client,
                    org_path=org_path,
                    destination=destination,
                    progress=progress,
                ),
            ]
        )

    print(Panel(f"Finished {settings.DOWNLOAD_COMMAND_NAME} for {destination}."))
    return organization, workspaces_for_mapping, schemas_for_mapping, hooks_for_mapping


async def download_workspaces(
    client: ElisAPIClient,
    org_path: Path,
    progress: Progress,
    mapping: dict = {},
    destination: str = "",
    sources: dict = {},
    targets: dict = {},
):
    workspaces = []

    paginated_workspaces = [
        workspace async for workspace in client.list_all_workspaces()
    ]
    # Progress is split between downloading the workspace itself and downloading its queues
    task = progress.add_task(
        f"Downloading {destination} workspaces and queues...",
        total=2 * len(paginated_workspaces),
    )

    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_workspaces = await asyncio.gather(
        *[
            retrieve_with_progress(
                functools.partial(
                    client._http_client.fetch_one, Resource.Workspace, ws.id
                ),
                progress,
                task,
            )
            for ws in paginated_workspaces
        ]
    )

    for workspace in full_workspaces:
        destination_local = (
            destination
            if destination
            else await determine_object_destination(
                object=workspace,
                object_type="workspace",
                org_path=org_path,
                mapping=mapping,
                sources=sources,
                targets=targets,
            )
        )

        workspace_config_path = (
            org_path
            / destination_local
            / "workspaces"
            / templatize_name_id(workspace["name"], workspace["id"])
            / "workspace.json"
        )

        await write_json(workspace_config_path, workspace, "workspace")

        workspace["queues"] = await download_queues_for_workspace(
            client, workspace_config_path.parent, workspace["id"]
        )
        workspaces.append((destination_local, workspace))
        progress.update(task, advance=1)

    return workspaces


async def download_queues_for_workspace(
    client: ElisAPIClient, parent_dir: Path, workspace_id: int
):
    queues = []

    paginated_queues = [q async for q in client.list_all_queues(workspace=workspace_id)]
    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_queues = await asyncio.gather(
        *[client._http_client.fetch_one(Resource.Queue, q.id) for q in paginated_queues]
    )

    for queue in full_queues:
        queue_path = (
            parent_dir / "queues" / f"{templatize_name_id(queue['name'], queue['id'])}"
        )
        await write_json(queue_path / "queue.json", queue, "queue")

        inbox_id = extract_id_from_url(queue["inbox"])
        if inbox_id:
            queue["inbox"] = await download_inbox(client, queue_path, inbox_id)
        queues.append(queue)

    return queues


async def download_inbox(client: ElisAPIClient, parent_dir: Path, inbox_id: int):
    inbox = await client._http_client.fetch_one(Resource.Inbox, inbox_id)
    await write_json(parent_dir / "inbox.json", inbox, "inbox")
    return inbox


async def download_schemas(
    client: ElisAPIClient,
    org_path: Path,
    progress: Progress,
    mapping: dict = {},
    destination: str = "",
    sources: dict = {},
    targets: dict = {},
):
    schemas = []

    paginated_schemas = [schema async for schema in client.list_all_schemas()]
    task = progress.add_task(
        f"Downloading {destination} schemas...", total=len(paginated_schemas)
    )

    # Refetch because schema fields are not fully listed
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_schemas = await asyncio.gather(
        *[
            retrieve_with_progress(
                functools.partial(
                    client._http_client.fetch_one, Resource.Schema, schema.id
                ),
                progress,
                task,
            )
            for schema in paginated_schemas
        ]
    )

    for schema in full_schemas:
        destination_local = (
            destination
            if destination
            else await determine_object_destination(
                object=schema,
                object_type="schema",
                org_path=org_path,
                mapping=mapping,
                sources=sources,
                targets=targets,
            )
        )
        schema_config_path = (
            org_path
            / destination_local
            / "schemas"
            / f"{templatize_name_id(schema['name'], schema['id'])}.json"
        )
        await write_json(schema_config_path, schema, "schema")
        schemas.append((destination_local, schema))

        formula_fields = find_formula_fields_in_schema(schema["content"])
        if formula_fields:
            formula_directory_path = (
                schema_config_path.parent
                / f"{settings.FORMULA_DIR_PREFIX}{templatize_name_id(schema['name'], schema['id'])}"
            )
            for field_id, code in formula_fields:
                await create_formula_file(
                    formula_directory_path / f"{field_id}.py", code
                )

    return schemas


async def download_hooks(
    client: ElisAPIClient,
    org_path: Path,
    progress: Progress,
    mapping: dict = {},
    destination: str = "",
    sources: dict = {},
    targets: dict = {},
):
    hooks = []

    paginated_hooks = [hook async for hook in client.list_all_hooks()]
    task = progress.add_task(
        f"Downloading {destination} hooks...", total=len(paginated_hooks)
    )

    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_hooks = await asyncio.gather(
        *[
            retrieve_with_progress(
                functools.partial(
                    client._http_client.fetch_one, Resource.Hook, hook.id
                ),
                progress,
                task,
            )
            for hook in paginated_hooks
        ]
    )

    for hook in full_hooks:
        destination_local = (
            destination
            if destination
            else await determine_object_destination(
                object=hook,
                object_type="hook",
                org_path=org_path,
                mapping=mapping,
                sources=sources,
                targets=targets,
            )
        )
        hook_config_path = (
            org_path
            / destination_local
            / "hooks"
            / f"{templatize_name_id(hook['name'], hook['id'])}.json"
        )

        await write_json(hook_config_path, hook, "hook")
        hooks.append((destination_local, hook))

        if hook["extension_source"] != "rossum_store":
            if hook_code := hook.get("config", {}).get("code", None):
                hook_runtime = hook["config"].get("runtime")
                extension = ".py" if "python" in hook_runtime else ".js"
                hook_code_path = hook_config_path.with_suffix(extension)
                await write_str(hook_code_path, hook_code)

    return hooks


# TODO: might be obsolete even for interorg
async def download_organization_combined(
    client: ElisAPIClient = None, org_path: Path = None
):
    try:
        if not client:
            client = ElisAPIClient(
                base_url=settings.SOURCE_API_URL,
                token=settings.SOURCE_TOKEN,
                username=settings.SOURCE_USERNAME,
                password=settings.SOURCE_PASSWORD,
            )

        organizations = [org async for org in client.list_all_organizations()]
        if not len(organizations):
            raise click.ClickException("No organization found.")
        organization = await client._http_client.fetch_one(
            Resource.Organization, organizations[0].id
        )

        if not org_path:
            org_path = Path("./")

        org_config_path = org_path / settings.SOURCE_DIRNAME / "organization.json"
        if await org_config_path.exists():
            if not Confirm.ask(
                f'Project "{(await org_path.absolute()).name}" already has configuration files in it, do you want to replace it with the new configuration?',
            ):
                return
            await delete_current_configuration(org_path)

        await write_json(org_config_path, organization, "organization")

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

    except Exception as e:
        display_error(f"Error during project {settings.DOWNLOAD_COMMAND_NAME}: {e}", e)
