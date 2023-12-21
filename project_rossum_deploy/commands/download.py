import dataclasses
import json
import shutil
from anyio import Path
from rossum_api import ElisAPIClient
import click

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import coro, templatize_name_id


@click.command(
    name="download",
    help="""
Downloads all Rossum objects from the user's default (first) organization.
Creates a local organization directory structure with the configs of these objects.
In case the directory already exists, it first deletes its contents and then downloads them anew.
               """,
)
@coro
async def download_organization():
    client = ElisAPIClient(
        base_url=settings.API_URL,
        username=settings.USERNAME,
        password=settings.PASSWORD,
    )

    organization = await client.retrieve_own_organization()

    org_path = Path(templatize_name_id(organization.name, organization.id))
    if await org_path.exists():
        click.echo(f'Path "{org_path}" already exists, cleaning it up first...')
        shutil.rmtree(org_path)
    await write_file(org_path / "organization.json", organization)

    await download_workspaces(client, org_path)
    await download_queues(client, org_path)
    await download_schemas(client, org_path)
    await download_hooks(client, org_path)


async def download_workspaces(client: ElisAPIClient, parent_dir: Path):
    async for workspace in client.list_all_workspaces():
        workspace_config_path = (
            parent_dir
            / "workspaces"
            / templatize_name_id(workspace.name, workspace.id)
            / "workspace.json"
        )
        await write_file(workspace_config_path, workspace)


async def download_queues(client: ElisAPIClient, parent_dir: Path):
    async for queue in client.list_all_queues():
        queue_config_path = (
            parent_dir / "queues" / f"{templatize_name_id(queue.name, queue.id)}.json"
        )
        await write_file(queue_config_path, queue)


async def download_schemas(client: ElisAPIClient, parent_dir: Path):
    async for schema in client.list_all_schemas():
        schema_config_path = (
            parent_dir
            / "schemas"
            / f"{templatize_name_id(schema.name, schema.id)}.json"
        )
        await write_file(schema_config_path, schema)


async def download_hooks(client: ElisAPIClient, parent_dir: Path):
    async for hook in client.list_all_hooks():
        hook_config_path = (
            parent_dir / "hooks" / f"{templatize_name_id(hook.name, hook.id)}.json"
        )
        await write_file(hook_config_path, hook)


async def write_file(path: Path, object: dict):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        json.dump(object, wf)
