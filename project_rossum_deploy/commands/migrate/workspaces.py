import asyncio
from anyio import Path
from rich.progress import Progress
from rich import print
from rich.panel import Panel

from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    replace_dependency_url,
)
from project_rossum_deploy.common.upload import (
    upload_inbox,
    upload_queue,
    upload_workspace,
)
from project_rossum_deploy.utils.consts import settings

from project_rossum_deploy.utils.functions import detemplatize_name_id, read_json


async def migrate_workspaces(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict,
    sources_by_source_id_map: dict,
    progress: Progress,
):
    workspace_paths = [
        workspace_path
        async for workspace_path in (source_path / "workspaces").iterdir()
    ]
    task = progress.add_task("Releasing workspaces...", total=len(workspace_paths))

    async def migrate_workspace(ws_path: Path):
        try:
            _, id = detemplatize_name_id(ws_path.stem)
            ws_config_path = ws_path / "workspace.json"
            workspace = await read_json(ws_config_path)
            sources_by_source_id_map[id] = workspace

            workspace["queues"] = []
            workspace[
                "organization"
            ] = f"{settings.TARGET_API_URL}/organizations/{mapping['organization']['target_object']}"

            workspace_mapping = find_mapping_of_object(
                mapping["organization"]["workspaces"], id
            )
            if workspace_mapping.get("ignore", None):
                progress.update(task, advance=1)
                return

            result = await upload_workspace(
                client, workspace, workspace_mapping["target_object"]
            )

            workspace_mapping["target_object"] = result["id"]
            source_id_target_pairs[id] = result

            await migrate_queues_and_inboxes(
                ws_path=ws_path,
                client=client,
                workspace_mapping=workspace_mapping,
                mapping=mapping,
                sources_by_source_id_map=sources_by_source_id_map,
                source_id_target_pairs=source_id_target_pairs,
            )

            progress.update(task, advance=1)
        except Exception as e:
            print(Panel(f"Error while migrating workspace with path '{ws_path}': {e}"))

    await asyncio.gather(
        *[migrate_workspace(ws_path=ws_path) for ws_path in workspace_paths]
    )


async def migrate_queues_and_inboxes(
    ws_path: Path,
    client: ElisAPIClient,
    workspace_mapping: dict,
    mapping: dict,
    sources_by_source_id_map: dict,
    source_id_target_pairs: dict,
):
    if not (await (ws_path / "queues").exists()):
        return

    queue_paths = [queue_path async for queue_path in (ws_path / "queues").iterdir()]

    async def migrate_queue_and_inbox(queue_path: Path):
        try:
            _, id = detemplatize_name_id(queue_path.stem)

            queue_config_path = queue_path / "queue.json"
            queue = await read_json(queue_config_path)
            sources_by_source_id_map[id] = queue

            replace_dependency_url(queue, "workspace", source_id_target_pairs)
            replace_dependency_url(queue, "schema", source_id_target_pairs)
            # Both should be updated, otherwise Elis API uses 'webhooks' in case of a mismatch even though it is deprecated
            replace_dependency_url(queue, "hooks", source_id_target_pairs)
            replace_dependency_url(queue, "webhooks", source_id_target_pairs)
            queue.pop('inbox', None)

            queue_mapping = find_mapping_of_object(workspace_mapping["queues"], id)
            if queue_mapping.get("ignore", None):
                return

            queue_result = await upload_queue(
                client, queue, queue_mapping["target_object"]
            )

            queue_mapping["target_object"] = queue_result["id"]
            source_id_target_pairs[id] = queue_result


            inbox_config_path = queue_path / "inbox.json"
            try:
                inbox = await read_json(inbox_config_path)
            except FileNotFoundError:
                return
            sources_by_source_id_map[inbox["id"]] = inbox

            replace_dependency_url(inbox, "queues", source_id_target_pairs)
            # Should either create a new one or it is already present
            inbox.pop('email', None)

            inbox_mapping = queue_mapping["inbox"]
            # Inbox cannot be ignored because a queue depends on it
            inbox_result = await upload_inbox(
                client, inbox, inbox_mapping["target_object"]
            )
            inbox_mapping["target_object"] = inbox_result["id"]
            source_id_target_pairs[inbox["id"]] = inbox_result
        except Exception as e:
            print(Panel(f"Error while migrating queue with path '{queue_path}': {e}"))

    await asyncio.gather(
        *[migrate_queue_and_inbox(queue_path=queue_path) for queue_path in queue_paths]
    )
