import asyncio
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.download.helpers import (
    create_formula_directory_path,
    should_write_object,
)

from project_rossum_deploy.common.read_write import (
    create_formula_file,
    find_formula_fields_in_schema,
    write_json,
)
from project_rossum_deploy.utils.functions import (
    templatize_name_id,
)


async def download_schemas(
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict = {},
    destination: str = "",
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
        schema_config_path = (
            org_path
            / destination
            / "schemas"
            / f"{templatize_name_id(schema['name'], schema['id'])}.json"
        )

        if download_all or await should_write_object(
            schema_config_path, schema, changed_files
        ):
            await write_json(
                schema_config_path,
                schema,
                Resource.Schema,
                log_message=f"Pulled {schema_config_path}",
            )

            formula_fields = find_formula_fields_in_schema(schema["content"])
            if formula_fields:
                formula_directory_path = create_formula_directory_path(
                    schema_config_path, schema.get("name", ""), schema.get("id", "")
                )
                for field_id, code in formula_fields:
                    await create_formula_file(
                        formula_directory_path / f"{field_id}.py", code
                    )

        schemas.append((destination, schema))

    return schemas
