from urllib.parse import urlparse

import questionary
from anyio import Path
from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.utils.consts import display_error, display_info, settings
from rich import print as pprint
from ruamel.yaml import YAML


async def create_or_append_sync_template(old_hooks_file: Path = "") -> None:
    old_hooks = []
    if old_hooks_file and await old_hooks_file.exists():
        # load existing hooks from the old file
        old_hooks = YAML().load(await old_hooks_file.read_text())
    hooks = []
    while (
        not len(hooks)
        or await questionary.confirm(
            "Would you like to specify another hook to this template file?"
        ).ask_async()
    ):
        local_path, errors = None, []
        while not local_path or errors:
            local_path = await questionary.text(
                "Local .py hook file path (e.g. org/suborg/hooks/Extension_[123].py)"
            ).ask_async()
            local_path = Path(local_path)
            if not await local_path.exists():
                errors.append("Local hook file does not exist.")
            if not local_path.suffix == ".py":
                errors.append("Local hook file path must end with '.py'.")
            if errors:
                display_error("\n".join(errors))
                local_path, errors = None, []

        remote_path, errors = None, []
        while not remote_path or errors:
            remote_path = await questionary.text(
                "URL to remote script in Gitlab or path from the root directory in elis-serverless-functions (e.g. generic-functions/stable/po-matching/po_matching.py"
            ).ask_async()
            parsed_url = urlparse(remote_path)
            if not parsed_url.path.endswith(".py"):
                errors.append("Remote hook file path must end with '.py'.")
            if errors:
                display_error("\n".join(errors))
                remote_path, errors = None, []

        hooks.append({"local_path": str(local_path), "remote_path": str(remote_path)})

    if old_hooks:
        hooks = old_hooks + hooks

    org_path = Path("./")
    sync_filepath = await get_filepath_from_user(
        org_path,
        default=str(old_hooks_file) or str(Path(settings.DEFAULT_HOOK_SYNC_PARENT) / "deployment.yaml"),
        should_confirm_overwrite=not bool(old_hooks_file)
    )

    await sync_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(sync_filepath, "w") as f:
        YAML().dump(hooks, f)

    display_info(
        f"Deploy file saved to [green]{sync_filepath}[/green]. Use it by running:"
    )

    pprint(
        f'\n  {settings.NEW_COMMAND_NAME} {settings.HOOK_COMMAND_NAME} {settings.HOOK_SYNC_COMMAND_NAME} {settings.DEPLOY_RUN_COMMAND_NAME} "{sync_filepath}"\n'
    )
