import json
from rossum_api.dtos import Token
from anyio import Path
from deployment_manager.common.custom_client import CustomAsyncRossumAPIClient as AsyncRossumAPIClient
from rich import print as pprint

from deployment_manager.commands.deploy.subcommands.run.helpers import (
    get_url_and_credentials,
)
from deployment_manager.commands.hook.helpers import (
    get_org_name_from_hook_path,
    get_project_path_from_hook_path,
    load_hook_object,
)
from deployment_manager.commands.hook.payload import generate_hook_payload
from deployment_manager.common.read_write import read_object_from_json
from deployment_manager.utils.consts import display_error
from deployment_manager.utils.functions import detemplatize_name_id


async def test_hook(
    hook_path: Path,
    payload_path: Path = None,
    annotation_url: str = "",
    client: AsyncRossumAPIClient = None,
):
    try:
        if not client:
            project_path = get_project_path_from_hook_path(hook_path=hook_path)
            org_name = get_org_name_from_hook_path(hook_path=hook_path)
            credentials = await get_url_and_credentials(
                project_path=project_path,
                org_name=org_name,
            )
            if not credentials:
                return
            client = AsyncRossumAPIClient(
                base_url=credentials.url, credentials=Token(credentials.token)
            )

        if not payload_path:
            payload = await generate_hook_payload(
                hook_path=hook_path, annotation_url=annotation_url
            )
            if not payload:
                return
        else:
            payload = await read_object_from_json(path=payload_path)

        hook = await load_hook_object(hook_path=hook_path)
        if not hook:
            return

        _, hook_id = detemplatize_name_id(hook_path)

        request_body = {"payload": payload}

        # Use the latest code in the .py file where available
        latest_code_str = hook.get("config", {}).get("code", "")
        runtime = hook.get("config", {}).get("runtime", "")
        code_path = hook_path.with_suffix(".py")
        if await code_path.exists():
            latest_code_str = await code_path.read_text()

        if latest_code_str:
            request_body["config"] = {"runtime": runtime, "code": latest_code_str}

        result = await client._http_client.request_json(
            method="POST", url=f"hooks/{hook_id}/test", json=request_body
        )

        pprint("[bold]### RETURN: ###[/bold]")
        pprint(json.dumps(result.get("response", {}), indent=4))
        pprint("\n[bold]### STDOUT: ###[/bold]")
        pprint(result.get("log", ""))

    except Exception as e:
        display_error("Error while testing hook ^", e)
