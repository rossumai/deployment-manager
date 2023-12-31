from anyio import Path
from rossum_api.models import Organization, Workspace, Hook, Schema, Queue, Inbox

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import read_yaml, write_yaml


async def create_update_mapping(
    org_path: Path,
    organization: Organization,
    workspace_mappings: list[Workspace],
    hook_mappings: list[Hook],
    schema_mappings: list[Schema],
    previous_targets: dict[list],
):
    mapping = create_empty_mapping()

    mapping["organization"]["id"] = organization.id
    mapping["organization"]["name"] = organization.name

    # Ids of both source and target objects
    # Used to check that a target object was not deleted
    # If yes, ignore old mapping that assigns this target to some left (source) object
    new_ids = []

    for workspace in workspace_mappings:
        new_ids.append(workspace.id)
        if workspace.id in previous_targets["workspaces"]:
            continue

        ws_mapping = {
            **get_attributes_for_mapping(workspace),
            "queues": [],
        }
        for q in workspace.queues:
            new_ids.append(q.id)
            new_ids.append(q.inbox.id)

            queue_mapping = {
                **get_attributes_for_mapping(q),
                "inbox": get_attributes_for_mapping(q.inbox),
            }
            ws_mapping["queues"].append(queue_mapping)

        mapping["organization"]["workspaces"].append(ws_mapping)

    for hook in hook_mappings:
        new_ids.append(hook.id)
        if hook.id in previous_targets["hooks"]:
            continue
        mapping["organization"]["hooks"].append(get_attributes_for_mapping(hook))

    for schema in schema_mappings:
        new_ids.append(schema.id)
        if schema.id in previous_targets["schemas"]:
            continue
        mapping["organization"]["schemas"].append(get_attributes_for_mapping(schema))

    # Take targets (right sides) from the previous mapping and reuse them where applicable
    mapping_path = org_path / settings.MAPPING_FILENAME
    if await mapping_path.exists():
        old_mapping = read_yaml(mapping_path)
        enrich_mappings_with_targets(old_mapping=old_mapping, new_mapping=mapping, new_ids=new_ids)

    await write_yaml(mapping_path, mapping)


def create_empty_mapping():
    return {
        "organization": {
            "id": "",
            "name": "",
            "target": None,
            "workspaces": [],
            "hooks": [],
            "schemas": [],
        }
    }


def get_attributes_for_mapping(object: Organization | Queue | Hook | Schema | Inbox):
    return {"id": object.id, "name": object.name, "target": None}


def enrich_mappings_with_targets(old_mapping: dict, new_mapping: dict, new_ids: list[int]):
    new_mapping["organization"]["target"] = old_mapping["organization"]["target"]

    schema_targets = {
        s["id"]: s["target"] for s in old_mapping["organization"]["schemas"]
    }
    for schema in new_mapping["organization"]["schemas"]:
        target = schema_targets.get(schema["id"], None)
        schema["target"] = target if target in new_ids else None

    hook_targets = {h["id"]: h["target"] for h in old_mapping["organization"]["hooks"]}
    for hook in new_mapping["organization"]["hooks"]:
        target = hook_targets.get(hook["id"], None)
        hook["target"] = target if target in new_ids else None

    workspace_and_queue_targets = {
        ws["id"]: ws for ws in old_mapping["organization"]["workspaces"]
    }
    for ws in workspace_and_queue_targets.values():
        ws["queues"] = {q["id"]: q["target"] for q in ws["queues"]}
    for workspace in new_mapping["organization"]["workspaces"]:
        ws_target = workspace_and_queue_targets[workspace["id"]].get("target", None)
        ws["target"] = ws_target if ws_target in new_ids else None
        for queue in workspace["queues"]:
            queue_target =workspace_and_queue_targets[workspace["id"]]["queues"].get(queue['id'], None)
            queue["target"] = queue_target if queue_target in new_ids else None


def extract_targets(mapping: dict) -> dict:
    targets = {}

    targets["organization"] = mapping["organization"]["target"]

    targets["workspaces"] = []
    targets["queues"] = []
    targets["inboxes"] = []
    for ws in mapping["organization"]["workspaces"]:
        if ws["target"]:
            targets["workspaces"].append(ws["target"])
        for q in ws["queues"]:
            if q["target"]:
                targets["queues"].append(q["target"])
            if q["inbox"]["target"]:
                targets["inboxes"].append(q["inbox"]["target"])

    targets["schemas"] = []
    for schema in mapping["organization"]["schemas"]:
        if schema["target"]:
            targets["schemas"].append(schema["target"])

    targets["hooks"] = []
    for hook in mapping["organization"]["hooks"]:
        if hook["target"]:
            targets["hooks"].append(hook["target"])

    return targets
