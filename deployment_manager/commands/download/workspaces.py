import asyncio
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from deployment_manager.commands.download.email_templates import (
    download_email_templates_for_queue,
)
from deployment_manager.commands.download.helpers import (
    should_write_object,
)

from deployment_manager.common.read_write import write_json
from deployment_manager.utils.functions import (
    extract_id_from_url,
    templatize_name_id,
)


# async def save_downloaded_objects(self, objects: list[dict]):
#      # TODO: unknown destination and regex

#      for workspace in objects:
#          workspace_config_path = (
#              org_path
#              / destination
#              / "workspaces"
#              / templatize_name_id(workspace["name"], workspace["id"])
#              / "workspace.json"
#          )

#          if self.download_all or await should_write_object(
#              workspace_config_path, workspace, self.changed_files
#          ):
#              await write_json(
#                  workspace_config_path,
#                  workspace,
#                  Resource.Workspace,
#                  log_message=f"Pulled {workspace_config_path}",
#              )

#          workspace["queues"] = await download_queues_for_workspace(
#              client=client,
#              parent_dir=workspace_config_path.parent,
#              workspace_id=workspace["id"],
#              changed_files=changed_files,
#              download_all=download_all,
#          )
#          # TODO: return just the second value
#          workspaces.append((destination, workspace))

#      return workspaces


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
            await write_json(
                queue_path / "queue.json",
                queue,
                Resource.Queue,
                log_message=f'Pulled {queue_path / "queue.json"}',
            )

        inbox_id = extract_id_from_url(queue["inbox"])
        if inbox_id:
            queue["inbox"] = await download_inbox_for_queue(
                client=client,
                parent_dir=queue_path,
                inbox_id=inbox_id,
                changed_files=changed_files,
                download_all=download_all,
            )

        await download_email_templates_for_queue(
            client=client,
            parent_dir=queue_path,
            queue_id=queue["id"],
            changed_files=changed_files,
            download_all=download_all,
        )

        queues.append(queue)

    return queues


async def download_inbox_for_queue(
    client: ElisAPIClient,
    parent_dir: Path,
    inbox_id: int,
    changed_files: list = [],
    download_all: bool = False,
):
    inbox = await client._http_client.fetch_one(Resource.Inbox, inbox_id)
    inbox_path = parent_dir / "inbox.json"
    if download_all or await should_write_object(inbox_path, inbox, changed_files):
        await write_json(
            inbox_path,
            inbox,
            Resource.Inbox,
            log_message=f"Pulled {inbox_path}",
        )

    return inbox
