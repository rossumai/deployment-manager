from copy import deepcopy
import json
import logging
from anyio import Path

import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.download.download import download_organization
from project_rossum_deploy.commands.download.helpers import extract_sources_targets
from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.commands.migrate.helpers import (
    is_org_targetting_itself,
    find_mapping_of_object,
    traverse_mapping,
)
from project_rossum_deploy.commands.migrate.hooks import migrate_hooks
from project_rossum_deploy.commands.migrate.workspaces import migrate_workspaces
from project_rossum_deploy.commands.upload import update_object
from project_rossum_deploy.common.attribute_override import override_attributes
from project_rossum_deploy.common.upload import (
    upload_organization,
    upload_schema,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    detemplatize_name_id,
)


@click.command(
    name=settings.MIGRATE_COMMAND_NAME,
    help="""
Applies selected changes onto other objects.
If these objects don't exist, they get crated.
The specifics of what objects to migrate where can be specified in a mapping.yaml file.
               """,
)
@click.option(
    "--mapping",
    default=settings.MAPPING_FILENAME,
    show_default=True,
    help="Path to the mapping file to use.",
)
@coro
async def migrate_project(mapping: str):
    mapping_file = mapping
    org_path = Path("./")
    mapping = await read_mapping(org_path / mapping_file)
    previous_mapping = deepcopy(mapping)

    target_organization = mapping["organization"]["target"]
    if not target_organization:
        raise click.ClickException(
            "No target for organization. If you want to migrate inside the same organization, just target its own ID."
        )

    if is_org_targetting_itself(mapping):
        client = ElisAPIClient(
            base_url=settings.API_URL,
            token=settings.TOKEN,
            username=settings.USERNAME,
            password=settings.PASSWORD,
        )
    else:
        client = ElisAPIClient(
            base_url=settings.TO_API_URL,
            token=settings.TO_TOKEN,
            username=settings.TO_USERNAME,
            password=settings.TO_PASSWORD,
        )

    source_id_target_pairs = {}

    # TODO: add messages to signal progress

    try:
        organization = json.loads(await (org_path / "organization.json").read_text())
        # Use only a subset of org fields where it makes sense to migrate
        organization_fields = {k: organization[k] for k in settings.ORGANIZATION_FIELDS}
        await upload_organization(client, organization_fields, organization["id"])

        source_path = org_path / settings.SOURCE_DIRNAME

        source_id_target_pairs = {
            **(await migrate_schemas(source_path, client, mapping)),
            **(await migrate_hooks(source_path, client, mapping)),
        }
        source_id_target_pairs = await migrate_workspaces(
            source_path, client, mapping, source_id_target_pairs
        )

        # Update the mapping with right hand sides (targets) created during migration
        await write_mapping(org_path / mapping_file, mapping)
    except Exception as e:
        logging.error(f"Unexpected error while migrating objects: {e}")

    _, previous_targets = extract_sources_targets(previous_mapping)
    previous_target_ids = []
    for objects in previous_targets.values():
        if isinstance(objects, list):
            previous_target_ids.extend(objects)
    previous_target_ids = set(previous_target_ids)

    all_target_ids = set()
    for object in source_id_target_pairs.values():
        all_target_ids.add(object["id"])
    new_target_ids = all_target_ids.difference(previous_target_ids)

    if len(new_target_ids):
        click.echo("These target objects were created:")
        click.echo(new_target_ids)

    # In case of newly created objects, there could be references which did not exist at the time of the objects' creation
    # Attribute override is therefore run again for such objects.
    for mapping_object in traverse_mapping(previous_mapping):
        if (
            mapping_object.get("attribute_override", None)
            and not mapping_object.get("target", None)
            and not mapping_object.get("ignore", None)
        ):
            new_object = source_id_target_pairs[mapping_object["id"]]
            new_object = override_attributes(mapping, mapping_object, new_object)
            await update_object(path=None, client=client, object=new_object)

    if is_org_targetting_itself(mapping):
        click.echo(f"Running {settings.DOWNLOAD_COMMAND_NAME} for new target objects.")
        await download_organization()
    else:
        click.echo(
            f'{settings.MIGRATE_COMMAND_NAME} to organization "{target_organization}" was successful. Please run the {settings.DOWNLOAD_COMMAND_NAME} in that organization project.'
        )


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


async def migrate_schemas(source_path: Path, client: ElisAPIClient, mapping: dict):
    source_id_target_pairs = {}
    async for schema_path in (source_path / "schemas").iterdir():
        try:
            _, id = detemplatize_name_id(schema_path.stem)
            schema = json.loads(await schema_path.read_text())

            schema["queues"] = []

            schema_mapping = find_mapping_of_object(
                mapping["organization"]["schemas"], id
            )
            if schema_mapping.get("ignore", None):
                continue

            schema = override_attributes(
                complete_mapping=mapping, mapping=schema_mapping, object=schema
            )
            result = await upload_schema(client, schema, schema_mapping["target"])
            schema_mapping["target"] = result["id"]
            source_id_target_pairs[id] = result
        except Exception as e:
            logging.error(f'Error while migrationg schema "{id}: {e}')

    return source_id_target_pairs
