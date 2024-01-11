import copy
from anyio import Path
import os
import shutil
from rich.prompt import Confirm

from rossum_api.models import Workspace, Hook, Schema, Queue, Inbox
from project_rossum_deploy.commands.download.mapping import create_empty_mapping
from project_rossum_deploy.commands.migrate.helpers import is_org_targetting_itself

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import templatize_name_id


async def delete_current_configuration(org_path: Path):
    # We do not delete mapping.yaml on purposes
    os.remove(org_path / "organization.json")
    spaces = [settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]
    paths_to_delete = ["workspaces", "schemas", "hooks"]
    for space in spaces:
        space_path = org_path / space
        if await space_path.exists():
            for path in paths_to_delete:
                path = space_path / path
                if await path.exists():
                    shutil.rmtree(path)


async def determine_object_destination(
    object: Workspace | Schema | Hook,
    object_type: str,
    org_path: Path,
    mapping: dict,
    sources: dict,
    targets: dict,
):
    if object.id in targets[object_type + "s"] or await find_object_in_project(
        object, org_path / settings.TARGET_DIRNAME / (object_type + "s")
    ):
        destination = settings.TARGET_DIRNAME
    # Cross-org migration means that there is no target dir in this project
    # Both organizations = projects only have the source dir
    elif (
        not is_org_targetting_itself(mapping) or object.id in sources[object_type + "s"]
    ):
        destination = settings.SOURCE_DIRNAME
    else:
        user_decision = Confirm(
            f'Should the {object_type} "{object.name}" ({object.id}) be in {settings.SOURCE_DIRNAME}? Otherwise, it will be understood as {settings.TARGET_DIRNAME}.'
        )
        destination = (
            settings.SOURCE_DIRNAME if user_decision else settings.TARGET_DIRNAME
        )

    return destination


async def find_object_in_project(
    object: Workspace | Queue | Hook | Schema | Inbox, base_path: Path
):
    file_name = templatize_name_id(object.name, object.id)
    return (
        await (base_path / file_name).exists()
        or await (base_path / (file_name + ".json")).exists()
    )


def extract_sources_targets(mapping: dict) -> tuple[dict, dict]:
    if not mapping:
        mapping = create_empty_mapping()

    targets = {
        "workspaces": [],
        "queues": [],
        "inboxes": [],
        "schemas": [],
        "hooks": [],
    }
    sources = copy.deepcopy(targets)

    targets["organization"] = mapping["organization"]["target"]
    sources["organization"] = mapping["organization"]["id"]

    for ws in mapping["organization"]["workspaces"]:
        sources["workspaces"].append(ws["id"])
        if ws["target"]:
            targets["workspaces"].append(ws["target"])

        for q in ws["queues"]:
            sources["queues"].append(q["id"])
            if q["target"]:
                targets["queues"].append(q["target"])

            sources["inboxes"].append(q["inbox"]["id"])
            if q["inbox"] and q["inbox"]["target"]:
                targets["inboxes"].append(q["inbox"]["target"])

    for schema in mapping["organization"]["schemas"]:
        sources["schemas"].append(schema["id"])
        if schema["target"]:
            targets["schemas"].append(schema["target"])

    for hook in mapping["organization"]["hooks"]:
        sources["hooks"].append(hook["id"])
        if hook["target"]:
            targets["hooks"].append(hook["target"])

    return sources, targets
