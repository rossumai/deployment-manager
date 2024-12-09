import asyncio
from anyio import Path
from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from deployment_manager.commands.download.helpers import (
    create_custom_hook_code_path,
    should_write_object,
)

from deployment_manager.common.read_write import write_json, write_str
from deployment_manager.utils.functions import (
    templatize_name_id,
)


async def download_hooks(
    client: ElisAPIClient,
    org_path: Path,
    mapping: dict = {},
    destination: str = "",
    changed_files: list = [],
    download_all: bool = False,
):
    hooks = []

    paginated_hooks = [hook async for hook in client.list_all_hooks()]

    # Refetch in case the paginated fields don't include everything
    # Use raw dicts and not dataclasses in case of fields not defined in the Rossum API lib
    full_hooks = await asyncio.gather(
        *[
            client._http_client.fetch_one(Resource.Hook, hook.id)
            for hook in paginated_hooks
        ]
    )

    for hook in full_hooks:
        hook_config_path = (
            org_path
            / destination
            / "hooks"
            / f"{templatize_name_id(hook['name'], hook['id'])}.json"
        )

        if download_all or await should_write_object(
            hook_config_path, hook, changed_files
        ):
            await write_json(
                hook_config_path,
                hook,
                Resource.Hook,
                log_message=f"Pulled {hook_config_path}",
            )

            custom_hook_code_path = create_custom_hook_code_path(hook_config_path, hook)
            if custom_hook_code_path:
                await write_str(
                    custom_hook_code_path, hook.get("config", {}).get("code", None)
                )

        hooks.append((destination, hook))

    return hooks
