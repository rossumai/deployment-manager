import asyncio
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


NON_VERSIONED_ATTRIBUTES_FILE_LOCK = asyncio.Lock()


async def write_object_to_json(
    path: Path, object: dict, type: Resource = None, log_message: str = ""
):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    if type:
        # NON_PULLED keys are thrown away completely
        if non_pulled_keys := settings.NON_PULLED_KEYS_PER_OBJECT.get(type):
            for key in non_pulled_keys:
                if key in object:
                    del object[key]
        # NON_VERSIONED_ATTRIBUTES are saved in separate file
        if non_versioned_keys := settings.NON_VERSIONED_ATTRIBUTES:
            for key in non_versioned_keys:
                if key in object:
                    non_versioned_key_written = await write_non_versioned_attribute(path, object, key)
                    if non_versioned_key_written:
                        del object[key]
    with open(path, "w") as wf:
        json.dump(object, wf, indent=2)

    if log_message:
        print(log_message)


async def write_non_versioned_attribute(path, object_, key):
    if len(path.parents) < 3:
        # outside subdirectory, no non_versioned_attribute allowed at this level
        return False

    # path.parents is a list of full paths which are parents for the current file from closest to furthest
    # path.parents example: if we have a file a/b/c/d/e.txt, Path(e.txt).parents would be [a/b/c/d, a/b/c, a/b, a, .]
    # `non_versioned_attributes` file we need to find is always saved on org/suborg level
    # That's why it's always -3. then, we can load org/suborg/non_versioned_object_attributes.json
    subdir_path = path.parents[-3]  # path to dir/subdir, or organization/suborganization
    non_versioned_attributes_file = subdir_path / settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME  # file is saved in root for each subdirectory

    # avoid simultaneous write to the same file
    async with NON_VERSIONED_ATTRIBUTES_FILE_LOCK:
        if await non_versioned_attributes_file.exists():
            with open(non_versioned_attributes_file, "r", encoding="utf-8") as f:
                non_versioned_data = json.load(f)
        else:
            non_versioned_data = {}

        # Saving new value of the key to the non_versioned file structure
        # Example: path.parts[2:] is ["c", "d", "e", "f"], key is KEY and current_level[KEY] is VALUE.
        # This loop will result in writing a following value into non_versioned_data: {c: {d: {e: {f: {KEY: VALUE}}}}}
        # It benefits from how references are used in python.
        current_level = non_versioned_data
        for part in path.parts[2:]:
            if part not in current_level or not isinstance(current_level[part], dict):
                current_level[part] = {}
            current_level = current_level[part]
        current_level[key] = object_[key]

        try:
            with open(non_versioned_attributes_file, "w", encoding="utf-8") as f:
                json.dump(non_versioned_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error: Failed to write to '{non_versioned_attributes_file}': {e}")
        return False


async def write_str(path: Path, code: str):
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        wf.write(code)


async def create_local_object(path: Path, object: dict):
    object_type = determine_object_type_from_path(path)
    await write_object_to_json(path, object, object_type)
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


def find_fields_in_schema(node: Any) -> list[tuple[dict]]:
    fields = []

    def add_fields(node: dict):
        if node["category"] == "datapoint":
            return [node]
        elif "children" in node:
            return find_fields_in_schema(node["children"])
        return []

    if isinstance(node, list):
        for subnode in node:
            fields.extend(add_fields(subnode))
    elif isinstance(node, dict):
        fields.extend(add_fields(node))

    return fields


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


async def read_object_from_json(path: Path) -> dict:
    object_ = json.loads(await path.read_text())
    await read_non_versioned_attribute_data(path, object_)
    return object_


async def read_non_versioned_attribute_data(path, object_):
    # extend object with data from separate file

    if len(path.parents) < 3:
        # outside subdirectory, no non_versioned_attribute allowed at this level
        return

    # fore more clarity of how this works, read comments in the `write_non_versioned_attribute` function
    subdir_path = path.parents[-3] # path to dir/subdir, or organization/suborganization
    non_versioned_attributes_file = subdir_path / settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME  # file is saved in root for each subdirectory
    if await non_versioned_attributes_file.exists():
        non_versioned_data = {}
        # locking the file while reading to be sure other process won't write in the meantime
        async with NON_VERSIONED_ATTRIBUTES_FILE_LOCK:
            with open(non_versioned_attributes_file, "r") as f:
                non_versioned_data = json.load(f)

        # fore more clarity of how this works, read the comment before the writing loop in the `write_non_versioned_attribute` function
        # this function does the opposite and reads the data from the separate file, and results in having the full object in memory
        for path_part in path.parts[2:]:
            # iterate deeper into the object until the filename is found
            non_versioned_data = non_versioned_data.get(path_part)
            if not non_versioned_data:
                return
        if non_versioned_data:
            # join non_versioned data into the object
            object_.update(non_versioned_data)
    return


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
