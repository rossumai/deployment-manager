from rich.progress import Progress
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource


from deployment_manager.utils.consts import display_error
from deployment_manager.utils.functions import (
    gather_with_concurrency,
    make_request_with_progress,
)


async def delete_all_objects_with_ids(ids_to_delete: list[dict], client: ElisAPIClient):
    to_delete = {
        "workspaces": [],
        "queues": [],
        "inboxes": [],
        "schemas": [],
        "hooks": [],
    }
    total_to_delete_count = 0

    async for schema in client.list_all_schemas():
        if schema.id in ids_to_delete["schemas"]:
            to_delete["schemas"].append(schema.id)
            total_to_delete_count += 1

    async for hook in client.list_all_hooks():
        if hook.id in ids_to_delete["hooks"]:
            to_delete["hooks"].append(hook.id)
            total_to_delete_count += 1

    async for workspace in client.list_all_workspaces():
        if workspace.id in ids_to_delete["workspaces"]:
            to_delete["workspaces"].append(workspace.id)
            total_to_delete_count += 1

    async for queue in client.list_all_queues():
        if queue.id in ids_to_delete["queues"]:
            to_delete["queues"].append(queue.id)
            total_to_delete_count += 1

    # Rossum SDK is missing pagination of inboxes...
    async for inbox in client._http_client.fetch_all(Resource.Inbox):
        inbox = client._deserializer(Resource.Inbox, inbox)
        if inbox.id in ids_to_delete["inboxes"]:
            to_delete["inboxes"].append(inbox.id)
            total_to_delete_count += 1

    with Progress() as progress:
        task = progress.add_task(
            "Deleting objects in Rossum.", total=total_to_delete_count
        )

        try:
            await gather_with_concurrency(
                *[
                    make_request_with_progress(
                        client._http_client.delete(Resource.Hook, hook_id),
                        progress,
                        task,
                    )
                    for hook_id in to_delete["hooks"]
                ]
            )
        except Exception as e:
            display_error(f"Error while deleting hooks: {e}", e)

        try:
            await gather_with_concurrency(
                *[
                    make_request_with_progress(
                        client._http_client.delete(Resource.Inbox, inbox_id),
                        progress,
                        task,
                    )
                    for inbox_id in to_delete["inboxes"]
                ]
            )
        except Exception as e:
            display_error(f"Error while deleting inboxes: {e}", e)

        try:
            await gather_with_concurrency(
                *[
                    make_request_with_progress(
                        client._http_client._request(
                            "DELETE", f"queues/{queue_id}", params={"delete_after": "0"}
                        ),
                        progress,
                        task,
                    )
                    for queue_id in to_delete["queues"]
                ]
            )
        except Exception as e:
            display_error(f"Error while deleting queues: {e}", e)

        try:
            await gather_with_concurrency(
                *[
                    make_request_with_progress(
                        client.delete_workspace(workspace_id), progress, task
                    )
                    for workspace_id in to_delete["workspaces"]
                ]
            )
        except Exception as e:
            display_error(f"Error while deleting workspaces: {e}", e)

        try:
            await gather_with_concurrency(
                *[
                    make_request_with_progress(
                        client.delete_schema(schema_id), progress, task
                    )
                    for schema_id in to_delete["schemas"]
                ]
            )
        except Exception as e:
            display_error(f"Error while deleting schemas: {e}", e)
