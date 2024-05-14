import os
from typing import Any
from anyio import Path
import shutil
from rich.prompt import Confirm

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
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


async def delete_current_configuration(org_path: Path):
    # We do not delete mapping.yaml on purpose
    destinations = [settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]

    paths_to_delete = ["workspaces", "schemas", "hooks", "organization.json"]
    for destination in destinations:
        destination_path = org_path / destination
        if await destination_path.exists():
            for path in paths_to_delete:
                path = destination_path / path
                if await path.exists():
                    if await path.is_file():
                        os.remove(path)
                    else:
                        shutil.rmtree(path)


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


async def create_formula_file(path: Path, code: str):
    await write_str(path, code)
