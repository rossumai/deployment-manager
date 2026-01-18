from copy import deepcopy
from itertools import zip_longest
from typing import Any

import questionary
from anyio import Path
from pydantic import BaseModel

from deployment_manager.commands.deploy.subcommands.run.attribute_override import create_regex_override_syntax
from deployment_manager.common.read_write import read_object_from_json, read_prd_project_config
from deployment_manager.utils.consts import CustomResource, display_error, display_warning, settings
from deployment_manager.utils.functions import (
    extract_id_from_url,
    find_all_hook_paths_in_destination,
    find_object_by_id,
    templatize_name_id,
)
from rossum_api.api_client import Resource


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
{settings.DEPLOY_KEY_PATCH_TARGET_ORG}: false

workspaces:

queues:

hooks:

unselected_hooks: # List hook IDs that should not be deployed, even if they belong to selected queues
"""


async def prepare_choices(paths: list[Path], preselected_ids: list = None, preselect_all: bool = False):
    if not preselected_ids:
        preselected_ids = []
    choices = []

    for path in paths:
        object = await read_object_from_json(path)
        name, id = object.get("name", ""), object.get("id", "")
        if not id:
            continue
        choice = questionary.Choice(
            title=f"{name} ({id})" if name else id,
            value={**object, "path": path},
            checked=preselect_all or id in preselected_ids,
        )
        choices.append(choice)

    return sorted(choices, key=lambda choice: choice.value["id"])


async def get_dir_from_user(project_path: Path, type: str, config: dict, default: str = None):
    dir_candidates = [
        dir_path
        for dir_path in config.get(settings.CONFIG_KEY_DIRECTORIES, {}).keys()
        if await (Path(project_path) / dir_path).exists()
    ]

    dir_choices = [questionary.Choice(title=str(Path(project_path / path))) for path in dir_candidates]
    # Target dirname is not required (it might not exist unlike the source one)
    if type.casefold() == settings.TARGET_DIRNAME:
        dir_choices.append(questionary.Choice(title="N/A", value=""))

    # Reset default if it is not found in the current options
    if default not in [choice.title for choice in dir_choices]:
        default = None

    selected_dir = await questionary.select(
        f"Which folder is the {type}?", choices=dir_choices, default=default
    ).ask_async()

    return selected_dir


async def get_dir_and_subdir_from_user(project_path: Path, type: str, default: str = ""):
    config = await read_prd_project_config(project_path)

    if not config:
        return ""

    if not default:
        default = ""

    source_dir = default.split("/")[0]

    selected_dir = await get_dir_from_user(project_path=project_path, type=type, default=source_dir, config=config)
    if not selected_dir:
        return ""

    subdir_candidates = [
        subdir_path
        for subdir_path in config.get(settings.CONFIG_KEY_DIRECTORIES, {})
        .get(selected_dir, {})
        .get(settings.CONFIG_KEY_SUBDIRECTORIES, {})
        .keys()
        if await (Path(selected_dir) / subdir_path).exists()
    ]
    subdir_choices = [questionary.Choice(title=str(Path(selected_dir) / path)) for path in subdir_candidates]

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
    all_hooks = [{**await read_object_from_json(hook_path), "path": hook_path} for hook_path in hook_paths]
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
            queue_path async for queue_path in (ws_path / "queues").iterdir() if await queue_path.is_dir()
        ]
        for ws_queue_path in ws_queue_paths:
            queue_path_to_file = ws_queue_path / "queue.json"
            if await queue_path_to_file.exists():
                queue_paths.append(queue_path_to_file)

    return queue_paths


async def find_ws_paths_for_dir(base_dir: Path):
    return [
        workspace_path
        async for workspace_path in (base_dir / Resource.Workspace.value).iterdir()
        if await workspace_path.is_dir()
    ]


async def find_rule_paths_for_dir(base_dir: Path):
    return [rule_path async for rule_path in (base_dir).iterdir()]


async def find_rule_template_paths_for_dir(base_dir: Path):
    rule_template_dir = base_dir / CustomResource.RuleTemplate.value
    if not (await rule_template_dir.exists()):
        return []
    return [rule_path async for rule_path in (rule_template_dir).iterdir() if await rule_path.is_file()]


DEFAULT_TARGETS = [{"id": None}]


def prepare_deploy_file_objects(
    objects: list[dict],
    include_path: bool = False,
    extra_attributes: dict = {},
    objects_in_previous_file: list[dict] = [],
):
    previous_objects_by_id = {object["id"]: object for object in objects_in_previous_file}

    deploy_objects = []
    for object in objects:
        previous_object = previous_objects_by_id.get(object["id"], {})
        deploy_representation = {
            **previous_object,
            "id": object["id"],
            "name": object["name"],
            **{key: previous_object.get(key, value) for key, value in extra_attributes.items()},
            settings.DEPLOY_KEY_BASE_PATH: str(object["path"].parent.parent.parent),
            settings.DEPLOY_KEY_TARGETS: previous_objects_by_id.get(object["id"], {}).get(
                settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)
            ),
        }
        if not include_path:
            deploy_representation.pop(settings.DEPLOY_KEY_BASE_PATH)
        deploy_objects.append(deploy_representation)
    return deploy_objects


def prepare_subqueue_deploy_file_object(
    object: dict,
    previous_object: dict = {},
    include_name: bool = False,
):
    deploy_representation = {
        **previous_object,
        "id": object["id"],
        settings.DEPLOY_KEY_TARGETS: previous_object.get(settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)),
    }
    if include_name:
        deploy_representation["name"] = object["name"]

    return deploy_representation


# TODO: generalize functions (also used in document.py and for deploy template, wrapper will create deploy objects)
async def get_workspaces_from_user(
    source_path: Path,
    interactive: bool,
    previous_deploy_file_workspaces: list[dict] = None,
):
    if not previous_deploy_file_workspaces:
        previous_deploy_file_workspaces = []
    selected_ws_ids = [ws["id"] for ws in previous_deploy_file_workspaces]
    ws_paths = await find_ws_paths_for_dir(source_path)
    ws_paths = [ws_path / "workspace.json" for ws_path in ws_paths if await (ws_path / "workspace.json").exists()]
    if not ws_paths:
        display_warning("No workspaces in the selected subdir.")
        return [], []

    ws_choices = await prepare_choices(
        paths=ws_paths,
        preselected_ids=selected_ws_ids,
    )
    deploy_file_workspaces = [ws.value for ws in ws_choices if ws.checked]
    if interactive or not selected_ws_ids:
        deploy_file_workspaces = await questionary.checkbox("Select workspaces:", choices=ws_choices).ask_async()

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
        display_warning("No queues in the selected workspaces.")
        return [], []

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
        extra_attributes={settings.DEPLOY_KEY_IGNORE_DEPLOY_WARNINGS: False},
        objects_in_previous_file=previous_deploy_file_queues,
    )

    previous_queues_by_id = {object["id"]: object for object in previous_deploy_file_queues}
    for queue in deploy_file_queues:
        # No point letting the user select a schema or inbox, each queue should just get its schema
        await get_schema_for_queue(queue=queue, previous_queues_by_id=previous_queues_by_id)
        if schema := queue.get(settings.DEPLOY_KEY_SCHEMA, None):
            await get_rules_for_schema(
                schema=schema,
                queue=queue,
                previous_queues_by_id=previous_queues_by_id,
            )
        await get_inbox_for_queue(queue=queue, previous_queues_by_id=previous_queues_by_id)

    return deploy_file_queues, selected_queues


async def get_schema_for_queue(queue: dict, previous_queues_by_id: dict):
    schema_path = (
        Path(queue[settings.DEPLOY_KEY_BASE_PATH])
        / settings.DEPLOY_KEY_QUEUES
        / templatize_name_id(queue["name"], queue["id"])
        / "schema.json"
    )

    if not (await schema_path.exists()):
        display_warning(
            f'No schema found for queue [green]{templatize_name_id(queue["name"], queue["id"])}[/green] - you will not be able to release the queue without providing a schema'
        )
        return

    schema_object = await read_object_from_json(schema_path)

    previous_schema = previous_queues_by_id.get(queue["id"], {}).get(settings.DEPLOY_KEY_SCHEMA, {})

    deploy_schema_object = prepare_subqueue_deploy_file_object(object=schema_object, previous_object=previous_schema)
    queue[settings.DEPLOY_KEY_SCHEMA] = deploy_schema_object


async def get_rules_for_schema(queue: dict, schema: dict, previous_queues_by_id: dict):
    rules_path = (
        Path(queue[settings.DEPLOY_KEY_BASE_PATH])
        / settings.DEPLOY_KEY_QUEUES
        / templatize_name_id(queue["name"], queue["id"])
        / settings.RULES_DIR_NAME
    )

    if not (await rules_path.exists()):
        return

    previous_rules = (
        previous_queues_by_id.get(queue["id"], {})
        .get(settings.DEPLOY_KEY_SCHEMA, {})
        .get(settings.DEPLOY_KEY_RULES, [])
    )
    deploy_rule_objects = []
    for rule_path in await find_rule_paths_for_dir(rules_path):
        rule_object = await read_object_from_json(rule_path)

        previous_rule = find_rule(rules=previous_rules, rule_id=rule_object["id"])
        deploy_rule_object = prepare_subqueue_deploy_file_object(
            object=rule_object, previous_object=previous_rule, include_name=True
        )
        deploy_rule_objects.append(deploy_rule_object)

    schema[settings.DEPLOY_KEY_RULES] = deploy_rule_objects


async def get_inbox_for_queue(queue: dict, previous_queues_by_id: dict):
    inbox_path = (
        Path(queue[settings.DEPLOY_KEY_BASE_PATH])
        / settings.DEPLOY_KEY_QUEUES
        / templatize_name_id(queue["name"], queue["id"])
        / "inbox.json"
    )

    if not (await inbox_path.exists()):
        return

    inbox_object = await read_object_from_json(inbox_path)

    previous_inbox = previous_queues_by_id.get(queue["id"], {}).get(settings.DEPLOY_KEY_INBOX, {})

    deploy_inbox_object = prepare_subqueue_deploy_file_object(object=inbox_object, previous_object=previous_inbox)
    queue[settings.DEPLOY_KEY_INBOX] = deploy_inbox_object


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
    hook_ids_for_selected_queues = [hook["id"] for hook in await find_hooks_for_queues(source_path, queues)]
    # Take all hooks for the selected queues and any extra hooks in the preexisting file
    # Automatically remove hooks that were previously unselected by the user (during previous deploy file creation)
    preselected_hook_ids = set(hook_ids_for_selected_queues).union(selected_hook_ids).difference(unselected_hook_ids)
    hook_paths = await find_all_hook_paths_in_destination(source_path)
    if not hook_paths:
        display_warning("No hooks in the selected subdir.")
        return [], []

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


def check_input_integer(input: Any):
    try:
        if int(input):
            return True
    except Exception:
        return "Invalid integer"


async def get_multi_targets_from_user(deploy_file_object: dict):
    if not await questionary.confirm(
        "Do you want to specify more than one target for some of the objects?",
        default=False,
    ).ask_async():
        return

    multi_target_options = [
        settings.DEPLOY_KEY_WORKSPACES,
        settings.DEPLOY_KEY_QUEUES,
        settings.DEPLOY_KEY_HOOKS,
    ]

    for object_type in multi_target_options:
        objects = deploy_file_object.get(object_type, [])
        if not len(objects):
            continue
        while await questionary.confirm(
            f"Do you want to add multiple targets for {object_type.upper()}?",
            default=False,
        ).ask_async():
            object_choices = [
                questionary.Choice(
                    title=f"{object.get('name', 'no-name')} ({object.get('id', 'no-id')})",
                    value=object,
                )
                for object in objects
            ]
            selected_objects = await questionary.checkbox("Select objects:", choices=object_choices).ask_async()
            target_count = await questionary.text(
                "Specify number of targets:",
                validate=lambda x: check_input_integer(x),
            ).ask_async()

            for selected_object in selected_objects:
                add_multi_targets_to_object(selected_object, target_count)

                # Automatically mirror target count for queue's inbox and schema
                if object_type == settings.DEPLOY_KEY_QUEUES:
                    schema = selected_object.get(settings.DEPLOY_KEY_SCHEMA, None)
                    if schema:
                        add_multi_targets_to_object(schema, target_count)
                        rules = schema.get(settings.DEPLOY_KEY_RULES, [])
                        if rules:
                            for rule in rules:
                                add_multi_targets_to_object(rule, target_count)

                    inbox = selected_object.get(settings.DEPLOY_KEY_INBOX, None)
                    if inbox:
                        add_multi_targets_to_object(inbox, target_count)


def add_multi_targets_to_object(object, target_count: int):
    previous_targets = object.get(settings.DEPLOY_KEY_TARGETS, [])
    new_multi_targets = []
    for _ in range(int(target_count)):
        # Copy explicitly to have different memory objects
        new_multi_targets.extend(deepcopy(DEFAULT_TARGETS))
    object[settings.DEPLOY_KEY_TARGETS] = [
        *previous_targets,
        *new_multi_targets,
    ]


class AttributeOverride(BaseModel):
    object_types: list[str]
    attribute: str
    value: str


async def get_attribute_overrides_from_user():
    override_options = [
        settings.DEPLOY_KEY_WORKSPACES,
        settings.DEPLOY_KEY_QUEUES,
        settings.DEPLOY_KEY_HOOKS,
    ]
    overrides = []
    while await questionary.confirm("Do you want to add a regex attribute override?", default=True).ask_async():
        override_objects = await questionary.checkbox(
            "Select objects:",
            choices=[questionary.Choice(title=option) for option in override_options],
        ).ask_async()
        override_attribute = await questionary.text("Input attribute/JMESPath:").ask_async()
        # TODO: escaping test
        override_source_regex = await questionary.text(
            "Input source REGEX to override (empty value will be understood as 'replace everything'):"
        ).ask_async()
        override_target = await questionary.text("Input new STRING (e.g., 'PROD'):").ask_async()

        overrides.append(
            AttributeOverride(
                object_types=override_objects,
                attribute=override_attribute,
                value=(
                    create_regex_override_syntax(override_source_regex, override_target)
                    if override_source_regex
                    else override_target
                ),
            )
        )
    return overrides


async def get_secrets_from_user(deploy_file_object: dict, previous_secrets_file: dict):
    hooks = deploy_file_object.get(settings.DEPLOY_KEY_HOOKS, [])
    object_choices = [
        questionary.Choice(
            title=f"{hook.get('name', 'no-name')} ({hook.get('id', 'no-id')})",
            value=hook,
            checked=templatize_name_id(hook.get("name", "no-name"), hook.get("id", "no-id"))
            in previous_secrets_file.keys(),
        )
        for hook in hooks
    ]

    if not object_choices:
        return {}

    selected_hooks = await questionary.checkbox("Select hooks for secrets:", choices=object_choices).ask_async()

    secrets = {}

    for selected_hook in selected_hooks:
        key = templatize_name_id(selected_hook.get("name", "no-name"), selected_hook.get("id", "no-id"))
        # Preserve previous secrets and create empty dicts for new entries
        secrets[key] = {**previous_secrets_file.get(key, {})}

    return secrets


def add_override_to_deploy_file_objects(override: AttributeOverride, root_deploy_file_object: dict):
    for object_type in override.object_types:
        if object_type not in root_deploy_file_object:
            display_warning(f'Could not find object type "{object_type}" in the deploy file. Skipping.')
            continue

        for object in root_deploy_file_object[object_type]:
            add_override_to_deploy_file_object(override=override, object=object)


def add_override_to_deploy_file_object(override: AttributeOverride, object: dict):
    for target in object.get(settings.DEPLOY_KEY_TARGETS, []):
        object_overrides = target.get(settings.DEPLOY_KEY_OVERRIDES, {})

        object_overrides[override.attribute] = override.value

        if settings.DEPLOY_KEY_OVERRIDES not in target:
            target[settings.DEPLOY_KEY_OVERRIDES] = object_overrides


def add_targets_from_mapping(mapping: dict, deploy_file: dict):
    org_targets = mapping["organization"].get("targets", [])
    if org_targets:
        target_org_id = org_targets[0].get("target_id", None)
        deploy_file[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = target_org_id

    mapping_workspaces = mapping["organization"]["workspaces"]
    deploy_workspaces = deploy_file.get(settings.DEPLOY_KEY_WORKSPACES, [])
    add_targets_for_objects(
        mapping_objects=mapping_workspaces,
        deploy_objects=deploy_workspaces,
        object_type=settings.DEPLOY_KEY_WORKSPACES,
    )

    mapping_queues = []
    for mapping_ws in mapping_workspaces:
        mapping_queues.extend(mapping_ws.get("queues", []))
    deploy_queues = deploy_file.get(settings.DEPLOY_KEY_QUEUES, [])
    add_targets_for_objects(
        mapping_objects=mapping_queues,
        deploy_objects=deploy_queues,
        object_type=settings.DEPLOY_KEY_QUEUES,
    )

    mapping_hooks = mapping["organization"]["hooks"]
    deploy_hooks = deploy_file.get(settings.DEPLOY_KEY_HOOKS, [])
    add_targets_for_objects(
        mapping_objects=mapping_hooks,
        deploy_objects=deploy_hooks,
        object_type=settings.DEPLOY_KEY_HOOKS,
    )

    mapping_inboxes = []
    for mapping_queue in mapping_queues:
        if mapping_inbox := mapping_queue.get("inbox", None):
            mapping_inboxes.append(mapping_inbox)
    deploy_inboxes = []
    for deploy_queue in deploy_queues:
        if deploy_inbox := deploy_queue.get(settings.DEPLOY_KEY_INBOX, None):
            deploy_inboxes.append(deploy_inbox)
    add_targets_for_objects(
        mapping_objects=mapping_inboxes,
        deploy_objects=deploy_inboxes,
        object_type=settings.DEPLOY_KEY_INBOX,
    )

    mapping_schemas = mapping["organization"]["schemas"]
    deploy_schemas = []
    for deploy_queue in deploy_queues:
        if deploy_schema := deploy_queue.get(settings.DEPLOY_KEY_SCHEMA, None):
            deploy_schemas.append(deploy_schema)
    add_targets_for_objects(
        mapping_objects=mapping_schemas,
        deploy_objects=deploy_schemas,
        object_type=settings.DEPLOY_KEY_SCHEMA,
    )


def add_targets_for_objects(mapping_objects: list, deploy_objects: list, object_type: str):
    try:
        mapping_objects_by_id = {ws["id"]: ws for ws in mapping_objects}
        for deploy_object in deploy_objects:
            if deploy_object["id"] not in mapping_objects_by_id:
                continue

            mapping_ws = mapping_objects_by_id[deploy_object["id"]]
            deploy_targets = deploy_object.get(settings.DEPLOY_KEY_TARGETS, [])

            new_deploy_targets = []
            for deploy_target, mapping_target in zip_longest(deploy_targets, mapping_ws.get("targets", [])):
                deploy_target_id = deploy_target.get("id", None)
                mapping_target_id = mapping_target.get("target_id", None)
                deploy_attribute_override = deploy_target.get("attribute_override", {})
                mapping_attribute_override = mapping_target.get("attribute_override", {})
                new_target = {
                    "id": deploy_target_id if deploy_target_id else mapping_target_id,
                    "attribute_override": {
                        **mapping_attribute_override,
                        **deploy_attribute_override,
                    },
                }
                new_deploy_targets.append(new_target)

            deploy_object[settings.DEPLOY_KEY_TARGETS] = new_deploy_targets
    except Exception as e:
        display_error(f"Error while adding targets to deploy file {object_type} ^", e)


def find_rule(rules, rule_id):
    for rule in rules:
        if rule["id"] == rule_id:
            return rule
    return {}


async def get_rule_templates_from_user(
    source_path: Path,
    interactive: bool,
    previous_deploy_file_rule_templates: list[dict] = None,
):
    if not previous_deploy_file_rule_templates:
        previous_deploy_file_rule_templates = []
    selected_rule_template_ids = [template["id"] for template in previous_deploy_file_rule_templates]
    rule_template_paths = await find_rule_template_paths_for_dir(source_path)
    if not rule_template_paths:
        return [], []

    rule_template_choices = await prepare_choices(
        paths=rule_template_paths,
        preselected_ids=selected_rule_template_ids,
    )
    deploy_file_rule_templates = [template.value for template in rule_template_choices if template.checked]
    if interactive or not selected_rule_template_ids:
        deploy_file_rule_templates = await questionary.checkbox(
            f"Select {CustomResource.RuleTemplate.value}:",
            choices=rule_template_choices,
        ).ask_async()

    return prepare_deploy_file_objects(
        objects=deploy_file_rule_templates,
        objects_in_previous_file=previous_deploy_file_rule_templates,
    ), [template["path"] for template in deploy_file_rule_templates]
