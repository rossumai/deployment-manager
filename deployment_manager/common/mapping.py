import copy
from math import inf
from typing import Any

from anyio import Path

from deployment_manager.common.read_write import read_yaml, write_yaml
from deployment_manager.utils.consts import settings


def adjust_keys(object: Any, uppercase_fields: list = [], lower: bool = True):
    if isinstance(object, dict):
        lowercased = {}
        for k, v in object.items():
            new_key = k
            if lower and k.lower() in uppercase_fields:
                new_key = k.lower()
            elif not lower and k in uppercase_fields:
                new_key = k.upper()
            lowercased[new_key] = adjust_keys(v, uppercase_fields, lower)
        return lowercased
    elif isinstance(object, list):
        lowercased = []
        for v in object:
            lowercased.append(adjust_keys(v, uppercase_fields, lower))
        return lowercased
    else:
        return object


async def read_mapping(mapping_path: Path):
    if await mapping_path.exists():
        mapping = read_yaml(mapping_path)
        return adjust_keys(mapping, settings.MAPPING_UPPERCASE_FIELDS)

    return None


def get_mapping_key_index(key: str):
    try:
        return settings.MAPPING_KEYS_ORDER.index(key)
    except Exception:
        return inf


def sort_mapping(mapping: dict):
    if isinstance(mapping, list):
        result = []
        for el in mapping:
            result.append(sort_mapping(el))
        return result
    elif isinstance(mapping, dict):
        result = {}
        for k, v in sorted(mapping.items(), key=lambda item: get_mapping_key_index(item[0])):
            result[k] = sort_mapping(v)
        return result
    else:
        return mapping


async def write_mapping(mapping_path: Path, mapping: dict):
    mapping = adjust_keys(mapping, settings.MAPPING_UPPERCASE_FIELDS, lower=False)

    # Python dictionaries are sorted
    mapping = sort_mapping(mapping)

    await write_yaml(mapping_path, mapping)


def create_empty_mapping():
    return {
        "organization": {
            "id": "",
            "name": "",
            "targets": [{"target_id": None}],
            "workspaces": [],
            "hooks": [],
            "schemas": [],
        }
    }


async def create_update_mapping(
    org_path: Path,
    organization: dict,
    workspaces_for_mapping: list[dict],
    hooks_for_mapping: list[dict],
    schemas_for_mapping: list[dict],
    old_mapping: dict,
):
    mapping = create_empty_mapping()

    mapping["organization"]["id"] = organization["id"]
    mapping["organization"]["name"] = organization["name"]

    # Ids of both source and target objects
    # Used to check that a target object was not deleted
    # If yes, ignore old mapping that assigns this target to some left (source) object
    new_ids = []

    for destination, workspace in workspaces_for_mapping:
        new_ids.append(workspace["id"])
        ws_mapping = {
            **get_attributes_for_mapping(workspace),
            "queues": [],
        }
        for q in workspace["queues"]:
            new_ids.append(q["id"])
            if (inbox := q.get("inbox", None)) and (inbox_id := inbox.get("id", None)):
                new_ids.append(inbox_id)

            queue_mapping = {
                **get_attributes_for_mapping(q),
                "inbox": get_attributes_for_mapping(inbox) if inbox else None,
            }
            ws_mapping["queues"].append(queue_mapping)

        # Throw away the mapping, we just want the ids for objects that are targeted by something (based on the old mapping)
        if destination == settings.TARGET_DIRNAME:
            continue

        mapping["organization"]["workspaces"].append(ws_mapping)

    for destination, hook in hooks_for_mapping:
        new_ids.append(hook["id"])
        if destination == settings.TARGET_DIRNAME:
            continue
        mapping["organization"]["hooks"].append(get_attributes_for_mapping(hook))

    for destination, schema in schemas_for_mapping:
        new_ids.append(schema["id"])
        if destination == settings.TARGET_DIRNAME:
            continue
        mapping["organization"]["schemas"].append(get_attributes_for_mapping(schema))

    enrich_mappings_with_existing_attributes(old_mapping=old_mapping, new_mapping=mapping, new_ids=new_ids)

    await write_mapping(org_path / settings.MAPPING_FILENAME, mapping)


def get_attributes_for_mapping(
    object: dict,
):
    return {
        "id": object["id"],
        "name": object["name"],
        "targets": [],
    }


def get_default_targets():
    return [{"target_id": None}]


def index_mappings_by_object_id(sub_mapping: list[dict]):
    indexed = {sm["id"]: sm for sm in sub_mapping}
    return indexed


def enrich_mapping_with_previous_properties(new_sub_mapping: dict, old_sub_mapping: dict):
    if not old_sub_mapping:
        old_sub_mapping = {}
    for k, v in old_sub_mapping.items():
        if k not in new_sub_mapping:
            new_sub_mapping[k] = v


def enrich_mapping_with_previous_targets(new_sub_mapping: dict, old_sub_mapping: dict, new_ids: list):
    old_targets = old_sub_mapping.get("targets", [])
    new_targets = []
    for old_target in old_targets:
        old_target_id = old_target.get("target_id", None)
        if old_target_id is None or old_target_id in new_ids:
            new_targets.append(old_target)

    if not len(new_targets):
        new_targets = get_default_targets()

    new_sub_mapping["targets"] = new_targets


def enrich_mappings_with_existing_attributes(old_mapping: dict, new_mapping: dict, new_ids: list[int]):
    """Use targets from the previous mapping, but only if the target objects were not deleted in Rossum"""

    enrich_mapping_with_previous_properties(new_mapping["organization"], old_mapping["organization"])
    old_org_targets = old_mapping["organization"].get("targets", [])
    if not old_org_targets:
        old_org_targets = [{"target_id": None}]
    new_mapping["organization"]["targets"] = old_org_targets

    old_schema_mappings = index_mappings_by_object_id(old_mapping["organization"]["schemas"])
    for new_schema_mapping in new_mapping["organization"]["schemas"]:
        old_schema_mapping = old_schema_mappings.get(new_schema_mapping["id"], {})
        enrich_mapping_with_previous_properties(new_schema_mapping, old_schema_mapping)

        enrich_mapping_with_previous_targets(
            new_sub_mapping=new_schema_mapping,
            old_sub_mapping=old_schema_mapping,
            new_ids=new_ids,
        )

    old_hook_mappings = index_mappings_by_object_id(old_mapping["organization"]["hooks"])
    for new_hook_mapping in new_mapping["organization"]["hooks"]:
        old_hook_mapping = old_hook_mappings.get(new_hook_mapping["id"], {})
        enrich_mapping_with_previous_properties(new_hook_mapping, old_hook_mapping)

        enrich_mapping_with_previous_targets(
            new_sub_mapping=new_hook_mapping,
            old_sub_mapping=old_hook_mapping,
            new_ids=new_ids,
        )

    old_workspace_mappings = index_mappings_by_object_id(old_mapping["organization"]["workspaces"])
    for new_workspace_mapping in new_mapping["organization"]["workspaces"]:
        old_workspace_mapping = old_workspace_mappings.get(new_workspace_mapping["id"], {})
        enrich_mapping_with_previous_properties(new_workspace_mapping, old_workspace_mapping)

        enrich_mapping_with_previous_targets(
            new_sub_mapping=new_workspace_mapping,
            old_sub_mapping=old_workspace_mapping,
            new_ids=new_ids,
        )

        old_queue_mappings = index_mappings_by_object_id(old_workspace_mapping.get("queues", []))
        for new_queue_mapping in new_workspace_mapping.get("queues", []):
            old_queue_mapping = old_queue_mappings.get(new_queue_mapping["id"], {})
            enrich_mapping_with_previous_properties(new_queue_mapping, old_queue_mapping)

            enrich_mapping_with_previous_targets(
                new_sub_mapping=new_queue_mapping,
                old_sub_mapping=old_queue_mapping,
                new_ids=new_ids,
            )

            if new_inbox_mapping := new_queue_mapping.get("inbox", None):
                old_inbox_mapping = old_queue_mapping.get("inbox", {})
                enrich_mapping_with_previous_properties(new_inbox_mapping, old_inbox_mapping)

                enrich_mapping_with_previous_targets(
                    new_sub_mapping=new_queue_mapping["inbox"],
                    old_sub_mapping=old_inbox_mapping,
                    new_ids=new_ids,
                )


def find_mapping_of_object(sub_mapping: list[dict], id: int):
    for object in sub_mapping:
        if object["id"] == id:
            return object
    return None


def extract_target_ids(submapping: dict) -> list[int]:
    target_ids = []
    for target_object in submapping.get("targets", []):
        if target_id := target_object.get("target_id", None):
            target_ids.append(target_id)

    return target_ids


def extract_sources_targets(mapping: dict, include_organization=True) -> tuple[dict, dict]:
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

    if include_organization:
        targets["organization"] = extract_target_ids(mapping["organization"])
        sources["organization"] = mapping["organization"]["id"]

    for ws in mapping["organization"]["workspaces"]:
        sources["workspaces"].append(ws["id"])
        targets["workspaces"].extend(extract_target_ids(ws))

        for q in ws.get("queues", []):
            sources["queues"].append(q["id"])
            targets["queues"].extend(extract_target_ids(q))

            inbox = q.get("inbox", {})
            if inbox and (inbox_id := inbox.get("id", None)):
                sources["inboxes"].append(inbox_id)
                targets["inboxes"].extend(extract_target_ids(inbox))

    for schema in mapping["organization"]["schemas"]:
        sources["schemas"].append(schema["id"])
        targets["schemas"].extend(extract_target_ids(schema))

    for hook in mapping["organization"]["hooks"]:
        sources["hooks"].append(hook["id"])
        targets["hooks"].extend(extract_target_ids(hook))

    return sources, targets


def extract_source_target_pairs(mapping: dict) -> dict[str, dict[int, list]]:
    pairs = {
        "workspaces": {},
        "queues": {},
        "inboxes": {},
        "schemas": {},
        "hooks": {},
    }

    for ws in mapping["organization"]["workspaces"]:
        pairs["workspaces"][ws["id"]] = extract_target_ids(ws)

        for q in ws.get("queues", []):
            pairs["queues"][q["id"]] = extract_target_ids(q)

            inbox = q.get("inbox", None)
            if inbox and (inbox_id := inbox.get("id", None)):
                pairs["inboxes"][inbox_id] = extract_target_ids(inbox)

    for schema in mapping["organization"]["schemas"]:
        pairs["schemas"][schema["id"]] = extract_target_ids(schema)

    for hook in mapping["organization"]["hooks"]:
        pairs["hooks"][hook["id"]] = extract_target_ids(hook)

    return pairs


def extract_flat_lookup_table(mapping: dict) -> dict:
    pairs_by_type = extract_source_target_pairs(mapping)
    table = {}
    for pairs in pairs_by_type.values():
        table = {**table, **pairs}
    return table
