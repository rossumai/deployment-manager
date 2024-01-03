import asyncio
import json
from anyio import Path

import httpx
import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.common.upload import (
    upload_hook,
    upload_inbox,
    upload_queue,
    upload_schema,
    upload_workspace,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    detemplatize_name_id,
    extract_id_from_url,
    read_yaml,
    templatize_name_id,
    write_json,
    write_yaml,
)


@click.command(
    name="migrate",
    help="""
Applies selected changes onto other objects.
If these objects don't exist, they get crated.
The specifics of what objects to migrate where can be specified in a mapping.yaml file.
               """,
)
@click.option(
    "--mapping",
    default=settings.MAPPING_FILENAME,
    show_default=True,
    help="Path to the mapping file to use.",
)
@coro
async def migrate_project(mapping: str):
    mapping_file = mapping
    org_path = Path("./")
    mapping = read_yaml(org_path / mapping_file)

    target_organization = mapping["organization"]["target"]
    if not target_organization:
        raise click.ClickException(
            "No target for organization. If you want to migrate inside the same organization, just target its own ID."
        )

    if target_organization == mapping["organization"]["id"]:
        client = ElisAPIClient(
            base_url=settings.API_URL,
            username=settings.USERNAME,
            password=settings.PASSWORD,
        )
    else:
        client = ElisAPIClient(
            base_url=settings.TO_API_URL,
            username=settings.TO_USERNAME,
            password=settings.TO_PASSWORD,
        )

    # TODO: Update ORG based on the json

    # TODO: better error handling

    source_path = org_path / settings.SOURCE_DIRNAME

    _object_urls = []

    source_id_target_pairs = {
        **(await migrate_schemas(source_path, client, mapping)),
        **(await migrate_hooks(source_path, client, mapping)),
    }
    for object in source_id_target_pairs.values():
        _object_urls.append(object["url"])

    # Read workspaces in filesystem, check them in mapping
    # Read child queues in FS, ignore if you already ignore WS
    # Update inbox mapping after creating queue and always just update
    async for ws_path in (source_path / "workspaces").iterdir():
        name, id = detemplatize_name_id(ws_path.stem)
        ws_config_path = ws_path / "workspace.json"
        workspace = json.loads(await ws_config_path.read_text())

        workspace_mapping = find_mapping_of_object(
            mapping["organization"]["workspaces"], id
        )
        if workspace_mapping.get("ignore", None):
            continue

        result = await upload_workspace(client, workspace, workspace_mapping["target"])

        # hook_config_path = org_path / settings.TARGET_DIRNAME / 'workspaces' / f"{templatize_name_id(result['name'], result['id'])}.json"
        # await write_json(hook_config_path, result)
        workspace_mapping["target"] = result["id"]
        source_id_target_pairs[id] = result

        _object_urls.append(result["url"])

        async for queue_path in (ws_path / "queues").iterdir():
            name, id = detemplatize_name_id(queue_path.stem)

            queue_config_path = queue_path / "queue.json"
            queue = json.loads(await queue_config_path.read_text())

            replace_dependency_url(queue, "workspace", source_id_target_pairs)
            replace_dependency_url(queue, "schema", source_id_target_pairs)
            replace_dependency_url(queue, "hooks", source_id_target_pairs)
            del queue["inbox"]

            queue_mapping = find_mapping_of_object(workspace_mapping["queues"], id)
            if queue_mapping.get("ignore", None):
                continue

            queue_result = await upload_queue(client, queue, queue_mapping["target"])

            queue_mapping["target"] = queue_result["id"]
            source_id_target_pairs[id] = queue_result

            _object_urls.append(queue_result["url"])

            inbox_config_path = queue_path / "inbox.json"
            inbox = json.loads(await inbox_config_path.read_text())

            replace_dependency_url(inbox, "queues", source_id_target_pairs)
            del inbox[
                "email"
            ]  # Should either create a new one or it is already present

            inbox_mapping = queue_mapping["inbox"]
            # Inbox cannot be ignored because a queue depends on it
            # if inbox_mapping.get("ignore", None):
            # continue

            inbox_result = await upload_inbox(client, inbox, inbox_mapping["target"])
            inbox_mapping["target"] = inbox_result["id"]
            source_id_target_pairs[id] = result

            _object_urls.append(result["url"])

    # Update the mapping with right hand sides (targets) created during migration
    await write_yaml(org_path / mapping_file, mapping)

    # TODO: attribute override

    # TODO: write all target jsons (by running download)

    await _delete_migrated_objects(_object_urls)


async def migrate_schemas(source_path: Path, client: ElisAPIClient, mapping: dict):
    source_id_target_pairs = {}
    async for schema_path in (source_path / "schemas").iterdir():
        name, id = detemplatize_name_id(schema_path.stem)
        schema = json.loads(await schema_path.read_text())

        schema_mapping = find_mapping_of_object(mapping["organization"]["schemas"], id)
        if not schema_mapping.get("ignore", None):
            result = await upload_schema(client, schema, schema_mapping["target"])
            schema_mapping["target"] = result["id"]
            source_id_target_pairs[id] = result

    return source_id_target_pairs


async def migrate_hooks(source_path: Path, client: ElisAPIClient, mapping: dict):
    source_id_target_pairs = {}
    async for hook_path in (source_path / "hooks").iterdir():
        name, id = detemplatize_name_id(hook_path.stem)
        hook = json.loads(await hook_path.read_text())

        # TODO: handling hook private issues
        if hook["type"] != "function":
            continue

        # TODO: handle dependency graph of hooks

        hook["queues"] = []

        # TODO: ? token owner ?

        hook_mapping = find_mapping_of_object(mapping["organization"]["hooks"], id)
        if not hook_mapping.get("ignore", None):
            result = await upload_hook(client, hook, hook_mapping["target"])
            hook_mapping["target"] = result["id"]
            source_id_target_pairs[id] = result

    return source_id_target_pairs


def replace_dependency_url(object: dict, dependency: str, source_id_target_pairs: dict):
    if isinstance(object[dependency], list):
        new_urls = []
        for old_url in object[dependency]:
            old_id = extract_id_from_url(old_url)
            if new_object := source_id_target_pairs.get(old_id, None):
                new_urls.append(new_object["url"])
        object[dependency] = new_urls
    else:
        if new_object := source_id_target_pairs.get(
            extract_id_from_url(object[dependency]), None
        ):
            object[dependency] = new_object["url"]


def find_mapping_of_object(sub_mapping: list[dict], id: int):
    for object in sub_mapping:
        if object["id"] == id:
            return object
    return None


async def _delete_migrated_object(client: httpx.AsyncClient, object_url: str):
    await client.delete(object_url)


# Debug function to clean up
async def _delete_migrated_objects(object_urls: list[str]):
    elis = ElisAPIClient(
        base_url=settings.API_URL,
        username=settings.USERNAME,
        password=settings.PASSWORD,
    )
    token = await elis.get_token()

    async with httpx.AsyncClient(headers={"Authorization": f"Token {token}"}) as client:
        await asyncio.gather(
            *[_delete_migrated_object(client, url) for url in object_urls]
        )
