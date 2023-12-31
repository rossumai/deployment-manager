import json
from anyio import Path
import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.common.upload import upload_schema

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    detemplatize_name_id,
    read_yaml,
    write_yaml,
)


@click.command(
    name="migrate",
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
    mapping = read_yaml(org_path / mapping_file)

    target_organization = mapping["organization"]["target"]
    if not target_organization:
        raise click.ClickException(
            "No target for organization. If you want to migrate inside the same organization, just target its own ID."
        )

    if target_organization == mapping["organization"]["id"]:
        client = ElisAPIClient(
            base_url=settings.API_URL,
            username=settings.USERNAME,
            password=settings.PASSWORD,
        )
    else:
        # Create/update workspaces -> update mapping
        # Create update schemas -> update mapping
        # Create/update queues -> update mapping
        # Create update hooks -> update mapping
        client = ElisAPIClient(
            base_url=settings.TO_API_URL,
            username=settings.TO_USERNAME,
            password=settings.TO_PASSWORD,
        )

    # Update ORG based on the json

    source_path = org_path / settings.SOURCE_DIRNAME

    # Read through schemas, ignore queue deps, add to mapping
    async for schema_path in (source_path / "schemas").iterdir():
        name, id = detemplatize_name_id(schema_path.stem)
        schema = json.loads(await schema_path.read_text())

        schema_mapping = find_mapping_of_object(mapping["organization"]["schemas"], id)
        if not schema_mapping.get("ignore", None):
            result = await upload_schema(client, schema, schema_mapping["target"])
            schema_mapping["target"] = result["id"]
            break

    # Read through hooks, ignore queue deps, add to mapping

    # Read workspaces in filesystem, check them in mapping
    # Read child queues in FS, ignore if you already ignore WS
    # Read inbox of queue ...

    # Update the mapping with righ hand sides (targets) created during migration
    await write_yaml(org_path / mapping_file, mapping)


def find_mapping_of_object(sub_mapping: list[dict], id: int):
    for object in sub_mapping:
        if object["id"] == id:
            return object
    return None
