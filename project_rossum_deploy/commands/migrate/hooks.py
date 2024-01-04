import json
import logging

from anyio import Path
import click
from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    get_token_owner,
)
from project_rossum_deploy.common.upload import upload_hook
from project_rossum_deploy.utils.functions import (
    detemplatize_name_id,
    extract_id_from_url,
)


async def migrate_hooks(source_path: Path, client: ElisAPIClient, mapping: dict):
    source_id_target_pairs = {}
    token_owner = await get_token_owner(client)

    async for hook_path in (source_path / "hooks").iterdir():
        try:
            _, id = detemplatize_name_id(hook_path.stem)
            hook = json.loads(await hook_path.read_text())

            # TODO: handling hook private issues
            if hook["type"] != "function":
                continue

            hook["run_after"] = []
            hook["queues"] = []
            # Change token owner to TO user (important for cross-org migrations)
            hook["token_owner"] = token_owner.url

            hook_mapping = find_mapping_of_object(mapping["organization"]["hooks"], id)
            if not hook_mapping.get("ignore", None):
                result = await upload_hook(client, hook, hook_mapping["target"])
                hook_mapping["target"] = result["id"]
                source_id_target_pairs[id] = result
        except Exception as e:
            logging.error(f"Error while migrating hook '{id}':")
            logging.exception(e)

    await migrate_hook_dependency_graph(client, source_path, source_id_target_pairs)

    click.echo(
        "Hooks were successfully migrated to target. Please add any necessary secrets manually."
    )

    return source_id_target_pairs


async def migrate_hook_dependency_graph(
    client: ElisAPIClient, source_path: Path, source_id_target_pairs: dict
):
    async for hook_path in (source_path / "hooks").iterdir():
        try:
            _, old_hook_id = detemplatize_name_id(hook_path.stem)
            old_hook = json.loads(await hook_path.read_text())
            new_hook = source_id_target_pairs.get(old_hook_id, None)

            # The hook was ignored, it has no target equivalent anyway
            if not new_hook:
                continue

            run_after = []
            for predecessor_url in old_hook["run_after"]:
                predecessor_id = extract_id_from_url(predecessor_url)
                # The hook was ignored, it has no target equivalent anyway
                target_object = source_id_target_pairs.get(predecessor_id, None)
                if not target_object:
                    continue

                new_url = predecessor_url.replace(
                    str(predecessor_id), str(target_object["id"])
                )
                run_after.append(new_url)

                await upload_hook(client, {"run_after": run_after}, new_hook["id"])
        except Exception as e:
            logging.error(f"Error while migrating hook '{source_path}':")
            logging.exception(e)
