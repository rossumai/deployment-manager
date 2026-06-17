import difflib
from urllib.parse import urlparse

import questionary
from anyio import Path
from rich import print as pprint
from rich.panel import Panel

from deployment_manager.commands.deploy.subcommands.run.attribute_override import AttributeOverrider
from deployment_manager.commands.hook.sync.helpers import get_git_file_content_from_url_ssh
from deployment_manager.common.read_write import read_yaml
from deployment_manager.utils.consts import display_error, display_info, settings


async def sync_hook(sync_file: Path) -> None:
    if not await sync_file.exists():
        display_error(f"Sync file {sync_file} does not exist.")
        return
    hook_name = sync_file.name
    hook_data = read_yaml(sync_file)
    if not isinstance(hook_data, list):
        hook_data = [hook_data]

    for hook_to_sync in hook_data:
        local_file_path = Path(hook_to_sync["local_path"])
        local_filename = local_file_path.name
        remote_file_path = hook_to_sync["remote_path"]
        parsed_url = urlparse(remote_file_path)
        if not parsed_url.path.endswith(".py") or not hook_to_sync["local_path"].endswith(".py"):
            display_error(f"Processing of {local_filename} error: Repo path and local path must point to a .py file")
            continue

        # only file path was provided
        if not parsed_url.hostname:
            remote_file_path = f"{settings.GITLAB_SERVERLESS_FUNCTIONS_URL}/{hook_to_sync['remote_path']}"

        remote_file = get_git_file_content_from_url_ssh(remote_file_path)
        if not remote_file:
            display_error(f"Processing of {local_filename} error: Pull from remote unsuccessful.")
            continue

        remote_file = remote_file.decode("utf-8")
        if not await local_file_path.exists():
            display_error(f"Processing of {local_filename} error: Local path does not exist.")
            continue

        with open(local_file_path, "r") as local_file:
            local_file = local_file.read()

        code_diff = difflib.unified_diff(
            local_file.splitlines(),
            remote_file.splitlines(),
            fromfile="local",
            tofile="remote",
            lineterm="",
        )
        code_diff = "\n".join(list(code_diff))
        formatted_diff = AttributeOverrider.parse_diff(code_diff)
        if not formatted_diff:
            display_info(f"Skipping {hook_name}: No changes detected.")
            continue
        pprint(Panel(f"[purple]Differences for alias {hook_name}[/purple]:\n{formatted_diff}"))

        overwrite = await questionary.confirm(
            "Do you want to pull the changes to your local repository?", default=True
        ).ask_async()

        if overwrite:
            with open(hook_to_sync["local_path"], "w") as local_file:
                local_file.write(remote_file)
            display_info(f"File {hook_to_sync['local_path']} updated.")
        else:
            display_info(f"Skipping pull to {hook_to_sync['local_path']}.")

    display_info("Pull completed.")
