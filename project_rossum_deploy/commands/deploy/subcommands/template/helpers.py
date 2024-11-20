from copy import deepcopy
from project_rossum_deploy.commands.deploy.subcommands.run.attribute_override import (
    create_regex_override_syntax,
)
from project_rossum_deploy.common.read_write import read_json
from pydantic import BaseModel
import questionary
from anyio import Path

from project_rossum_deploy.utils.consts import display_error, display_warning, settings
from project_rossum_deploy.utils.functions import (
    extract_id_from_url,
    find_all_hook_paths_in_destination,
    find_object_by_id,
    templatize_name_id,
)


def create_deploy_file_template():
    # This is done to control the order of the keys
    return f"""\
# The API URL where changes should be deployed (e.g., https://my-org.rossum.app/api/v1)
# The organization's ID is determined automatically based on the token / user credentials.
{settings.DEPLOY_KEY_TARGET_URL}:
# Which local folder is considered to be the source (takes JSON objects from there)
{settings.DEPLOY_KEY_SOURCE_DIR}:

# [Optional] Which local folder is considered to be the target (takes URL and credentials if found)
{settings.DEPLOY_KEY_TARGET_DIR}:
# [Optional] API URL for the source organization (otherwise taken from the source dir config.yaml)
{settings.DEPLOY_KEY_SOURCE_URL}:

# User ID to use as the hook owner (unnecessary if using username+password credentials for target)
{settings.DEPLOY_KEY_TOKEN_OWNER}:

# [Automatic] Marks the deploy file as used and validates that another deploy is into the same org
{settings.DEPLOY_KEY_DEPLOYED_ORG_ID}:

# Define anchors in the following way:
# x_any_name: &anchor_name
#     name: Name from Variable
#     another_attr: 4
# You can then use them in the objects by adding '<<: *anchor_name'

# Update attributes of target organization with those from source organization
{settings.DEPLOY_KEY_PATCH_TARGET_ORG}: true

workspaces:

queues:

hooks:

unselected_hooks: # List hook IDs that should not be deployed, even if they belong to selected queues
"""


async def prepare_choices(
    paths: list[Path], preselected_ids: list = None, preselect_all: bool = False
):
    if not preselected_ids:
        preselected_ids = []
    choices = []

    for path in paths:
        object = await read_json(path)
        name, id = object.get("name", ""), object.get("id", "")
        if not id:
            continue
        choice = questionary.Choice(
            title=f"{name} [{id}]" if name else id,
            value={**object, "path": path},
            checked=preselect_all or id in preselected_ids,
        )
        choices.append(choice)

    return sorted(choices, key=lambda choice: choice.value["id"])


async def get_token_owner_from_user(default: str = ""):
    # YAML can have an explicit None, overwrite
    if default is None:
        default = ""
    token_owner = await questionary.text(
        "What is the token owner user ID (can be empty for same-org target):",
        default=default,
    ).ask_async()

    try:
        if not token_owner:
            return token_owner
        return int(token_owner)
    except Exception:
        display_error("Invalid ID (not an int, please try again).")
        return await get_token_owner_from_user(default=default)


async def get_dir_and_subdir_from_user(org_path: Path, type: str, default: str = None):
    dir_candidates = [
        dir_path
        async for dir_path in org_path.iterdir()
        if await dir_path.is_dir() and str(dir_path) not in settings.DEPLOY_IGNORED_DIRS
    ]
    dir_choices = [questionary.Choice(title=str(path)) for path in dir_candidates]
    # Target dirname is not required (it might not exist unlike the source one)
    if type == settings.TARGET_DIRNAME:
        dir_choices.append(questionary.Choice(title="N/A", value=""))

    # Reset default if it is not found in the current options
    if default not in [choice.title for choice in dir_choices]:
        default = None

    selected_dir = await questionary.select(
        f"Which folder is the {type}?", choices=dir_choices, default=default
    ).ask_async()

    if not selected_dir:
        return ""

    subdir_candidates = [
        subdir_path
        async for subdir_path in (org_path / selected_dir).iterdir()
        if await subdir_path.is_dir()
    ]
    subdir_choices = [questionary.Choice(title=str(path)) for path in subdir_candidates]

    # Reset default if it is not found in the current options
    if default not in [choice.title for choice in subdir_choices]:
        default = None

    selected_subdir = await questionary.select(
        f"Which subfolder is the {type}?",
        choices=subdir_choices,
        default=default,
    ).ask_async()

    return selected_subdir


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


DEFAULT_TARGETS = [{"id": None}]


def prepare_deploy_file_objects(
    objects: list[dict],
    include_path: bool = False,
    objects_in_previous_file: list[dict] = [],
):
    previous_objects_by_id = {
        object["id"]: object for object in objects_in_previous_file
    }

    deploy_objects = []
    for object in objects:
        deploy_representation = {
            "id": object["id"],
            "name": object["name"],
            settings.DEPLOY_KEY_BASE_PATH: str(object["path"].parent.parent.parent),
            settings.DEPLOY_KEY_TARGETS: previous_objects_by_id.get(
                object["id"], {}
            ).get(settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)),
        }
        if not include_path:
            deploy_representation.pop(settings.DEPLOY_KEY_BASE_PATH)
        deploy_objects.append(deploy_representation)
    return deploy_objects


def prepare_subqueue_deploy_file_object(
    object: dict,
    previous_object: dict = {},
):
    deploy_representation = {
        "id": object["id"],
        settings.DEPLOY_KEY_TARGETS: previous_object.get(
            settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)
        ),
    }
    return deploy_representation


async def get_workspaces_from_user(
    source_path: Path,
    interactive: bool,
    previous_deploy_file_workspaces: list[dict] = None,
):
    if not previous_deploy_file_workspaces:
        previous_deploy_file_workspaces = []
    selected_ws_ids = [ws["id"] for ws in previous_deploy_file_workspaces]
    ws_paths = await find_ws_paths_for_dir(source_path)
    ws_choices = await prepare_choices(
        paths=[ws_path / "workspace.json" for ws_path in ws_paths],
        preselected_ids=selected_ws_ids,
    )
    deploy_file_workspaces = [ws.value for ws in ws_choices if ws.checked]
    if interactive or not selected_ws_ids:
        deploy_file_workspaces = await questionary.checkbox(
            "Select WS:", choices=ws_choices
        ).ask_async()

    return prepare_deploy_file_objects(
        objects=deploy_file_workspaces,
        objects_in_previous_file=previous_deploy_file_workspaces,
    ), [ws["path"] for ws in deploy_file_workspaces]


async def get_queues_from_user(
    deploy_ws_paths: list[dict],
    interactive: bool,
    previous_deploy_file_queues: list[dict] = None,
):
    if not previous_deploy_file_queues:
        previous_deploy_file_queues = []
    # TODO: let user select extra queues not in the WS already selected
    selected_queue_ids = [queue["id"] for queue in previous_deploy_file_queues]
    queue_paths = await find_queue_paths_for_workspaces(deploy_ws_paths)
    if not queue_paths:
        display_error("No queues in the selected workspaces.")
        return []

    # If there are no preselected queues, assume the file is being created and preselect everything
    queue_choices = await prepare_choices(
        queue_paths,
        preselected_ids=selected_queue_ids,
        preselect_all=len(selected_queue_ids) == 0,
    )
    deploy_file_queues = [queue.value for queue in queue_choices if queue.checked]
    if interactive or not selected_queue_ids:
        deploy_file_queues = await questionary.checkbox(
            "Modify selection of the queues or just continue:", choices=queue_choices
        ).ask_async()

    selected_queues = deploy_file_queues
    deploy_file_queues = prepare_deploy_file_objects(
        deploy_file_queues,
        include_path=True,
        objects_in_previous_file=previous_deploy_file_queues,
    )

    # TODO: functions for paths for schemas and inboxes
    previous_queues_by_id = {
        object["id"]: object for object in previous_deploy_file_queues
    }
    for queue in deploy_file_queues:
        # No point letting the user select a schema or inbox, each queue should just get its schema
        schema_path = (
            Path(queue[settings.DEPLOY_KEY_BASE_PATH])
            / "queues"
            / templatize_name_id(queue["name"], queue["id"])
            / "schema.json"
        )
        if not (await schema_path.exists()):
            continue
        schema_object = await read_json(schema_path)

        previous_schema = previous_queues_by_id.get(queue["id"], {}).get("schema", {})

        deploy_schema_object = prepare_subqueue_deploy_file_object(
            object=schema_object, previous_object=previous_schema
        )
        queue["schema"] = deploy_schema_object

        inbox_path = (
            Path(queue[settings.DEPLOY_KEY_BASE_PATH])
            / "queues"
            / templatize_name_id(queue["name"], queue["id"])
            / "inbox.json"
        )
        if not (await inbox_path.exists()):
            continue
        inbox_object = await read_json(inbox_path)

        previous_inbox = previous_queues_by_id.get(queue["id"], {}).get("inbox", {})

        deploy_inbox_object = prepare_subqueue_deploy_file_object(
            object=inbox_object, previous_object=previous_inbox
        )
        queue["inbox"] = deploy_inbox_object

    return deploy_file_queues, selected_queues


async def get_hooks_from_user(
    source_path: Path,
    queues: list[dict],
    interactive: bool,
    previous_deploy_file_hooks: list[dict] = None,
    unselected_hook_ids: list[int] = None,
):
    if not previous_deploy_file_hooks:
        previous_deploy_file_hooks = []
    if not unselected_hook_ids:
        unselected_hook_ids = []
    selected_hook_ids = [hook["id"] for hook in previous_deploy_file_hooks]
    hook_ids_for_selected_queues = [
        hook["id"] for hook in await find_hooks_for_queues(source_path, queues)
    ]
    # Take all hooks for the selected queues and any extra hooks in the preexisting file
    # Automatically remove hooks that were previously unselected by the user (during previous deploy file creation)
    preselected_hook_ids = (
        set(hook_ids_for_selected_queues)
        .union(selected_hook_ids)
        .difference(unselected_hook_ids)
    )
    hook_paths = await find_all_hook_paths_in_destination(source_path)

    hook_choices = await prepare_choices(
        paths=[hook_path for hook_path in hook_paths],
        preselected_ids=list(preselected_hook_ids),
    )
    deploy_file_hooks = [hook.value for hook in hook_choices if hook.checked]
    if interactive or not selected_hook_ids:
        deploy_file_hooks = await questionary.checkbox(
            "Modify selection of the hooks:", choices=hook_choices
        ).ask_async()
    selected_hooks = prepare_deploy_file_objects(
        objects=deploy_file_hooks, objects_in_previous_file=previous_deploy_file_hooks
    )
    # Automatically unselected all hooks that belonged to selected queues, but the user did not select them
    unselected_hooks = list(
        set(hook_ids_for_selected_queues)
        .union(unselected_hook_ids)
        .difference([hook["id"] for hook in deploy_file_hooks])
    )
    return selected_hooks, unselected_hooks


class AttributeOverride(BaseModel):
    object_types: list[str]
    attribute: str
    value: str


async def get_attribute_overrides_from_user():
    override_options = ["workspaces", "queues", "hooks"]
    overrides = []
    while await questionary.confirm(
        "Do you want to add a regex attribute override?", default=True
    ).ask_async():
        override_objects = await questionary.checkbox(
            "Select objects:",
            choices=[questionary.Choice(title=option) for option in override_options],
        ).ask_async()
        override_attribute = await questionary.text(
            "Input attribute/JMESPath:"
        ).ask_async()
        # TODO: escaping test
        override_source_regex = await questionary.text(
            "Input regex to override (empty value will be understood as 'replace everything'):"
        ).ask_async()
        override_target = await questionary.text(
            "Input new string (e.g., 'PROD'):"
        ).ask_async()

        overrides.append(
            AttributeOverride(
                object_types=override_objects,
                attribute=override_attribute,
                value=create_regex_override_syntax(
                    override_source_regex, override_target
                )
                if override_source_regex
                else override_target,
            )
        )
    return overrides


def add_override_to_deploy_file_objects(
    override: AttributeOverride, root_deploy_file_object: dict
):
    for object_type in override.object_types:
        if object_type not in root_deploy_file_object:
            display_warning(
                f'Could not find object type "{object_type}" in the deploy file'
            )
            continue

        for object in root_deploy_file_object[object_type]:
            add_override_to_deploy_file_object(override=override, object=object)


def add_override_to_deploy_file_object(override: AttributeOverride, object: dict):
    for target in object.get(settings.DEPLOY_KEY_TARGETS, []):
        object_overrides = target.get(settings.DEPLOY_KEY_OVERRIDES, {})

        object_overrides[override.attribute] = override.value

        if settings.DEPLOY_KEY_OVERRIDES not in target:
            target[settings.DEPLOY_KEY_OVERRIDES] = object_overrides
