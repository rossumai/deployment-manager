import asyncio
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.download.helpers import (
    determine_object_destination,
    should_write_object,
)

from project_rossum_deploy.utils.functions import (
    extract_id_from_url,
    templatize_name_id,
    write_json,
)


async def download_workspaces(
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict = {},
    destination: str = "",
    sources: dict = {},
    targets: dict = {},
    changed_files: list = [],
    download_all: bool = False,
):
    workspaces = []

    paginated_workspaces = [
        workspace async for workspace in client.list_all_workspaces()
    ]

    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_workspaces = await asyncio.gather(
        *[
            client._http_client.fetch_one(Resource.Workspace, ws.id)
            for ws in paginated_workspaces
        ]
    )

    for workspace in full_workspaces:
        destination_local = (
            destination
            if destination
            else await determine_object_destination(
                object=workspace,
                object_type="workspace",
                org_path=org_path,
                mapping=mapping,
                sources=sources,
                targets=targets,
            )
        )

        workspace_config_path = (
            org_path
            / destination_local
            / "workspaces"
            / templatize_name_id(workspace["name"], workspace["id"])
            / "workspace.json"
        )

        if download_all or await should_write_object(
            workspace_config_path, workspace, changed_files
        ):
            await write_json(workspace_config_path, workspace, Resource.Workspace)

        workspace["queues"] = await download_queues_for_workspace(
            client=client,
            parent_dir=workspace_config_path.parent,
            workspace_id=workspace["id"],
            changed_files=changed_files,
            download_all=download_all,
        )
        workspaces.append((destination_local, workspace))

    return workspaces


async def download_queues_for_workspace(
    client: ElisAPIClient,
    parent_dir: Path,
    workspace_id: int,
    changed_files: list = [],
    download_all: bool = False,
):
    queues = []

    paginated_queues = [q async for q in client.list_all_queues(workspace=workspace_id)]
    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_queues = await asyncio.gather(
        *[client._http_client.fetch_one(Resource.Queue, q.id) for q in paginated_queues]
    )

    for queue in full_queues:
        queue_path = (
            parent_dir / "queues" / f"{templatize_name_id(queue['name'], queue['id'])}"
        )
        if download_all or await should_write_object(
            queue_path / "queue.json", queue, changed_files
        ):
            await write_json(queue_path / "queue.json", queue, Resource.Queue)

        inbox_id = extract_id_from_url(queue["inbox"])
        if inbox_id:
            queue["inbox"] = await download_inbox(
                client=client,
                parent_dir=queue_path,
                inbox_id=inbox_id,
                changed_files=changed_files,
                download_all=download_all,
            )
        queues.append(queue)

    return queues


async def download_inbox(
    client: ElisAPIClient,
    parent_dir: Path,
    inbox_id: int,
    changed_files: list = [],
    download_all: bool = False,
):
    inbox = await client._http_client.fetch_one(Resource.Inbox, inbox_id)
    inbox_path = parent_dir / "inbox.json"
    if download_all or await should_write_object(inbox_path, inbox, changed_files):
        await write_json(inbox_path, inbox, Resource.Inbox)

    return inbox
