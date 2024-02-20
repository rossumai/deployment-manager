from copy import deepcopy
from anyio import Path
from rich import print
from rich.panel import Panel
from rich.progress import Progress


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
from project_rossum_deploy.common.attribute_override import override_attributes
from project_rossum_deploy.common.upload import (
    upload_organization,
    upload_schema,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    detemplatize_name_id,
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

    source_id_target_pairs = {
        mapping["organization"]["id"]: {"id": mapping["organization"]["target_object"]}
    }

    try:
        organization = await read_json(
            org_path / settings.SOURCE_DIRNAME / "organization.json"
        )
        # Use only a subset of org fields where it makes sense to migrate
        organization_fields = {k: organization[k] for k in settings.ORGANIZATION_FIELDS}
        with Progress() as progress:
            task = progress.add_task("Releasing organization...", total=1)
            source_id_target_pairs[
                mapping["organization"]["id"]
            ] = await upload_organization(
                client, organization_fields, target_organization
            )
            progress.update(task, advance=1)

            source_path = org_path / settings.SOURCE_DIRNAME

            source_id_target_pairs = {
                **(await migrate_schemas(source_path, client, mapping, progress)),
                **(await migrate_hooks(source_path, client, mapping, progress)),
            }
            source_id_target_pairs = await migrate_workspaces(
                source_path, client, mapping, source_id_target_pairs, progress
            )

        # Update the mapping with right hand sides (targets) created during migration
        await write_mapping(org_path / settings.MAPPING_FILENAME, mapping)
    except Exception as e:
        print(f"Unexpected error while migrating objects: {e}")

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
            and not mapping_object.get("target_object", None)
            and not mapping_object.get("ignore", None)
        ):
            new_object = source_id_target_pairs[mapping_object["id"]]
            new_object = override_attributes(mapping, mapping_object, new_object)
            if 'inbox' in new_object:
                del new_object['inbox']
            await update_object(path=None, client=client, object=new_object)

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
    source_path: Path, client: ElisAPIClient, mapping: dict, progress: Progress
):
    source_id_target_pairs = {}
    schema_paths = [
        schema_path async for schema_path in (source_path / "schemas").iterdir()
    ]
    task = progress.add_task("Releasing schemas...", total=len(schema_paths))

    for schema_path in schema_paths:
        try:
            _, id = detemplatize_name_id(schema_path.stem)
            schema = await read_json(schema_path)

            schema["queues"] = []

            schema_mapping = find_mapping_of_object(
                mapping["organization"]["schemas"], id
            )
            if schema_mapping.get("ignore", None):
                progress.update(task, advance=1)
                continue

            schema = override_attributes(
                complete_mapping=mapping, mapping=schema_mapping, object=schema
            )
            result = await upload_schema(
                client, schema, schema_mapping["target_object"]
            )
            schema_mapping["target_object"] = result["id"]
            source_id_target_pairs[id] = result

            progress.update(task, advance=1)
        except Exception as e:
            print(f"Error while migrationg schema: {e}")

    return source_id_target_pairs
