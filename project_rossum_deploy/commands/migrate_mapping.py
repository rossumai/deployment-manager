from anyio import Path
from rich import print
from rich.panel import Panel

import click

from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.commands.migrate.helpers import traverse_mapping
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import coro


@click.command(
    name=settings.MIGRATE_MAPPING_COMMAND_NAME,
    help="""
Updates the current mapping.yaml to conform with the latest PRD syntax.
               """,
)
@click.argument("mapping", default="mapping.yaml")
@coro
async def migrate_mapping_wrapper(mapping: str):
    await migrate_mapping(mapping_file=mapping)


async def migrate_mapping(mapping_file: str = "", print_result: bool = True):
    mapping_path = Path("./") / mapping_file
    if not await mapping_path.exists():
        raise click.ClickException(f"Mapping '{mapping_path}' not found.")

    mapping = await read_mapping(mapping_path)

    for mapping_object in traverse_mapping(mapping["organization"]):
        target_object = mapping_object.get("target_object", None)
        attribute_override = mapping_object.get("attribute_override", None)

        target_objects = mapping_object.get("targets", [])
        new_target = {
            "target_id": target_object,
        }
        if attribute_override:
            new_target["attribute_override"] = attribute_override
        # Don't add a null target_object if there already is a list
        if len(target_objects) and target_object is None:
            mapping_object["targets"] = target_objects
        else:
            mapping_object["targets"] = [new_target, *target_objects]
        mapping_object.pop("target_object", None)
        mapping_object.pop("attribute_override", None)

    await write_mapping(mapping_path=mapping_path, mapping=mapping)

    if print_result:
        print(Panel(f'Successfully updated/migrated "{mapping_path}".'))
