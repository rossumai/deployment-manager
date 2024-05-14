import asyncio
import os
import shutil
from typing import Any
from anyio import Path
from rich.prompt import Confirm
from rich import print
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.api_client import Resource
from rich.panel import Panel

from project_rossum_deploy.commands.upload.helpers import (
    determine_object_type_from_path,
)
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    display_error,
    find_all_object_paths,
    read_json,
    templatize_name_id,
    write_str,
)


async def should_write_object(path: Path, remote_object: Any, changed_files: list):
    if await path.exists():
        local_file = await read_json(path)

        if (local_timestamp := local_file.get("modified_at", "")) != (
            remote_timestamp := remote_object.get("modified_at", "")
        ):
            if path in changed_files:
                return Confirm.ask(
                    f'File "{path}" has local unversioned changes (local: {local_timestamp} | remote: {remote_timestamp}). Should the remote version overwrite the local one?',
                )
            return True

    else:
        return True


def del_dirs(src_dir):
    for dirpath, _, _ in os.walk(src_dir, topdown=False):  # Listing the files
        if dirpath == src_dir:
            break
        try:
            os.rmdir(dirpath)
        except OSError as e:
            if e.errno != 66:
                display_error("Error while deleting empty directories", e)


async def remove_local_nonexistent_objects(client: ElisAPIClient, base_path: Path):
    """
    Checks that the local object still exists in Rossum and removes its local file if not.
    """
    paths = await find_all_object_paths(base_path)

    async def remove_local_nonexistent_object(path: Path):
        object = await read_json(path)
        try:
            if url := object.get("url", ""):
                await client._http_client.request_json(method="GET", url=url)
        except APIClientError as e:
            if e.status_code == 404:
                print(
                    Panel(
                        f"Deleting local object that no longer exists in Rossum: {path}",
                        style="yellow",
                    )
                )
                os.remove(path)

                object_type = determine_object_type_from_path(path)
                if object_type == Resource.Schema:
                    formula_directory_path = create_formula_directory_path(path, object)
                    if await formula_directory_path.exists():
                        shutil.rmtree(formula_directory_path)
                elif object_type == Resource.Hook:
                    custom_hook_code_path = create_custom_hook_code_path(path, object)
                    if custom_hook_code_path:
                        os.remove(custom_hook_code_path)

    await asyncio.gather(*[remove_local_nonexistent_object(path) for path in paths])

    del_dirs(base_path)


async def determine_object_destination(
    object: dict,
    object_type: str,
    org_path: Path,
    mapping: dict,
    sources: dict,
    targets: dict,
):
    if object["id"] in targets[object_type + "s"] or await find_object_in_project(
        object, org_path / settings.TARGET_DIRNAME / (object_type + "s")
    ):
        destination = settings.TARGET_DIRNAME
    # Cross-org migration means that there is no target dir in this project
    # Both organizations = projects only have the source dir
    elif (
        not settings.IS_PROJECT_IN_SAME_ORG
        or object["id"] in sources[object_type + "s"]
    ):
        destination = settings.SOURCE_DIRNAME
    else:
        object_name, object_id = object["name"], object["id"]
        user_decision = Confirm(
            f'Should the {object_type} "{object_name}" ({object_id}) be in {settings.SOURCE_DIRNAME}? Otherwise, it will be understood as {settings.TARGET_DIRNAME}.'
        )
        destination = (
            settings.SOURCE_DIRNAME if user_decision else settings.TARGET_DIRNAME
        )

    return destination


async def find_object_in_project(object: dict, base_path: Path):
    file_name = templatize_name_id(object["name"], object["id"])
    return (
        await (base_path / file_name).exists()
        or await (base_path / (file_name + ".json")).exists()
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


def create_formula_directory_path(schema_path: Path, schema: dict):
    return (
        schema_path.parent
        / f"{settings.FORMULA_DIR_PREFIX}{templatize_name_id(schema['name'], schema['id'])}"
    )


async def create_formula_file(path: Path, code: str):
    await write_str(path, code)
