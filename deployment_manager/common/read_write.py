import dataclasses
import json
from typing import Any
from anyio import Path
from rich import print
from rossum_api.api_client import Resource
import yaml
from ruamel.yaml import YAML


from deployment_manager.utils.consts import settings
from deployment_manager.common.determine_path import determine_object_type_from_path


async def write_json(
    path: Path, object: dict, type: Resource = None, log_message: str = ""
):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    if type:
        ignored_keys = settings.IGNORED_KEYS.get(type)
        if ignored_keys:
            for key in ignored_keys:
                if key in object:
                    del object[key]
    with open(path, "w") as wf:
        json.dump(object, wf, indent=2)

    if log_message:
        print(log_message)


async def write_str(path: Path, code: str):
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        wf.write(code)


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
    if hook.get("extension_source", "") != "rossum_store" and hook.get(
        "config", {}
    ).get("code", None):
        hook_runtime = hook["config"].get("runtime")
        extension = ".py" if "python" in hook_runtime else ".js"
        return hook_path.with_suffix(extension)
    return None


def create_formula_directory_path(schema_path: Path):
    return schema_path.parent / f"{settings.FORMULA_DIR_NAME}"


async def create_formula_file(path: Path, code: str):
    await write_str(path, code)


async def read_json(path: Path) -> dict:
    return json.loads(await path.read_text())


async def write_yaml(path: Path, object: dict):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        yaml.dump(object, wf, sort_keys=False)


def read_yaml(path: Path):
    with open(path, "r") as rf:
        return yaml.safe_load(rf)


async def read_formula_file(path: Path):
    return await path.read_text()


async def read_prd_project_config(project_path: Path):
    config_path = project_path / settings.CONFIG_FILENAME
    if await config_path.exists():
        return YAML().load(await config_path.read_text())
    return None


async def read_prd_cred_file(org_path: Path):
    credentials_path: Path = org_path / settings.CREDENTIALS_FILENAME
    if await credentials_path.exists():
        return YAML().load(await credentials_path.read_text())
    return None


async def write_prd_cred_file(org_path: Path, object: dict):
    credentials_path: Path = org_path / settings.CREDENTIALS_FILENAME
    await write_yaml(credentials_path, object)
