import logging
from anyio import Path
from rich.progress import Progress
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    replace_dependency_url,
)
from project_rossum_deploy.common.attribute_override import override_attributes
from project_rossum_deploy.common.upload import (
    upload_inbox,
    upload_queue,
    upload_workspace,
)

from project_rossum_deploy.utils.functions import detemplatize_name_id, read_json


async def migrate_workspaces(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict,
    progress: Progress,
):
    workspace_paths = [
        workspace_path
        async for workspace_path in (source_path / "workspaces").iterdir()
    ]
    task = progress.add_task("Releasing workspaces...", total=len(workspace_paths))

    for ws_path in workspace_paths:
        try:
            _, id = detemplatize_name_id(ws_path.stem)
            ws_config_path = ws_path / "workspace.json"
            workspace = await read_json(ws_config_path)

            workspace["queues"] = []

            workspace_mapping = find_mapping_of_object(
                mapping["organization"]["workspaces"], id
            )
            if workspace_mapping.get("ignore", None):
                progress.update(task, advance=1)
                continue

            workspace = override_attributes(
                complete_mapping=mapping, mapping=workspace_mapping, object=workspace
            )
            result = await upload_workspace(
                client, workspace, workspace_mapping["target"]
            )

            workspace_mapping["target"] = result["id"]
            source_id_target_pairs[id] = result

            source_id_target_pairs = await migrate_queues_and_inboxes(
                ws_path=ws_path,
                client=client,
                workspace_mapping=workspace_mapping,
                mapping=mapping,
                source_id_target_pairs=source_id_target_pairs,
            )

            progress.update(task, advance=1)
        except Exception as e:
            logging.error(f"Error while migrating workspace '{id}': {e}")

    return source_id_target_pairs


async def migrate_queues_and_inboxes(
    ws_path: Path,
    client: ElisAPIClient,
    workspace_mapping: dict,
    mapping: dict,
    source_id_target_pairs: dict,
):
    if not (await (ws_path / "queues").exists()):
        return source_id_target_pairs

    async for queue_path in (ws_path / "queues").iterdir():
        try:
            _, id = detemplatize_name_id(queue_path.stem)

            queue_config_path = queue_path / "queue.json"
            queue = await read_json(queue_config_path)

            replace_dependency_url(queue, "workspace", source_id_target_pairs)
            replace_dependency_url(queue, "schema", source_id_target_pairs)
            # Both should be updated, otherwise Elis API uses 'webhooks' in case of a mismatch even though it is deprecated
            replace_dependency_url(queue, "hooks", source_id_target_pairs)
            replace_dependency_url(queue, "webhooks", source_id_target_pairs)
            del queue["inbox"]

            queue_mapping = find_mapping_of_object(workspace_mapping["queues"], id)
            if queue_mapping.get("ignore", None):
                continue

            queue = override_attributes(
                complete_mapping=mapping, mapping=queue_mapping, object=queue
            )
            queue_result = await upload_queue(client, queue, queue_mapping["target"])

            queue_mapping["target"] = queue_result["id"]
            source_id_target_pairs[id] = queue_result

            inbox_config_path = queue_path / "inbox.json"
            inbox = await read_json(inbox_config_path)

            replace_dependency_url(inbox, "queues", source_id_target_pairs)
            # Should either create a new one or it is already present
            del inbox["email"]

            inbox_mapping = queue_mapping["inbox"]
            # Inbox cannot be ignored because a queue depends on it
            inbox = override_attributes(
                complete_mapping=mapping, mapping=inbox_mapping, object=inbox
            )
            inbox_result = await upload_inbox(client, inbox, inbox_mapping["target"])
            inbox_mapping["target"] = inbox_result["id"]
            source_id_target_pairs[inbox["id"]] = inbox_result
        except Exception as e:
            logging.error(f"Error while migrating queue '{id}': {e}")

    return source_id_target_pairs
