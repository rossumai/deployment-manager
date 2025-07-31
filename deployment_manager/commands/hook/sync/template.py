from urllib.parse import urlparse

import questionary
from ruamel.yaml import YAML

from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.commands.deploy.common.helpers import (
    get_api_url_from_config,
    get_api_url_from_user,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.template.helpers import (
    add_override_to_deploy_file_objects,
    add_targets_from_mapping,
    create_deploy_file_template,
    get_attribute_overrides_from_user,
    get_hooks_from_user,
    get_multi_targets_from_user,
    get_queues_from_user,
    get_dir_and_subdir_from_user,
    get_secrets_from_user,
    get_workspaces_from_user,
)
from deployment_manager.common.mapping import read_mapping
from deployment_manager.common.read_write import read_object_from_json, write_object_to_json
from deployment_manager.utils.consts import display_error, display_info, settings

from rich import print as pprint
from anyio import Path
from rossum_api import ElisAPIClient


async def create_sync_template(
):
    local_path = await questionary.text(
        "Local .py hook file path (e.g. org/suborg/hooks/Extension_[123].py)"
    ).ask_async()
    local_path = Path(local_path)
    if not await local_path.exists():
        display_error("Local hook file does not exist")
        return
    if not local_path.suffix == ".py":
        display_error("Local hook file path must end with '.py'.")
        return

    remote_path = await questionary.text(
        "URL to remote script in Gitlab or path from the root directory in elis-serverless-functions (e.g. generic-functions/stable/po-matching/po_matching.py"
    ).ask_async()
    parsed_url = urlparse(remote_path)
    if not parsed_url.path.endswith(".py"):
        display_error("Remote hook file path must end with '.py'.")
        return

    org_path = Path("./")
    default_deploy_name = local_path.name.split("_")[0] + ".yaml"
    sync_filepath = await get_filepath_from_user(
        org_path,
        default=str(Path(settings.DEFAULT_HOOK_SYNC_PARENT)/default_deploy_name)
        ,
    )

    await sync_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(sync_filepath, "w") as f:
        YAML().dump({"local_path": str(local_path), "remote_path": str(remote_path)}, f)

    display_info(
        f"Deploy file saved to [green]{sync_filepath}[/green]. Use it by running:"
    )

    pprint(
        f"\n  {settings.NEW_COMMAND_NAME} {settings.HOOK_COMMAND_NAME} {settings.HOOK_SYNC_COMMAND_NAME} {settings.DEPLOY_RUN_COMMAND_NAME} \"{sync_filepath}\"\n"
    )
