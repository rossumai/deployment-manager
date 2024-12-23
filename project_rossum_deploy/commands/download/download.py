import asyncio
import subprocess
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from rich import print
from rich.panel import Panel

import click
from project_rossum_deploy.commands.download.helpers import (
    get_all_objects_for_destination,
    remove_local_nonexistent_objects,
    replace_code_paths,
    should_write_object,
)
from project_rossum_deploy.commands.download.hooks import download_hooks
from project_rossum_deploy.common.client import create_and_validate_client
from project_rossum_deploy.common.mapping import (
    create_update_mapping,
    extract_sources_targets,
    read_mapping,
)

from project_rossum_deploy.commands.download.schemas import download_schemas
from project_rossum_deploy.commands.download.workspaces import download_workspaces
from project_rossum_deploy.common.git import get_changed_file_paths
from project_rossum_deploy.commands.migrate_mapping import migrate_mapping
from project_rossum_deploy.common.mapping import create_empty_mapping
from project_rossum_deploy.common.read_write import write_json
from project_rossum_deploy.utils.consts import display_error, settings
from project_rossum_deploy.utils.functions import (
    coro,
)


@click.command(
    name=settings.DOWNLOAD_COMMAND_NAME,
    help="""
Downloads all Rossum objects from the user's default (first) organization.
Creates a local organization directory structure with the configs of these objects.
In case the directory already exists, it first deletes its contents and then downloads them anew.
               """,
)
@click.argument(
    "destination",
    default=settings.BOTH_DESTINATIONS,
    type=click.Choice(
        [settings.BOTH_DESTINATIONS, settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]
    ),
)
@click.option(
    "--commit",
    "-c",
    default=False,
    is_flag=True,
    help="Commits the pulled changes automatically.",
)
@click.option(
    "--all",
    "-a",
    default=False,
    is_flag=True,
    help="Downloads all remote files and overwrites the local ones.",
)
@click.option(
    "--message",
    "-m",
    default="Sync changes to local",
    help="Commit message for pulling.",
)
@coro
# To be able to run the command progammatically without the CLI decorators
async def download_project_wrapper(
    destination: str, commit: bool = False, message: str = "", all: bool = False
):
    await download_project(
        destination=destination, commit_message=message, commit=commit, download_all=all
    )


async def download_project(
    destination: str = "",
    client: ElisAPIClient = None,
    org_path: Path = None,
    commit: bool = False,
    commit_message: str = "",
    download_all: bool = False,
):
    if not org_path:
        org_path = Path("./")

    changed_files = [
        *get_changed_file_paths(settings.SOURCE_DIRNAME),
        *get_changed_file_paths(settings.TARGET_DIRNAME),
    ]
    changed_files = list(map(lambda x: x[1], changed_files))
    changed_files = replace_code_paths(changed_files)

    try:
        if settings.IS_PROJECT_IN_SAME_ORG:
            await download_organization_combined_source_target(
                client=client,
                org_path=org_path,
                changed_files=changed_files,
                download_all=download_all,
            )
        else:
            await download_organizations_separate(
                org_path=org_path,
                destination=destination,
                changed_files=changed_files,
                download_all=download_all,
            )

        if commit:
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-m", commit_message])

    except Exception as e:
        display_error(f"Error during project {settings.DOWNLOAD_COMMAND_NAME}: {e}", e)


async def download_organizations_separate(
    org_path: Path = None,
    destination: str = settings.BOTH_DESTINATIONS,
    changed_files: list = [],
    download_all: bool = False,
):
    # Make the previous mapping conform in structure
    await migrate_mapping("mapping.yaml", print_result=False)
    mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
    if not mapping:
        mapping = create_empty_mapping()

    if destination in [settings.SOURCE_DIRNAME, settings.BOTH_DESTINATIONS]:
        source_client = await create_and_validate_client(settings.SOURCE_DIRNAME)
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
    else:
        (
            source_organization,
            source_workspaces,
            source_schemas,
            source_hooks,
        ) = await get_all_objects_for_destination(
            org_path=org_path, destination=settings.SOURCE_DIRNAME
        )

    if destination in [settings.TARGET_DIRNAME, settings.BOTH_DESTINATIONS]:
        target_client = await create_and_validate_client(settings.TARGET_DIRNAME)
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
    else:
        (
            _,
            target_workspaces,
            target_schemas,
            target_hooks,
        ) = await get_all_objects_for_destination(
            org_path=org_path, destination=settings.TARGET_DIRNAME
        )

    await create_update_mapping(
        org_path=org_path,
        organization=source_organization,
        workspaces_for_mapping=[*source_workspaces, *target_workspaces],
        schemas_for_mapping=[*source_schemas, *target_schemas],
        hooks_for_mapping=[*source_hooks, *target_hooks],
        old_mapping=mapping,
    )

    if destination in [settings.SOURCE_DIRNAME, settings.BOTH_DESTINATIONS]:
        await remove_local_nonexistent_objects(
            source_client, org_path, settings.SOURCE_DIRNAME, mapping
        )
    if destination in [settings.TARGET_DIRNAME, settings.BOTH_DESTINATIONS]:
        await remove_local_nonexistent_objects(
            target_client, org_path, settings.TARGET_DIRNAME, mapping
        )


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
    print(
        Panel(
            f"Scanning for remote changes{ f' in {destination}' if destination else ''}..."
        )
    )

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
        await write_json(
            org_config_path,
            organization,
            Resource.Organization,
            log_message=f"Pulled {org_config_path}.",
        )

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


async def download_organization_combined_source_target(
    client: ElisAPIClient = None,
    org_path: Path = None,
    changed_files: list = [],
    download_all: bool = False,
):
    if not client:
        client = await create_and_validate_client(settings.SOURCE_DIRNAME)

    # Make the previous mapping conform in structure
    await migrate_mapping("mapping.yaml", print_result=False)
    mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
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

    await create_update_mapping(
        org_path=org_path,
        organization=organization,
        workspaces_for_mapping=workspaces_for_mapping,
        schemas_for_mapping=schemas_for_mapping,
        hooks_for_mapping=hooks_for_mapping,
        old_mapping=mapping,
    )

    await remove_local_nonexistent_objects(
        client, org_path, settings.SOURCE_DIRNAME, mapping
    )
    await remove_local_nonexistent_objects(
        client, org_path, settings.TARGET_DIRNAME, mapping
    )
