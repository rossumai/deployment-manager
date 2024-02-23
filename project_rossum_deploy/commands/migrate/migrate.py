from copy import deepcopy
from anyio import Path
from rich import print
from rich.panel import Panel
from rich.progress import Progress
import asyncio

import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.download.download import (
    download_project,
)
from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    traverse_mapping,
)
from project_rossum_deploy.commands.migrate.hooks import migrate_hooks
from project_rossum_deploy.commands.migrate.workspaces import migrate_workspaces
from project_rossum_deploy.commands.upload import update_object
from project_rossum_deploy.common.attribute_override import override_attributes_v2
from project_rossum_deploy.common.upload import (
    upload_organization,
    upload_schema,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    detemplatize_name_id,
    extract_flat_lookup_table,
    extract_sources_targets,
    read_json,
)


@click.command(
    name=settings.MIGRATE_COMMAND_NAME,
    help="""
Applies selected changes onto other objects.
If these objects don't exist, they get crated.
The specifics of what objects to migrate where can be specified in a mapping.yaml file.
               """,
)
@coro
async def migrate_project_wrapper():
    await migrate_project()


async def migrate_project(
    client: ElisAPIClient = None,
    org_path: Path = None,
):
    if not org_path:
        org_path = Path("./")
    mapping = await read_mapping(org_path / settings.MAPPING_FILENAME)
    previous_mapping = deepcopy(mapping)

    target_organization = mapping["organization"]["target_object"]
    if not target_organization:
        raise click.ClickException(
            "No target for organization. If you want to migrate inside the same organization, just target its own ID."
        )

    if not client:
        if settings.IS_PROJECT_IN_SAME_ORG:
            client = ElisAPIClient(
                base_url=settings.SOURCE_API_URL,
                token=settings.SOURCE_TOKEN,
                username=settings.SOURCE_USERNAME,
                password=settings.SOURCE_PASSWORD,
            )
        else:
            client = ElisAPIClient(
                base_url=settings.TARGET_API_URL,
                token=settings.TARGET_TOKEN,
                username=settings.TARGET_USERNAME,
                password=settings.TARGET_PASSWORD,
            )

    source_id_target_pairs = {}
    sources_by_source_id_map = {}

    # TODO: dry-run / preview before releasing
    # ! References might not yet exist -> have to use dummies

    try:
        with Progress() as progress:
            task = progress.add_task("Releasing organization...", total=1)

            organization = await read_json(
                org_path / settings.SOURCE_DIRNAME / "organization.json"
            )
            sources_by_source_id_map[organization["id"]] = organization
            # Use only a subset of org fields where it makes sense to migrate
            organization_fields = {
                k: organization[k] for k in settings.ORGANIZATION_FIELDS
            }

            source_id_target_pairs[
                mapping["organization"]["id"]
            ] = await upload_organization(
                client, organization_fields, target_organization
            )
            progress.update(task, advance=1)

            source_path = org_path / settings.SOURCE_DIRNAME

            await migrate_schemas(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
            )
            await migrate_hooks(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
            )
            await migrate_workspaces(
                source_path=source_path,
                client=client,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
                sources_by_source_id_map=sources_by_source_id_map,
                progress=progress,
            )

        # Update the mapping with right hand sides (targets) created during migration
        await write_mapping(org_path / settings.MAPPING_FILENAME, mapping)
    except Exception as e:
        print(f"Unexpected error while migrating objects: {e}")

    _, previous_targets = extract_sources_targets(previous_mapping)
    lookup_table = extract_flat_lookup_table(mapping)
    current_target_ids = set(lookup_table.values())

    previous_target_ids = []
    for objects in previous_targets.values():
        if isinstance(objects, list):
            previous_target_ids.extend(objects)
    previous_target_ids = set(previous_target_ids)

    new_target_ids = current_target_ids.difference(previous_target_ids)

    if len(new_target_ids):
        click.echo("These target objects were created:")
        click.echo(new_target_ids)

    print("Running attribute_override...")
    for mapping_object in traverse_mapping(mapping):
        if mapping_object.get("attribute_override", None) and not mapping_object.get(
            "ignore", None
        ):
            target_object = source_id_target_pairs[mapping_object["id"]]

            target_object = await client._http_client.request_json(
                "GET", target_object["url"]
            )
            override_attributes_v2(
                lookup_table=lookup_table,
                submapping=mapping_object,
                object=target_object,
            )

            await update_object(path=None, client=client, object=target_object)

    print(Panel(f"Finished {settings.MIGRATE_COMMAND_NAME}."))

    await download_project(client=client, org_path=org_path)


def find_created_target_ids(previous_mapping: dict, source_id_target_pairs: dict):
    _, previous_targets = extract_sources_targets(previous_mapping)
    previous_target_ids = []
    for objects in previous_targets.values():
        if isinstance(objects, list):
            previous_target_ids.extend(objects)
    previous_target_ids = set(previous_target_ids)

    all_target_ids = set()
    for object in source_id_target_pairs.values():
        all_target_ids.add(object["id"])

    return all_target_ids.difference(previous_target_ids)


async def migrate_schemas(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict,
    sources_by_source_id_map: dict,
    progress: Progress,
):
    schema_paths = [
        schema_path async for schema_path in (source_path / "schemas").iterdir()
    ]
    task = progress.add_task("Releasing schemas...", total=len(schema_paths))

    async def migrate_schema(schema_path: Path):
        try:
            _, id = detemplatize_name_id(schema_path.stem)
            schema = await read_json(schema_path)
            sources_by_source_id_map[id] = schema

            schema["queues"] = []

            schema_mapping = find_mapping_of_object(
                mapping["organization"]["schemas"], id
            )
            if schema_mapping.get("ignore", None):
                progress.update(task, advance=1)
                return

            result = await upload_schema(
                client, schema, schema_mapping["target_object"]
            )
            schema_mapping["target_object"] = result["id"]
            source_id_target_pairs[id] = result

            progress.update(task, advance=1)
        except Exception as e:
            print(f"Error while migrationg schema: {e}")

    await asyncio.gather(
        *[migrate_schema(schema_path=schema_path) for schema_path in schema_paths]
    )
