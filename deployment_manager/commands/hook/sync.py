import difflib
from urllib.parse import urlparse

import questionary
from anyio import Path

from deployment_manager.commands.deploy.subcommands.run.attribute_override import AttributeOverrider
from deployment_manager.commands.hook.helpers import get_git_file_content_from_url_ssh
from deployment_manager.common.read_write import read_yaml, read_prd_project_config
from deployment_manager.utils.consts import display_warning, settings, display_error, display_info

from rich import print as pprint
from rich.panel import Panel

async def sync_hook(destination: Path, aliases: list[str]) -> None:
    if not destination:
        display_warning(
            f"No destination specified to {settings.HOOK_SYNC_COMMAND_NAME}."
        )
        return

    project_path = Path("./")

    hooks_sync_config = read_yaml(project_path/destination/settings.HOOK_MAPPING_FILENAME)
    if aliases:
        # filter only the ones we want to sync
        hooks_to_sync = [i for i in hooks_sync_config if i["alias"] in aliases]
    else:
        hooks_to_sync = hooks_sync_config

    for hook in hooks_to_sync:
        remote_file_path = hook["remote_path"]
        parsed_url = urlparse(remote_file_path)
        if not parsed_url.path.endswith(".py") or not hook["local_path"].endswith(".py"):
            display_error(f"Processing of {hook['alias']} error: Repo path and local path must point to a .py file")
            continue

        # only file path was provided
        if not parsed_url.hostname:
            remote_file_path = f"{settings.GITLAB_SERVERLESS_FUNCTIONS_URL}/{hook['remote_path']}"

        remote_file = get_git_file_content_from_url_ssh(remote_file_path)
        if not remote_file:
            display_error(f"Processing of {hook['alias']} error: Pull from remote unsuccessful.")
            return

        remote_file = remote_file.decode("utf-8")
        with open(hook["local_path"], "r") as local_file:
            local_file = local_file.read()

        code_diff = difflib.unified_diff(local_file.splitlines(), remote_file.splitlines(), fromfile="local", tofile="remote", lineterm="")
        code_diff = "\n".join(list(code_diff))
        formatted_diff = AttributeOverrider.parse_diff(code_diff)
        if not formatted_diff:
            display_info(f"Skipping {hook['alias']}: No changes detected.")
            continue
        pprint(Panel(f"[purple]Differences for alias {hook['alias']}[/purple]:\n{formatted_diff}"))

        overwrite = await questionary.confirm(
            f'Do you want to pull the changes to your local repository?', default=True
        ).ask_async()

        if overwrite:
            with open(hook["local_path"], "w") as local_file:
                local_file.write(remote_file)
            display_info(f"File {hook['local_path']} updated.")
        else:
            display_info(f"Skipping pull to {hook['local_path']}.")

    display_info("Pull completed.")
