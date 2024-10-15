from project_rossum_deploy.common.read_write import read_json


import questionary
from anyio import Path

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    extract_id_from_url,
    find_all_hook_paths_in_destination,
    find_all_schema_paths_in_destination,
    find_object_by_id,
)


def create_deploy_file_template(target_org_url: str = None, source_dir: str = None):
    return f"""\
# The API URL where changes should be deployed (e.g., https://my-org.rossum.app/api/v1)
# The organization's ID is determined automatically based on the token / user credentials.
{settings.DEPLOY_TARGET_URL_KEY}: {target_org_url}
# Which local folder is considered to be the source
{settings.DEPLOY_SOURCE_DIR_KEY}: {source_dir}

# Define anchors in the following way:
# x_any_name: &anchor_name
#     name: Name from Variable
#     another_attr: 4
# You can then use them in the objects by adding '<<: *anchor_name'

workspaces:

queues:

hooks:

schemas:

### PRD internal ###
# List IDs of queues that should not be deployed, even if they belong to selected WS
unselected_queues:
"""


async def prepare_choices(paths: list[Path], preselect: bool = False):
    choices = []

    for path in paths:
        object = await read_json(path)
        name, id = object.get("name", ""), object.get("id", "")
        if not id:
            continue
        choice = questionary.Choice(
            title=f"{name} [{id}]" if name else id,
            value={**object, "path": path},
            checked=preselect,
        )
        choices.append(choice)

    return choices


async def get_filename_from_user(org_path: Path, default: str = None):
    deploy_filename: str = await questionary.text(
        "Name for the deploy file:",
        default=default,
    ).ask_async()
    deploy_filepath = org_path / deploy_filename

    if await deploy_filepath.exists():
        overwrite = await questionary.confirm(
            f'File "{deploy_filepath}" already exists. Overwrite?', default=False
        ).ask_async()
        if not overwrite:
            return await get_filename_from_user(org_path)

    return deploy_filepath


async def find_schemas_for_queues(source_path: Path, queues: list[dict]):
    schema_paths = await find_all_schema_paths_in_destination(source_path)
    all_schemas = [
        {**await read_json(schema_path), "path": schema_path}
        for schema_path in schema_paths
    ]

    found_schema_ids = set()
    found_schemas = []

    for queue in queues:
        schema_url = queue.get("schema", None)
        schema_id = extract_id_from_url(schema_url)
        schema = find_object_by_id(schema_id, all_schemas)
        if schema and schema["id"] not in found_schema_ids:
            found_schema_ids.add(schema["id"])
            found_schemas.append(schema)

    return found_schemas


async def find_hooks_for_queues(source_path: Path, queues: list[dict]):
    hook_paths = await find_all_hook_paths_in_destination(source_path)
    all_hooks = [
        {**await read_json(hook_path), "path": hook_path} for hook_path in hook_paths
    ]
    found_hook_ids = set()
    found_hooks = []

    for queue in queues:
        hook_urls = queue.get("hooks", [])
        queue_hook_ids = [extract_id_from_url(hook_url) for hook_url in hook_urls]
        for hook_id in queue_hook_ids:
            hook = find_object_by_id(hook_id, all_hooks)
            if hook and hook["id"] not in found_hook_ids:
                found_hook_ids.add(hook["id"])
                found_hooks.append(hook)

    return found_hooks


async def find_queue_paths_for_workspaces(ws_paths: list[Path]):
    queue_paths = []
    for ws_path in ws_paths:
        if not (await (ws_path / "queues").exists()):
            continue
        ws_queue_paths = [
            queue_path async for queue_path in (ws_path / "queues").iterdir()
        ]
        for ws_queue_path in ws_queue_paths:
            queue_path_to_file = ws_queue_path / "queue.json"
            if await queue_path_to_file.exists():
                queue_paths.append(queue_path_to_file)

    return queue_paths


async def find_ws_paths_for_dir(base_dir: Path):
    return [
        workspace_path
        async for workspace_path in (base_dir / "workspaces").iterdir()
        if await workspace_path.is_dir()
    ]


def prepare_deploy_file_objects(objects: list[dict], include_path: bool = False):
    deploy_objects = []
    for object in objects:
        deploy_representation = {
            "id": object["id"],
            "name": object["name"],
            settings.DEPLOY_BASE_PATH_KEY: str(object["path"].parent.parent.parent),
            "targets": [{"id": None}],
        }
        if not include_path:
            deploy_representation.pop(settings.DEPLOY_BASE_PATH_KEY)
        deploy_objects.append(deploy_representation)
    return deploy_objects
