import asyncio
import logging
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource
from project_rossum_deploy.common.mapping import read_mapping, write_mapping
from project_rossum_deploy.utils.consts import settings


async def create_self_targetting_org(tmp_path: Path, undo=False):
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    mapping["organization"]["target_object"] = (
        None if undo else mapping["organization"]["id"]
    )
    await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)


async def delete_migrated_objects(ids_to_retain: list[dict], client: ElisAPIClient):
    to_delete = {
        "workspaces": [],
        "queues": [],
        "inboxes": [],
        "schemas": [],
        "hooks": [],
    }

    async for schema in client.list_all_schemas():
        if schema.id not in ids_to_retain["schemas"]:
            to_delete["schemas"].append(schema.id)

    async for hook in client.list_all_hooks():
        if hook.id not in ids_to_retain["hooks"]:
            to_delete["hooks"].append(hook.id)

    async for workspace in client.list_all_workspaces():
        if workspace.id not in ids_to_retain["workspaces"]:
            to_delete["workspaces"].append(workspace.id)

    async for queue in client.list_all_queues():
        if queue.id not in ids_to_retain["queues"]:
            to_delete["queues"].append(queue.id)

    # Rossum SDK is missing pagination of inboxes...
    async for inbox in client._http_client.fetch_all(Resource.Inbox):
        inbox = client._deserializer(Resource.Inbox, inbox)
        if inbox.id not in ids_to_retain["inboxes"]:
            to_delete["inboxes"].append(inbox.id)

    try:
        await asyncio.gather(
            *[
                client._http_client.delete(Resource.Hook, hook_id)
                for hook_id in to_delete["hooks"]
            ]
        )
    except Exception as e:
        logging.exception(f"Error while deleting hooks: {e}")

    try:
        await asyncio.gather(
            *[
                client._http_client.delete(Resource.Inbox, inbox_id)
                for inbox_id in to_delete["inboxes"]
            ]
        )
    except Exception as e:
        logging.exception(f"Error while deleting inboxes: {e}")

    try:
        await asyncio.gather(
            *[
                client._http_client._request(
                    "DELETE", f"queues/{queue_id}", params={"delete_after": "0"}
                )
                for queue_id in to_delete["queues"]
            ]
        )
    except Exception as e:
        logging.exception(f"Error while deleting queues: {e}")

    try:
        await asyncio.gather(
            *[
                client.delete_workspace(workspace_id)
                for workspace_id in to_delete["workspaces"]
            ]
        )
    except Exception as e:
        logging.exception(f"Error while deleting workspaces: {e}")

    try:
        await asyncio.gather(
            *[client.delete_schema(schema_id) for schema_id in to_delete["schemas"]]
        )
    except Exception as e:
        logging.exception(f"Error while deleting schemas: {e}")
