import os
from anyio import Path
import shutil
from rich.prompt import Confirm

from rossum_api.models import Workspace, Hook, Schema, Queue, Inbox
from project_rossum_deploy.commands.migrate.helpers import is_org_targetting_itself

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import templatize_name_id


async def delete_current_configuration(org_path: Path, destination: str):
    # We do not delete mapping.yaml on purpose
    destinations = (
        [destination]
        if destination
        else [settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME]
    )
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
