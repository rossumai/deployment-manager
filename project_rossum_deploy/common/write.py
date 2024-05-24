from typing import Any
from anyio import Path
from rossum_api.api_client import Resource

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.common.determine_path import determine_object_type_from_path
from project_rossum_deploy.utils.functions import (
    templatize_name_id,
    write_json,
    write_str,
)


async def create_local_object(path: Path, object: dict):
    object_type = determine_object_type_from_path(path)
    await write_json(path, object, object_type)
    if object_type == Resource.Schema:
        formula_fields = find_formula_fields_in_schema(object["content"])
        if formula_fields:
            formula_directory_path = create_formula_directory_path(path, object)
            for field_id, code in formula_fields:
                await create_formula_file(
                    formula_directory_path / f"{field_id}.py", code
                )
    elif object_type == Resource.Hook:
        custom_hook_code_path = create_custom_hook_code_path(path, object)
        if custom_hook_code_path:
            await write_str(
                custom_hook_code_path, object.get("config", {}).get("code", None)
            )


def find_formula_fields_in_schema(node: Any) -> list[tuple[str, str]]:
    formula_fields = []

    def add_fields(node: dict):
        if node["category"] == "datapoint" and (formula := node.get("formula", None)):
            return [(node["id"], formula)]
        elif "children" in node:
            return find_formula_fields_in_schema(node["children"])
        return []

    if isinstance(node, list):
        for subnode in node:
            formula_fields.extend(add_fields(subnode))
    elif isinstance(node, dict):
        formula_fields.extend(add_fields(node))

    return formula_fields


def create_custom_hook_code_path(hook_path: Path, hook: object):
    if hook["extension_source"] != "rossum_store" and hook.get("config", {}).get(
        "code", None
    ):
        hook_runtime = hook["config"].get("runtime")
        extension = ".py" if "python" in hook_runtime else ".js"
        return hook_path.with_suffix(extension)
    return None


def create_formula_directory_path(schema_path: Path, schema_name: str, schema_id: int):
    return (
        schema_path.parent
        / f"{settings.FORMULA_DIR_PREFIX}{templatize_name_id(schema_name, schema_id)}"
    )


async def create_formula_file(path: Path, code: str):
    await write_str(path, code)
