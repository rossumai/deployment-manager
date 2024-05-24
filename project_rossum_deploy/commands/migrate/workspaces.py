import asyncio
from copy import deepcopy
import functools
import logging
from anyio import Path
from rich import print
from rich.progress import Progress
from rich.panel import Panel

from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    migrate_object_to_multiple_targets,
    replace_dependency_url,
    simulate_migrate_object,
)
from project_rossum_deploy.commands.migrate.upload import (
    upload_inbox,
    upload_queue,
    upload_workspace,
)
from project_rossum_deploy.utils.consts import PrdVersionException, display_error, settings

from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    read_json,
)


async def migrate_workspaces(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict[int, list],
    sources_by_source_id_map: dict,
    progress: Progress,
    plan_only: bool = False,
    target_objects: list[dict] = [],
    errors: dict = {},
    force: bool = False,
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
            replace_dependency_url(
                workspace, 0, 1, "organization", source_id_target_pairs
            )

            workspace_mapping = find_mapping_of_object(
                mapping["organization"]["workspaces"], id
            )
            if workspace_mapping.get("ignore", None):
                progress.update(task, advance=1)
                return

            if plan_only:
                partial_upload_workspace = functools.partial(
                    simulate_migrate_object,
                    source_object=workspace,
                )
            else:
                partial_upload_workspace = functools.partial(
                    upload_workspace,
                    client,
                    workspace,
                    target_objects=target_objects,
                    errors=errors,
                    force=force,
                )
            source_id_target_pairs[id] = []
            if "target_object" in workspace_mapping:
                raise PrdVersionException(
                    f'Detected "target_object" for workspace with ID "{id}". Please run "prd {settings.MIGRATE_MAPPING_COMMAND_NAME}" to have the correct mapping format.'
                )

            results = await migrate_object_to_multiple_targets(
                submapping=workspace_mapping, upload_function=partial_upload_workspace
            )
            source_id_target_pairs[id].extend(results)

            await migrate_queues_and_inboxes(
                ws_path=ws_path,
                client=client,
                workspace_mapping=workspace_mapping,
                mapping=mapping,
                sources_by_source_id_map=sources_by_source_id_map,
                source_id_target_pairs=source_id_target_pairs,
                plan_only=plan_only,
                target_objects=target_objects,
                errors=errors,
                force=force,
            )

            progress.update(task, advance=1)
        except PrdVersionException as e:
            raise e
        except Exception as e:
            display_error(
                f"Error while migrating workspace with path '{ws_path}': {e}", e
            )

    if plan_only:
        print(Panel("Simulating workspaces"))

    await asyncio.gather(
        *[migrate_workspace(ws_path=ws_path) for ws_path in workspace_paths]
    )


async def migrate_queues_and_inboxes(
    ws_path: Path,
    client: ElisAPIClient,
    workspace_mapping: dict,
    mapping: dict,
    sources_by_source_id_map: dict,
    source_id_target_pairs: dict[int, list],
    plan_only: bool = False,
    target_objects: list[dict] = [],
    errors: dict = {},
    force: bool = False,
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

            queue_mapping = find_mapping_of_object(workspace_mapping["queues"], id)
            if queue_mapping.get("ignore", None):
                return

            if plan_only:
                partial_upload_queue_function = functools.partial(
                    simulate_migrate_object,
                    source_object=queue,
                )
            else:
                partial_upload_queue_function = functools.partial(
                    prepare_queue_upload,
                    queue=queue,
                    client=client,
                    source_id_target_pairs=source_id_target_pairs,
                    target_objects=target_objects,
                    errors=errors,
                    force=force,
                )

            source_id_target_pairs[id] = []
            if "target_object" in queue_mapping:
                raise PrdVersionException(
                    f'Detected "target_object" for queue with ID "{id}". Please run "prd {settings.MIGRATE_MAPPING_COMMAND_NAME}" to have the correct mapping format.'
                )

            results = await migrate_object_to_multiple_targets(
                submapping=queue_mapping,
                upload_function=partial_upload_queue_function,
                pass_index_args=True,
            )
            source_id_target_pairs[id].extend(results)

            inbox_config_path = queue_path / "inbox.json"
            try:
                inbox = await read_json(inbox_config_path)
            except FileNotFoundError:
                return

            inbox_id = inbox["id"]
            sources_by_source_id_map[inbox["id"]] = inbox
            inbox_mapping = queue_mapping["inbox"]

            # Inbox cannot be ignored because a queue depends on it

            if plan_only:
                partial_upload_inbox_function = functools.partial(
                    simulate_migrate_object,
                    source_object=inbox,
                )
            else:
                partial_upload_inbox_function = functools.partial(
                    prepare_inbox_upload,
                    inbox=inbox,
                    client=client,
                    source_id_target_pairs=source_id_target_pairs,
                    target_objects=target_objects,
                    errors=errors,
                    force=force,
                )
            source_id_target_pairs[inbox_id] = []
            if "target_object" in inbox_mapping:
                raise PrdVersionException(
                    f'Detected "target_object" for inbox with ID "{inbox_id}". Please run "prd {settings.MIGRATE_MAPPING_COMMAND_NAME}" to have the correct mapping format.'
                )

            results = await migrate_object_to_multiple_targets(
                submapping=inbox_mapping,
                upload_function=partial_upload_inbox_function,
                pass_index_args=True,
            )
            source_id_target_pairs[inbox_id].extend(results)

        except PrdVersionException as e:
            raise e
        except Exception as e:
            display_error(
                f"Error while migrating queue with path '{queue_path}': {e}", e
            )
            logging.exception(e)

    await asyncio.gather(
        *[migrate_queue_and_inbox(queue_path=queue_path) for queue_path in queue_paths]
    )


async def prepare_queue_upload(
    queue: dict,
    client: ElisAPIClient,
    target_index: int,
    target_objects_count: int,
    source_id_target_pairs: dict[int, list],
    target_id: int,
    target_objects: list[dict] = [],
    errors: dict = {},
    force: bool = False,
):
    queue = deepcopy(queue)
    target_object = (
        await client._http_client.fetch_one(Resource.Queue, target_id)
        if target_id
        else None
    )

    replace_dependency_url(
        object=queue,
        target_index=target_index,
        target_objects_count=target_objects_count,
        dependency="workspace",
        source_id_target_pairs=source_id_target_pairs,
        target_object=target_object,
    )
    replace_dependency_url(
        object=queue,
        target_index=target_index,
        target_objects_count=target_objects_count,
        dependency="schema",
        source_id_target_pairs=source_id_target_pairs,
        target_object=target_object,
    )
    # Both should be updated, otherwise Elis API uses 'webhooks' in case of a mismatch even though it is deprecated
    replace_dependency_url(
        object=queue,
        target_index=target_index,
        target_objects_count=target_objects_count,
        dependency="hooks",
        source_id_target_pairs=source_id_target_pairs,
        target_object=target_object,
    )
    replace_dependency_url(
        object=queue,
        target_index=target_index,
        target_objects_count=target_objects_count,
        dependency="webhooks",
        source_id_target_pairs=source_id_target_pairs,
        target_object=target_object,
    )
    queue.pop("inbox", None)

    return await upload_queue(
        client=client,
        queue=queue,
        target_id=target_id,
        target_objects=target_objects,
        errors=errors,
        force=force,
    )


async def prepare_inbox_upload(
    inbox: dict,
    client: ElisAPIClient,
    target_index: int,
    target_objects_count: int,
    source_id_target_pairs: dict[int, list],
    target_id: int,
    target_objects: list[dict] = [],
    errors: dict = {},
    force: bool = False,
):
    inbox = deepcopy(inbox)

    replace_dependency_url(
        object=inbox,
        dependency="queues",
        target_index=target_index,
        target_objects_count=target_objects_count,
        source_id_target_pairs=source_id_target_pairs,
    )
    # Should either create a new one or it is already present
    inbox.pop("email", None)

    return await upload_inbox(
        client=client,
        inbox=inbox,
        target_id=target_id,
        target_objects=target_objects,
        errors=errors,
        force=force,
    )
