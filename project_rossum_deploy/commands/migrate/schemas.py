import asyncio
import functools
from typing import Any
from anyio import Path

from rossum_api import ElisAPIClient
from rich.progress import Progress
from rich.panel import Panel
from rich import print
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.migrate.helpers import (
    check_if_selected,
    migrate_object_to_multiple_targets,
    simulate_migrate_object,
)
from project_rossum_deploy.common.mapping import find_mapping_of_object
from project_rossum_deploy.common.read_write import read_formula_file, read_json
from project_rossum_deploy.utils.consts import (
    display_error,
    settings,
    PrdVersionException,
)
from project_rossum_deploy.commands.migrate.upload_helpers import upload_schema
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    templatize_name_id,
)


async def migrate_schemas(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict[int, list],
    sources_by_source_id_map: dict,
    progress: Progress,
    plan_only: bool = False,
    selected_only: bool = False,
    target_objects: list[dict] = [],
    errors: dict = {},
    force: bool = False,
):
    schema_paths = [
        schema_path async for schema_path in (source_path / "schemas").iterdir()
    ]
    task = progress.add_task("Releasing schemas.", total=len(schema_paths))

    async def migrate_schema(schema_path: Path):
        if schema_path.suffix != ".json":
            progress.update(task, advance=1)
            return

        try:
            _, id = detemplatize_name_id(schema_path.stem)
            schema = await read_json(schema_path)
            sources_by_source_id_map[id] = schema

            schema["queues"] = []

            schema_mapping = find_mapping_of_object(
                mapping["organization"]["schemas"], id
            )

            skip_migration = schema_mapping.get("ignore", None) or (
                selected_only and not check_if_selected(schema_mapping)
            )

            await update_formula_fields_code(schema_path, schema)

            if plan_only or skip_migration:
                partial_upload_schema = functools.partial(
                    simulate_migrate_object,
                    client=client,
                    source_object=schema,
                    target_object_type=Resource.Schema,
                    silent=skip_migration,
                )
            else:
                partial_upload_schema = functools.partial(
                    upload_schema,
                    client,
                    schema,
                    target_objects=target_objects,
                    errors=errors,
                    force=force,
                )
            source_id_target_pairs[id] = []
            if "target_object" in schema_mapping:
                raise PrdVersionException(
                    f'Detected "target_object" for schema with ID "{id}". Please run "prd {settings.MIGRATE_MAPPING_COMMAND_NAME}" to have the correct mapping format.'
                )

            results = await migrate_object_to_multiple_targets(
                submapping=schema_mapping,
                upload_function=partial_upload_schema,
                plan_only=plan_only,
            )
            source_id_target_pairs[id].extend(results)

            progress.update(task, advance=1)
        except PrdVersionException as e:
            raise e
        except Exception as e:
            display_error(f"Error while migrating schema: {e}", e)

    if plan_only:
        print(Panel("Simulating workspaces."))

    await asyncio.gather(
        *[
            migrate_schema(schema_path=schema_path)
            for schema_path in schema_paths
            if await schema_path.is_file()
        ]
    )


def find_schema_id(schema: Any, schema_id: str):
    if isinstance(schema, list):
        for subschema in schema:
            result = find_schema_id(subschema, schema_id)
            if result:
                return result
    elif isinstance(schema, dict) and "children" in schema:
        if isinstance(schema["children"], dict):
            result = find_schema_id(schema["children"], schema_id)
            if result:
                return result
        elif isinstance(schema["children"], list):
            for subschema in schema["children"]:
                result = find_schema_id(subschema, schema_id)
                if result:
                    return result
    elif isinstance(schema, dict) and schema.get("id", None) == schema_id:
        return schema


async def update_formula_fields_code(schema_path: Path, schema: dict):
    """Checks if there is not newer code in the associated formula fields and uses that for release.
    The original schema file is not modified.
    """
    formula_directory = (
        schema_path.parent
        / f"{settings.FORMULA_DIR_PREFIX}{templatize_name_id(schema['name'], schema['id'])}"
    )
    if not await formula_directory.exists():
        return

    async for field_file_path in formula_directory.iterdir():
        formula_code = await read_formula_file(field_file_path)
        formula_name = field_file_path.stem

        schema_id = find_schema_id(schema["content"], formula_name)
        schema_id["formula"] = formula_code
