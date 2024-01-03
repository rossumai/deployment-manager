import json
import logging

from anyio import Path
from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.migrate.helpers import (
    find_mapping_of_object,
    get_token_owner,
)
from project_rossum_deploy.common.upload import upload_hook
from project_rossum_deploy.utils.functions import detemplatize_name_id


async def migrate_hooks(source_path: Path, client: ElisAPIClient, mapping: dict):
    source_id_target_pairs = {}
    token_owner = await get_token_owner(client)

    async for hook_path in (source_path / "hooks").iterdir():
        try:
            name, id = detemplatize_name_id(hook_path.stem)
            hook = json.loads(await hook_path.read_text())

            # TODO: handling hook private issues
            if hook["type"] != "function":
                continue

            # TODO: handle dependency graph of hooks

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

    return source_id_target_pairs
