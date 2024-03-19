import asyncio
import subprocess
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from rich import print
from rich.panel import Panel

import click
from project_rossum_deploy.commands.download.helpers import (
    create_formula_file,
    determine_object_destination,
    find_formula_fields_in_schema,
    should_write_object,
)
from project_rossum_deploy.commands.download.mapping import (
    create_empty_mapping,
    create_update_mapping,
    read_mapping,
)

from project_rossum_deploy.common.git import get_changed_file_paths
from project_rossum_deploy.commands.migrate_mapping import migrate_mapping
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    display_error,
    extract_id_from_url,
    extract_sources_targets,
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
@click.option(
    "-c",
    default=False,
    is_flag=True,
    help="Commits the pulled changes automatically.",
)
@click.option(
    "--all",
    default=False,
    is_flag=True,
    help="Downloads all remote files and overwrites the local ones.",
)
@click.option(
    "-m",
    default="Sync changes",
    help="Commit message for pulling.",
)
@coro
# To be able to run the command progammatically without the CLI decorators
async def download_project_wrapper(c: bool = False, m: str = "", all: bool = False):
    await download_project(commit_message=m, commit=c, download_all=all)


async def download_project(
    client: ElisAPIClient = None,
    org_path: Path = None,
    commit: bool = False,
    commit_message: str = "",
    download_all: bool = False,
):
    if not org_path:
        org_path = Path("./")

    # TODO: check the paths have the same format for comparing
    # TODO: should files be put for mapping update even if overwrite did not happen?
    changed_files = get_changed_file_paths(settings.SOURCE_DIRNAME)
    changed_files = list(map(lambda x: x[1], changed_files))

    if settings.IS_PROJECT_IN_SAME_ORG:
        await download_organization_combined_source_target(
            client=client,
            org_path=org_path,
            commit=commit,
            commit_message=commit_message,
            changed_files=changed_files,
            download_all=download_all,
        )
    else:
        await download_organizations(
            org_path=org_path,
            commit=commit,
            commit_message=commit_message,
            changed_files=changed_files,
            download_all=download_all,
        )


async def download_organizations(
    org_path: Path = None,
    commit: bool = False,
    commit_message: str = "",
    changed_files: list = [],
    download_all: bool = False,
):
    try:
        mapping_path = org_path / settings.MAPPING_FILENAME
        mapping = await read_mapping(mapping_path)
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
            changed_files=changed_files,
            download_all=download_all,
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
            changed_files=changed_files,
            download_all=download_all,
        )

        # Make the previous mapping conform in structure
        await migrate_mapping("mapping.yaml")
        mapping = await read_mapping(mapping_path)

        await create_update_mapping(
            org_path=org_path,
            organization=source_organization,
            workspaces_for_mapping=[*source_workspaces, *target_workspaces],
            schemas_for_mapping=[*source_schemas, *target_schemas],
            hooks_for_mapping=[*source_hooks, *target_hooks],
            old_mapping=mapping,
        )

        if commit:
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", commit_message])

    except Exception as e:
        display_error(f"Error during project {settings.DOWNLOAD_COMMAND_NAME}: {e}", e)


async def download_organization_single(
    client: ElisAPIClient,
    org_path: Path,
    destination: str = "",
    previous_sources: dict = {},
    previous_targets: dict = {},
    org_config_path: str = "",
    changed_files: list = [],
    download_all: bool = False,
):
    print(Panel("Scanning for remote changes..."))

    organizations = [org async for org in client.list_all_organizations()]
    if not len(organizations):
        raise click.ClickException("No organization found.")
    organization = await client._http_client.fetch_one(
        Resource.Organization, organizations[0].id
    )

    if not org_config_path:
        org_config_path = org_path / destination / "organization.json"

    if download_all or await should_write_object(
        org_config_path, organization, changed_files
    ):
        await write_json(org_config_path, organization, "organization")

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
                sources=previous_sources,
                targets=previous_targets,
                changed_files=changed_files,
                download_all=download_all,
            ),
            download_schemas(
                client=client,
                org_path=org_path,
                destination=destination,
                sources=previous_sources,
                targets=previous_targets,
                changed_files=changed_files,
                download_all=download_all,
            ),
            download_hooks(
                client=client,
                org_path=org_path,
                destination=destination,
                sources=previous_sources,
                targets=previous_targets,
                changed_files=changed_files,
                download_all=download_all,
            ),
        ]
    )

    if destination:
        print(Panel(f"Finished {settings.DOWNLOAD_COMMAND_NAME} for {destination}."))
    else:
        print(Panel(f"Finished {settings.DOWNLOAD_COMMAND_NAME}."))
    return organization, workspaces_for_mapping, schemas_for_mapping, hooks_for_mapping


async def download_workspaces(
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict = {},
    destination: str = "",
    sources: dict = {},
    targets: dict = {},
    changed_files: list = [],
    download_all: bool = False,
):
    workspaces = []

    paginated_workspaces = [
        workspace async for workspace in client.list_all_workspaces()
    ]

    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_workspaces = await asyncio.gather(
        *[
            client._http_client.fetch_one(Resource.Workspace, ws.id)
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

        if download_all or await should_write_object(
            workspace_config_path, workspace, changed_files
        ):
            await write_json(workspace_config_path, workspace, "workspace")

        workspace["queues"] = await download_queues_for_workspace(
            client=client,
            parent_dir=workspace_config_path.parent,
            workspace_id=workspace["id"],
            changed_files=changed_files,
            download_all=download_all,
        )
        workspaces.append((destination_local, workspace))

    return workspaces


async def download_queues_for_workspace(
    client: ElisAPIClient,
    parent_dir: Path,
    workspace_id: int,
    changed_files: list = [],
    download_all: bool = False,
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
        if download_all or await should_write_object(
            queue_path / "queue.json", queue, changed_files
        ):
            await write_json(queue_path / "queue.json", queue, "queue")

        inbox_id = extract_id_from_url(queue["inbox"])
        if inbox_id:
            queue["inbox"] = await download_inbox(
                client=client,
                parent_dir=queue_path,
                inbox_id=inbox_id,
                changed_files=changed_files,
                download_all=download_all,
            )
        queues.append(queue)

    return queues


async def download_inbox(
    client: ElisAPIClient,
    parent_dir: Path,
    inbox_id: int,
    changed_files: list = [],
    download_all: bool = False,
):
    inbox = await client._http_client.fetch_one(Resource.Inbox, inbox_id)
    inbox_path = parent_dir / "inbox.json"
    if download_all or await should_write_object(inbox_path, inbox, changed_files):
        await write_json(inbox_path, inbox, "inbox")

    return inbox


async def download_schemas(
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict = {},
    destination: str = "",
    sources: dict = {},
    targets: dict = {},
    changed_files: list = [],
    download_all: bool = False,
):
    schemas = []

    paginated_schemas = [schema async for schema in client.list_all_schemas()]

    # Refetch because schema fields are not fully listed
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_schemas = await asyncio.gather(
        *[
            client._http_client.fetch_one(Resource.Schema, schema.id)
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

        if download_all or await should_write_object(
            schema_config_path, schema, changed_files
        ):
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
    mapping: dict = {},
    destination: str = "",
    sources: dict = {},
    targets: dict = {},
    changed_files: list = [],
    download_all: bool = False,
):
    hooks = []

    paginated_hooks = [hook async for hook in client.list_all_hooks()]

    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_hooks = await asyncio.gather(
        *[
            client._http_client.fetch_one(Resource.Hook, hook.id)
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

        if download_all or await should_write_object(
            hook_config_path, hook, changed_files
        ):
            await write_json(hook_config_path, hook, "hook")
        hooks.append((destination_local, hook))

        if hook["extension_source"] != "rossum_store":
            if hook_code := hook.get("config", {}).get("code", None):
                hook_runtime = hook["config"].get("runtime")
                extension = ".py" if "python" in hook_runtime else ".js"
                hook_code_path = hook_config_path.with_suffix(extension)
                await write_str(hook_code_path, hook_code)

    return hooks


async def download_organization_combined_source_target(
    client: ElisAPIClient = None,
    org_path: Path = None,
    commit: bool = False,
    commit_message: str = "",
    changed_files: list = [],
    download_all: bool = False,
):
    try:
        if not client:
            client = ElisAPIClient(
                base_url=settings.SOURCE_API_URL,
                token=settings.SOURCE_TOKEN,
                username=settings.SOURCE_USERNAME,
                password=settings.SOURCE_PASSWORD,
            )

        mapping_path = org_path / settings.MAPPING_FILENAME
        mapping = await read_mapping(mapping_path)
        if not mapping:
            mapping = create_empty_mapping()
        previous_sources, previous_targets = extract_sources_targets(mapping)
        org_config_path = org_path / settings.SOURCE_DIRNAME / "organization.json"

        (
            organization,
            workspaces_for_mapping,
            schemas_for_mapping,
            hooks_for_mapping,
        ) = await download_organization_single(
            client=client,
            org_path=org_path,
            previous_sources=previous_sources,
            previous_targets=previous_targets,
            org_config_path=org_config_path,
            changed_files=changed_files,
            download_all=download_all,
        )

        # Make the previous mapping conform in structure
        await migrate_mapping("mapping.yaml")
        mapping = await read_mapping(mapping_path)

        await create_update_mapping(
            org_path=org_path,
            organization=organization,
            workspaces_for_mapping=workspaces_for_mapping,
            schemas_for_mapping=schemas_for_mapping,
            hooks_for_mapping=hooks_for_mapping,
            old_mapping=mapping,
        )

        if commit:
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", commit_message])

    except Exception as e:
        display_error(f"Error during project {settings.DOWNLOAD_COMMAND_NAME}: {e}", e)
