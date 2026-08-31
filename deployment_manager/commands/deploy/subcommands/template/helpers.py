from copy import deepcopy
from itertools import zip_longest
from typing import Any

import questionary
from anyio import Path
from pydantic import BaseModel
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.attribute_override import create_regex_override_syntax
from deployment_manager.commands.deploy.subcommands.run.deploy_objects.email_template_deploy_object import (
    NON_CREATABLE_EMAIL_TEMPLATE_TYPES,
)
from deployment_manager.common.read_write import read_object_from_json, read_prd_project_config
from deployment_manager.utils.consts import display_error, display_warning, settings
from deployment_manager.utils.functions import (
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
{settings.DEPLOY_KEY_PATCH_TARGET_ORG}: false

workspaces:

queues:

hooks:

engines:

rules:

labels:

email_templates:

unselected_hooks: # List hook IDs that should not be deployed, even if they belong to selected queues
"""


async def prepare_choices(
    paths: list[Path],
    preselected_ids: list = None,
    preselect_all: bool = False,
    disabled_reasons: dict = None,
):
    """Build checkbox choices from object JSON files.

    ids in `disabled_reasons` (id -> reason) are checked and disabled: visible but
    not unselectable.
    """
    if not preselected_ids:
        preselected_ids = []
    if not disabled_reasons:
        disabled_reasons = {}
    choices = []

    for path in paths:
        object = await read_object_from_json(path)
        name, id = object.get("name", ""), object.get("id", "")
        if not id:
            continue
        disabled = disabled_reasons.get(id)
        choice = questionary.Choice(
            title=f"{name} ({id})" if name else id,
            value={**object, "path": path},
            checked=disabled is not None or preselect_all or id in preselected_ids,
            disabled=disabled,
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
    """Find all rule JSON files in the top-level rules/ directory."""
    rules_dir = base_dir / settings.RULES_DIR_NAME
    if not await rules_dir.exists():
        return []
    return [
        rule_path
        async for rule_path in rules_dir.iterdir()
        if await rule_path.is_file() and rule_path.name.endswith(".json")
    ]


async def find_label_paths_for_dir(base_dir: Path):
    """Find all label JSON files in the top-level labels/ directory."""
    labels_dir = base_dir / settings.LABELS_DIR_NAME
    if not await labels_dir.exists():
        return []
    return [
        label_path
        async for label_path in labels_dir.iterdir()
        if await label_path.is_file() and label_path.name.endswith(".json")
    ]


async def find_email_template_paths_for_queue(queue_path: Path):
    """Find all email template JSON files for a given queue (the queue's queue.json path)."""
    email_templates_dir = queue_path.parent / settings.EMAIL_TEMPLATES_DIR_NAME
    if not await email_templates_dir.exists():
        return []
    return [
        et_path
        async for et_path in email_templates_dir.iterdir()
        if await et_path.is_file() and et_path.name.endswith(".json")
    ]


async def find_all_email_template_paths_for_dir(base_dir: Path):
    """Find every email template JSON under base_dir (across all workspaces/queues)."""
    if not await (base_dir / Resource.Workspace.value).exists():
        return []
    ws_paths = await find_ws_paths_for_dir(base_dir)
    queue_paths = await find_queue_paths_for_workspaces(ws_paths)
    et_paths = []
    for queue_path in queue_paths:
        et_paths.extend(await find_email_template_paths_for_queue(queue_path))
    return et_paths


async def find_engine_paths_for_dir(base_dir: Path):
    engine_dir = base_dir / Resource.Engine.value
    if not (await engine_dir.exists()):
        return []
    engine_paths = []
    async for engine_subdir in engine_dir.iterdir():
        if await engine_subdir.is_dir():
            engine_json = engine_subdir / "engine.json"
            if await engine_json.exists():
                engine_paths.append(engine_json)
        elif await engine_subdir.is_file() and engine_subdir.name.endswith(".json"):
            engine_paths.append(engine_subdir)
    return engine_paths


async def find_engine_field_paths_for_engine(engine_path: Path):
    """Find all engine field JSON files for a given engine."""
    engine_fields_dir = engine_path.parent / "engine_fields"
    if not await engine_fields_dir.exists():
        return []
    return [
        field_path
        async for field_path in engine_fields_dir.iterdir()
        if await field_path.is_file() and field_path.name.endswith(".json")
    ]


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


def prepare_email_template_deploy_file_objects(
    objects: list[dict],
    objects_in_previous_file: list[dict] = [],
):
    """Email templates live under each queue's email_templates/ dir, so the base_path
    points directly at that dir (unlike top-level objects)."""
    previous_objects_by_id = {object["id"]: object for object in objects_in_previous_file}

    deploy_objects = []
    for object in objects:
        previous_object = previous_objects_by_id.get(object["id"], {})
        deploy_representation = {
            **previous_object,
            "id": object["id"],
            "name": object["name"],
            settings.DEPLOY_KEY_BASE_PATH: str(object["path"].parent),
            settings.DEPLOY_KEY_TARGETS: previous_object.get(settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)),
        }
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


async def find_rules_for_queues(source_path: Path, queues: list[dict]) -> set[int]:
    """Find rule IDs that reference any of the selected queues."""
    rule_paths = await find_rule_paths_for_dir(source_path)
    selected_queue_ids = {queue.get("id") for queue in queues}
    matching_rule_ids = set()

    for rule_path in rule_paths:
        rule_data = await read_object_from_json(rule_path)
        # Skip schema-based rules
        if rule_data.get("schema"):
            continue
        # Check if any of the rule's queues match the selected queues
        rule_queue_urls = rule_data.get("queues", [])
        for queue_url in rule_queue_urls:
            queue_id = extract_id_from_url(queue_url)
            if queue_id and queue_id in selected_queue_ids:
                matching_rule_ids.add(rule_data.get("id"))
                break

    return matching_rule_ids


async def get_rules_from_user(
    source_path: Path,
    queues: list[dict],
    interactive: bool,
    previous_deploy_file_rules: list[dict] = None,
):
    """Get rules from the top-level rules/ directory.

    Returns (deploy_file_rules, selected_rules) where selected_rules are the raw rule
    objects (including their `actions` and `path`) so callers can derive the rules'
    label/email-template dependencies.
    """
    if not previous_deploy_file_rules:
        previous_deploy_file_rules = []
    selected_rule_ids = [rule["id"] for rule in previous_deploy_file_rules]
    rule_paths = await find_rule_paths_for_dir(source_path)
    if not rule_paths:
        return [], []

    # Find rules that reference the selected queues
    rule_ids_for_selected_queues = await find_rules_for_queues(source_path, queues)

    # Filter out rules that use deprecated schema-based assignment
    valid_rule_paths = []
    for rule_path in rule_paths:
        rule_data = await read_object_from_json(rule_path)
        if rule_data.get("schema"):
            display_warning(
                f"Rule '{rule_data.get('name', 'unknown')}' ({rule_data.get('id', 'unknown')}) "
                "uses deprecated schema-based assignment and will be excluded. "
                "Please update the rule to use queue-based assignment."
            )
            continue
        valid_rule_paths.append(rule_path)

    if not valid_rule_paths:
        return [], []

    # Pre-select rules that belong to selected queues (similar to hooks behavior)
    # Also include any previously selected rules
    preselected_rule_ids = rule_ids_for_selected_queues.union(set(selected_rule_ids))

    rule_choices = await prepare_choices(
        paths=valid_rule_paths,
        preselected_ids=list(preselected_rule_ids),
    )
    selected_rules = [rule.value for rule in rule_choices if rule.checked]
    if interactive or not selected_rule_ids:
        selected_rules = await questionary.checkbox("Modify selection of the rules:", choices=rule_choices).ask_async()

    deploy_file_rules = prepare_deploy_file_objects(
        objects=selected_rules, objects_in_previous_file=previous_deploy_file_rules
    )
    return deploy_file_rules, selected_rules


def _rule_required_reasons(rule_required_ids: dict) -> dict:
    """id -> menu reason, e.g. `required by rule(s) 55, 60`."""
    return {
        obj_id: f"required by rule(s) {', '.join(str(rule_id) for rule_id in sorted(rule_ids))}"
        for obj_id, rule_ids in rule_required_ids.items()
    }


def _tag_included_by_rules(entries: list[dict], rule_required_ids: dict):
    """Add `included_by_rules` (before `targets`) to rule-referenced entries; drop stale tags."""
    for entry in entries:
        entry.pop("included_by_rules", None)
        rule_ids = rule_required_ids.get(entry["id"])
        if rule_ids:
            targets = entry.pop(settings.DEPLOY_KEY_TARGETS, None)
            entry["included_by_rules"] = sorted(rule_ids)
            if targets is not None:
                entry[settings.DEPLOY_KEY_TARGETS] = targets


async def select_objects_with_rule_dependencies(
    paths: list[Path],
    prompt_message: str,
    interactive: bool,
    prepare_fn,
    previous_deploy_file_objects: list[dict] = None,
    rule_required_ids: dict = None,
):
    """Shared label/email-template selection.

    Rule-required objects (`rule_required_ids`: id -> {rule_ids}) are forced into the
    selection and tagged `included_by_rules`; previous manual picks stay preselected.
    `prepare_fn` builds the entries (layout differs per type).
    """
    if not previous_deploy_file_objects:
        previous_deploy_file_objects = []
    if not rule_required_ids:
        rule_required_ids = {}
    previous_ids = [obj["id"] for obj in previous_deploy_file_objects]
    # Only preselect manual picks; rule-required ones are forced in via disabled_reasons.
    manual_ids = [obj["id"] for obj in previous_deploy_file_objects if not obj.get("included_by_rules")]
    if not paths:
        return []

    choices = await prepare_choices(
        paths=paths,
        preselected_ids=manual_ids,
        disabled_reasons=_rule_required_reasons(rule_required_ids),
    )
    selected = [choice.value for choice in choices if choice.checked]
    if interactive or not previous_ids:
        selected = await questionary.checkbox(prompt_message, choices=choices).ask_async()

    entries = prepare_fn(objects=selected, objects_in_previous_file=previous_deploy_file_objects)
    _tag_included_by_rules(entries, rule_required_ids)
    return entries


async def get_labels_from_user(
    source_path: Path,
    interactive: bool,
    previous_deploy_file_labels: list[dict] = None,
    rule_required_ids: dict = None,
):
    """Labels from the top-level labels/ directory (org-level, opt-in)."""
    return await select_objects_with_rule_dependencies(
        paths=await find_label_paths_for_dir(source_path),
        prompt_message="Select labels:",
        interactive=interactive,
        prepare_fn=prepare_deploy_file_objects,
        previous_deploy_file_objects=previous_deploy_file_labels,
        rule_required_ids=rule_required_ids,
    )


async def find_creatable_email_template_paths(selected_queues: list[dict]):
    """Collect email template paths for the selected queues, excluding non-creatable
    types (rejection_default, email_with_no_processable_attachments) which are
    auto-created with the queue and cannot be deployed standalone."""
    et_paths = []
    for queue in selected_queues:
        queue_path = queue.get("path")
        if not queue_path:
            continue
        for et_path in await find_email_template_paths_for_queue(queue_path):
            email_template = await read_object_from_json(et_path)
            if email_template.get("type") in NON_CREATABLE_EMAIL_TEMPLATE_TYPES:
                continue
            et_paths.append(et_path)
    return et_paths


async def get_email_templates_from_user(
    selected_queues: list[dict],
    interactive: bool,
    previous_deploy_file_email_templates: list[dict] = None,
    rule_required_ids: dict = None,
):
    """Email templates of the selected queues (they need a parent queue to deploy).

    Rule-required templates in non-selected queues aren't offered here; they're handled
    by get_rule_dependency_objects.
    """
    return await select_objects_with_rule_dependencies(
        paths=await find_creatable_email_template_paths(selected_queues),
        prompt_message="Select email templates:",
        interactive=interactive,
        prepare_fn=prepare_email_template_deploy_file_objects,
        previous_deploy_file_objects=previous_deploy_file_email_templates,
        rule_required_ids=rule_required_ids,
    )


def collect_rule_dependency_ids(selected_rules: list[dict]):
    """Map each label/email-template id referenced by the rules' actions to the set of rule
    ids that reference it."""
    label_rule_ids: dict[int, set] = {}
    email_template_rule_ids: dict[int, set] = {}
    for rule in selected_rules:
        # Schema-based rules are excluded from deploy entirely
        if rule.get("schema"):
            continue
        rule_id = rule.get("id")
        for action in rule.get("actions", []):
            action_type = action.get("type", "")
            payload = action.get("payload", {})
            if action_type in ("add_label", "add_remove_label"):
                for label_url in payload.get("labels", []):
                    label_id = extract_id_from_url(label_url)
                    if label_id:
                        label_rule_ids.setdefault(label_id, set()).add(rule_id)
            elif action_type == "send_email":
                email_template_url = payload.get("email_template")
                email_template_id = extract_id_from_url(email_template_url) if email_template_url else None
                if email_template_id:
                    email_template_rule_ids.setdefault(email_template_id, set()).add(rule_id)
    return label_rule_ids, email_template_rule_ids


async def get_rule_dependency_objects(
    selected_rules: list[dict],
    source_path: Path,
    exclude_label_ids: set = None,
    exclude_email_template_ids: set = None,
    previous_deploy_file_labels: list[dict] = None,
    previous_deploy_file_email_templates: list[dict] = None,
):
    """Entries for the rules' label/email-template dependencies, tagged `included_by_rules`.

    Skips ids in exclude_* (already in the menus) and preserves previous targets so repeat
    deploys don't duplicate. Returns (label_entries, email_template_entries).
    """
    exclude_label_ids = exclude_label_ids or set()
    exclude_email_template_ids = exclude_email_template_ids or set()
    previous_labels_by_id = {obj["id"]: obj for obj in (previous_deploy_file_labels or [])}
    previous_ets_by_id = {obj["id"]: obj for obj in (previous_deploy_file_email_templates or [])}

    label_rule_ids, email_template_rule_ids = collect_rule_dependency_ids(selected_rules)

    # Resolve referenced ids to their local files (id -> object)
    label_objects_by_id = {}
    for path in await find_label_paths_for_dir(source_path):
        obj = await read_object_from_json(path)
        if obj.get("id"):
            label_objects_by_id[obj["id"]] = obj

    et_paths_by_id = {}
    for path in await find_all_email_template_paths_for_dir(source_path):
        obj = await read_object_from_json(path)
        if obj.get("id"):
            et_paths_by_id[obj["id"]] = (path, obj)

    missing = []

    label_entries = []
    for label_id in sorted(label_rule_ids):
        if label_id in exclude_label_ids:
            continue
        obj = label_objects_by_id.get(label_id)
        if not obj:
            missing.append(("label", label_id, label_rule_ids[label_id]))
            continue
        previous = previous_labels_by_id.get(label_id, {})
        label_entries.append(
            {
                "id": label_id,
                "name": obj.get("name", f"label-{label_id}"),
                "included_by_rules": sorted(label_rule_ids[label_id]),
                settings.DEPLOY_KEY_TARGETS: previous.get(settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)),
            }
        )

    email_template_entries = []
    for et_id in sorted(email_template_rule_ids):
        if et_id in exclude_email_template_ids:
            continue
        found = et_paths_by_id.get(et_id)
        if not found:
            missing.append(("email template", et_id, email_template_rule_ids[et_id]))
            continue
        path, obj = found
        # Non-creatable auto types are resolved at deploy time, not deployed as standalone
        if obj.get("type") in NON_CREATABLE_EMAIL_TEMPLATE_TYPES:
            continue
        previous = previous_ets_by_id.get(et_id, {})
        email_template_entries.append(
            {
                "id": et_id,
                "name": obj.get("name", f"email-template-{et_id}"),
                "included_by_rules": sorted(email_template_rule_ids[et_id]),
                settings.DEPLOY_KEY_BASE_PATH: str(path.parent),
                settings.DEPLOY_KEY_TARGETS: previous.get(settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)),
            }
        )

    if missing:
        lines = "\n".join(
            f"  - {kind} {dep_id} (referenced by rules {sorted(rule_ids)})" for kind, dep_id, rule_ids in missing
        )
        display_warning(
            "Some labels/email templates referenced by the selected rules have no local file, so "
            "they won't be listed in the deploy file. They will still be deployed (auto-loaded from "
            f"the source) when the rule is deployed:\n{lines}"
        )

    return label_entries, email_template_entries


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
        settings.DEPLOY_KEY_RULES,
        settings.DEPLOY_KEY_LABELS,
        settings.DEPLOY_KEY_EMAIL_TEMPLATES,
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
        settings.DEPLOY_KEY_RULES,
        settings.DEPLOY_KEY_ENGINES,
        settings.DEPLOY_KEY_LABELS,
        settings.DEPLOY_KEY_EMAIL_TEMPLATES,
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
    object_choices = sorted(
        [
            questionary.Choice(
                title=f"{hook.get('name', 'no-name')} ({hook.get('id', 'no-id')})",
                value=hook,
                checked=templatize_name_id(hook.get("name", "no-name"), hook.get("id", "no-id"))
                in previous_secrets_file.keys(),
            )
            for hook in hooks
        ],
        key=lambda choice: choice.title.casefold(),
    )

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

    mapping_engines = mapping["organization"].get("engines", [])
    deploy_engines = deploy_file.get(settings.DEPLOY_KEY_ENGINES, [])
    add_targets_for_objects(
        mapping_objects=mapping_engines,
        deploy_objects=deploy_engines,
        object_type=settings.DEPLOY_KEY_ENGINES,
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


async def get_engines_from_user(
    source_path: Path,
    interactive: bool,
    previous_deploy_file_engines: list[dict] = None,
):
    if not previous_deploy_file_engines:
        previous_deploy_file_engines = []
    selected_engine_ids = [engine["id"] for engine in previous_deploy_file_engines]
    engine_paths = await find_engine_paths_for_dir(source_path)
    if not engine_paths:
        return [], []

    engine_choices = await prepare_choices(
        paths=engine_paths,
        preselected_ids=selected_engine_ids,
    )
    deploy_file_engines = [engine.value for engine in engine_choices if engine.checked]
    if interactive or not selected_engine_ids:
        deploy_file_engines = await questionary.checkbox(
            f"Select {Resource.Engine.value}:",
            choices=engine_choices,
        ).ask_async()

    prepared_engines = prepare_deploy_file_objects(
        objects=deploy_file_engines,
        objects_in_previous_file=previous_deploy_file_engines,
    )

    previous_engines_by_id = {engine["id"]: engine for engine in previous_deploy_file_engines}
    for engine, prepared_engine in zip(deploy_file_engines, prepared_engines):
        engine_path = engine.get("path")
        engine_field_paths = await find_engine_field_paths_for_engine(engine_path)
        previous_engine = previous_engines_by_id.get(engine["id"], {})
        previous_engine_fields = previous_engine.get("engine_fields", [])

        if engine_field_paths:
            engine_fields = []
            for field_path in engine_field_paths:
                field_data = await read_object_from_json(field_path)
                engine_fields.append({**field_data, "path": field_path})

            prepared_engine["engine_fields"] = prepare_engine_fields_for_deploy(
                engine_fields=engine_fields,
                previous_engine_fields=previous_engine_fields,
            )
        prepared_engine["base_path"] = str(engine_path.parent)

    return prepared_engines, [engine["path"] for engine in deploy_file_engines]


def prepare_engine_fields_for_deploy(engine_fields: list[dict], previous_engine_fields: list[dict] = None):
    """Prepare engine fields for deploy file format."""
    if not previous_engine_fields:
        previous_engine_fields = []
    previous_fields_by_id = {field["id"]: field for field in previous_engine_fields}

    deploy_fields = []
    for field in engine_fields:
        previous_field = previous_fields_by_id.get(field["id"], {})
        deploy_field = {
            **previous_field,
            "id": field["id"],
            "name": field["name"],
            settings.DEPLOY_KEY_TARGETS: previous_field.get(settings.DEPLOY_KEY_TARGETS, deepcopy(DEFAULT_TARGETS)),
        }
        deploy_fields.append(deploy_field)
    return deploy_fields
