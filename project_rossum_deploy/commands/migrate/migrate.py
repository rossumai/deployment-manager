import asyncio
import json
import logging
from anyio import Path

import click
from rossum_api import ElisAPIClient
from project_rossum_deploy.commands.migrate.helpers import (
    _delete_migrated_objects,
    find_mapping_of_object,
    replace_dependency_url,
)
from project_rossum_deploy.commands.migrate.hooks import migrate_hooks
from project_rossum_deploy.common.upload import (
    upload_inbox,
    upload_organization,
    upload_queue,
    upload_schema,
    upload_workspace,
)

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    coro,
    detemplatize_name_id,
    read_yaml,
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

    source_id_target_pairs = {}

    # TODO: add messages to signal progress

    try:
        organization = json.loads(await (org_path / "organization.json").read_text())
        # Use only a subset of org fields where it makes sense to migrate
        organization_fields = {k: organization[k] for k in settings.ORGANIZATION_FIELDS}
        await upload_organization(client, organization_fields, organization["id"])

        source_path = org_path / settings.SOURCE_DIRNAME

        source_id_target_pairs = {
            **(await migrate_schemas(source_path, client, mapping)),
            **(await migrate_hooks(source_path, client, mapping)),
        }
        source_id_target_pairs = await migrate_workspaces(
            source_path, client, mapping, source_id_target_pairs
        )

        # Update the mapping with right hand sides (targets) created during migration
        await write_yaml(org_path / mapping_file, mapping)
    except Exception as e:
        logging.error("Unexpected error while migrating objects:")
        logging.exception(e)

    _object_urls = []
    for object in source_id_target_pairs.values():
        _object_urls.append(object["url"])
    # await _delete_migrated_objects(_object_urls)

    click.echo(_object_urls)

    # TODO: attribute override

    # TODO: write all target jsons (by running download)


async def migrate_schemas(source_path: Path, client: ElisAPIClient, mapping: dict):
    source_id_target_pairs = {}
    async for schema_path in (source_path / "schemas").iterdir():
        try:
            name, id = detemplatize_name_id(schema_path.stem)
            schema = json.loads(await schema_path.read_text())

            schema_mapping = find_mapping_of_object(
                mapping["organization"]["schemas"], id
            )
            if not schema_mapping.get("ignore", None):
                result = await upload_schema(client, schema, schema_mapping["target"])
                schema_mapping["target"] = result["id"]
                source_id_target_pairs[id] = result
        except Exception as e:
            logging.error(f'Error while migrationg schema "{id}:')
            logging.exception(e)

    return source_id_target_pairs


async def migrate_workspaces(
    source_path: Path,
    client: ElisAPIClient,
    mapping: dict,
    source_id_target_pairs: dict,
):
    async for ws_path in (source_path / "workspaces").iterdir():
        try:
            name, id = detemplatize_name_id(ws_path.stem)
            ws_config_path = ws_path / "workspace.json"
            workspace = json.loads(await ws_config_path.read_text())

            workspace_mapping = find_mapping_of_object(
                mapping["organization"]["workspaces"], id
            )
            if workspace_mapping.get("ignore", None):
                continue

            result = await upload_workspace(
                client, workspace, workspace_mapping["target"]
            )

            workspace_mapping["target"] = result["id"]
            source_id_target_pairs[id] = result

            source_id_target_pairs = await migrate_queues_and_inboxes(
                ws_path, client, workspace_mapping, source_id_target_pairs
            )
        except Exception as e:
            logging.error(f"Error while migrating workspace '{id}':")
            logging.exception(e)

    return source_id_target_pairs


async def migrate_queues_and_inboxes(
    ws_path: Path,
    client: ElisAPIClient,
    workspace_mapping: dict,
    source_id_target_pairs: dict,
):
    async for queue_path in (ws_path / "queues").iterdir():
        try:
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

            inbox_config_path = queue_path / "inbox.json"
            inbox = json.loads(await inbox_config_path.read_text())

            replace_dependency_url(inbox, "queues", source_id_target_pairs)
            # Should either create a new one or it is already present
            del inbox["email"]

            inbox_mapping = queue_mapping["inbox"]
            
            # Inbox cannot be ignored because a queue depends on it

            inbox_result = await upload_inbox(client, inbox, inbox_mapping["target"])
            inbox_mapping["target"] = inbox_result["id"]
            source_id_target_pairs[inbox["id"]] = inbox_result
            print(inbox_result)
        except Exception as e:
            logging.error(f"Error while migrating queue '{id}':")
            logging.exception(e)

    return source_id_target_pairs


if __name__ == "__main__":
    asyncio.run(
        _delete_migrated_objects(
            [
                "https://deploymenttool.rossum.app/api/v1/schemas/1078213",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078214",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078215",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078216",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078217",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078218",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078219",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078220",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078221",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078222",
                "https://deploymenttool.rossum.app/api/v1/schemas/1078223",
                "https://deploymenttool.rossum.app/api/v1/hooks/224021",
                "https://deploymenttool.rossum.app/api/v1/hooks/224022",
                "https://deploymenttool.rossum.app/api/v1/workspaces/502480",
                "https://deploymenttool.rossum.app/api/v1/queues/811897",
                "https://deploymenttool.rossum.app/api/v1/inboxes/430635",
                "https://deploymenttool.rossum.app/api/v1/queues/811898",
                "https://deploymenttool.rossum.app/api/v1/inboxes/430636",
                "https://deploymenttool.rossum.app/api/v1/queues/811899",
                "https://deploymenttool.rossum.app/api/v1/inboxes/430637",
                "https://deploymenttool.rossum.app/api/v1/workspaces/502481",
                "https://deploymenttool.rossum.app/api/v1/queues/811900",
                "https://deploymenttool.rossum.app/api/v1/inboxes/430638",
            ]
        )
    )