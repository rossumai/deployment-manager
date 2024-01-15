from anyio import Path
from rossum_api.models import Organization, Workspace, Hook, Schema, Queue, Inbox

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    adjust_keys,
    create_empty_mapping,
    read_yaml,
    write_yaml,
)


async def read_mapping(mapping_path: Path):
    if await mapping_path.exists():
        mapping = read_yaml(mapping_path)
        return adjust_keys(mapping)

    return None


async def write_mapping(mapping_path: Path, mapping: dict):
    mapping = adjust_keys(mapping, lower=False)
    await write_yaml(mapping_path, mapping)


async def create_update_mapping(
    org_path: Path,
    organization: Organization,
    workspaces_for_mapping: list[Workspace],
    hooks_for_mapping: list[Hook],
    schemas_for_mapping: list[Schema],
    old_mapping: dict,
):
    mapping = create_empty_mapping()

    mapping["organization"]["id"] = organization.id
    mapping["organization"]["name"] = organization.name

    # Ids of both source and target objects
    # Used to check that a target object was not deleted
    # If yes, ignore old mapping that assigns this target to some left (source) object
    new_ids = []

    for destination, workspace in workspaces_for_mapping:
        new_ids.append(workspace.id)
        ws_mapping = {
            **get_attributes_for_mapping(workspace),
            "queues": [],
        }
        for q in workspace.queues:
            new_ids.append(q.id)
            if q.inbox:
                new_ids.append(q.inbox.id)

            queue_mapping = {
                **get_attributes_for_mapping(q),
                "inbox": get_attributes_for_mapping(q.inbox) if q.inbox else None,
            }
            ws_mapping["queues"].append(queue_mapping)

        # Throw away the mapping, we just want the ids for objects that are targeted by something (based on the old mapping)
        if destination == settings.TARGET_DIRNAME:
            continue

        mapping["organization"]["workspaces"].append(ws_mapping)

    for destination, hook in hooks_for_mapping:
        new_ids.append(hook.id)
        if destination == settings.TARGET_DIRNAME:
            continue
        mapping["organization"]["hooks"].append(get_attributes_for_mapping(hook))

    for destination, schema in schemas_for_mapping:
        new_ids.append(schema.id)
        if destination == settings.TARGET_DIRNAME:
            continue
        mapping["organization"]["schemas"].append(get_attributes_for_mapping(schema))

    enrich_mappings_with_existing_attributes(
        old_mapping=old_mapping, new_mapping=mapping, new_ids=new_ids
    )

    await write_mapping(org_path / settings.MAPPING_FILENAME, mapping)


def get_attributes_for_mapping(
    object: Organization | Workspace | Queue | Hook | Schema | Inbox,
):
    return {"id": object.id, "name": object.name, "target": None}


def index_mappings_by_object_id(sub_mapping: list[dict]):
    indexed = {sm["id"]: sm for sm in sub_mapping}
    return indexed


def enrich_mapping_with_previous_properties(
    new_sub_mapping: dict, old_sub_mapping: dict
):
    for k, v in old_sub_mapping.items():
        if k not in new_sub_mapping:
            new_sub_mapping[k] = v


def enrich_mappings_with_existing_attributes(
    old_mapping: dict, new_mapping: dict, new_ids: list[int]
):
    """Use targets from the previous mapping, but only if the target objects were not deleted in Rossum"""
    new_mapping["organization"]["target"] = old_mapping["organization"]["target"]

    old_schema_mappings = index_mappings_by_object_id(
        old_mapping["organization"]["schemas"]
    )
    for new_schema_mapping in new_mapping["organization"]["schemas"]:
        old_schema_mapping = old_schema_mappings.get(new_schema_mapping["id"], {})
        enrich_mapping_with_previous_properties(new_schema_mapping, old_schema_mapping)

        target = old_schema_mapping.get("target", None)
        new_schema_mapping["target"] = target if target in new_ids else None

    old_hook_mappings = index_mappings_by_object_id(
        old_mapping["organization"]["hooks"]
    )
    for new_hook_mapping in new_mapping["organization"]["hooks"]:
        old_hook_mapping = old_hook_mappings.get(new_hook_mapping["id"], {})
        enrich_mapping_with_previous_properties(new_hook_mapping, old_hook_mapping)

        target = old_hook_mapping.get("target", None)
        new_hook_mapping["target"] = target if target in new_ids else None

    old_workspace_mappings = index_mappings_by_object_id(
        old_mapping["organization"]["workspaces"]
    )
    for new_workspace_mapping in new_mapping["organization"]["workspaces"]:
        old_workspace_mapping = old_workspace_mappings.get(
            new_workspace_mapping["id"], {}
        )
        enrich_mapping_with_previous_properties(
            new_workspace_mapping, old_workspace_mapping
        )

        target = old_workspace_mapping.get("target", None)
        new_workspace_mapping["target"] = target if target in new_ids else None

        old_queue_mappings = index_mappings_by_object_id(
            old_workspace_mapping.get("queues", [])
        )
        for new_queue_mapping in new_workspace_mapping.get("queues", []):
            old_queue_mapping = old_queue_mappings.get(new_queue_mapping["id"], {})
            enrich_mapping_with_previous_properties(
                new_queue_mapping, old_queue_mapping
            )

            target = old_queue_mapping.get("target", None)
            new_queue_mapping["target"] = target if target in new_ids else None

            if new_queue_mapping.get("inbox", None):
                old_inbox_mapping = old_queue_mapping.get("inbox", {})
                enrich_mapping_with_previous_properties(
                    new_queue_mapping["inbox"], old_inbox_mapping
                )

                target = old_inbox_mapping.get("target", None)
                new_queue_mapping["inbox"]["target"] = (
                    target if target in new_ids else None
                )
