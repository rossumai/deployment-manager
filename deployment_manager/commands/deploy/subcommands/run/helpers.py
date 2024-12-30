from datetime import datetime, timezone
import re
from typing import Any
from anyio import Path
import questionary
from ruamel.yaml import YAML

from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.commands.deploy.common.helpers import (
    get_api_url_from_config,
    get_token_from_cred_file,
    validate_credentials,
)
from deployment_manager.commands.deploy.common.helpers import get_api_url_from_user
from deployment_manager.commands.deploy.common.helpers import get_token_from_user
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from deployment_manager.utils.consts import display_error, settings


class DeployYaml:
    RELEASE_KEYWORD_REGEX = re.compile(r"^release(_(\w)+)?$")

    def __init__(self, file: str):
        self._yaml = YAML()
        # Used also by auto-formatting in VSCode
        self._yaml.indent(mapping=2, sequence=4, offset=2)
        self._yaml.preserve_quotes = True
        self.data = self._yaml.load(file)

    async def save_to_file(self, file_path: str | Path):
        if file_path.parent and file_path.parent != file_path:
            await file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as wf:
            self._yaml.dump(self.data, wf)


def check_required_keys(release: dict):
    required_keys = [settings.DEPLOY_KEY_SOURCE_DIR, settings.DEPLOY_KEY_TARGET_URL]
    missing_keys = []

    for req_key in required_keys:
        if req_key not in release:
            missing_keys.append(req_key)

    if missing_keys:
        display_error(f"Release is missing the following required keys: {missing_keys}")
        return False
    else:
        return True


# TODO: more robust (all scenarios)
# TODO: prompt user for new token and store it
# TODO: username + password support
async def get_url_and_credentials(
    project_path: Path, org_name: str = "", type: str = "", yaml_data: dict = None
):
    api_url = ""
    if type == settings.TARGET_DIRNAME and yaml_data:
        api_url = yaml_data.get(settings.DEPLOY_KEY_TARGET_URL, None)
    elif type == settings.SOURCE_DIRNAME and yaml_data:
        api_url = yaml_data.get(settings.DEPLOY_KEY_SOURCE_URL, None)

    if not api_url and org_name:
        api_url = await get_api_url_from_config(
            base_path=project_path, org_name=org_name
        )
    if not api_url:
        api_url = await get_api_url_from_user(type=type)

    token = await get_token(
        project_path=project_path, org_name=org_name, api_url=api_url, type=type
    )

    try:
        credentials = Credentials(token=token, url=api_url)
        await validate_credentials(credentials)
        return credentials
    except Exception as e:
        display_error(f"Error while getting credentials for {type}: {str(e)}")

    return None


# TODO: move to a more common file
async def get_token(project_path: Path, org_name: str, api_url: str, type: str = ""):
    token = await get_token_from_cred_file(project_path / org_name, api_url=api_url)
    if not token:
        token = await get_token_from_user(name=type if type else org_name)
    return token


def traverse_object(parent_object: dict | None, parent_key: str, value: Any):
    if isinstance(value, list):
        for i in value:
            yield from traverse_object(parent_object, parent_key, i)
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from traverse_object(value, k, v)
    elif isinstance(value, str) or isinstance(value, int):
        yield parent_object, parent_key, value


async def get_new_deploy_file_path(
    deploy_file_path: Path,
    first_deploy: bool,
    suffix: str = "_deployed",
):
    if first_deploy:
        after_deploy_file_path = deploy_file_path.with_stem(
            f"{deploy_file_path.stem}{suffix}"
        )
        if await after_deploy_file_path.exists():
            overwrite = await questionary.confirm(
                f'File "{after_deploy_file_path}" already exists. Overwrite?',
                default=False,
            ).ask_async()
            if not overwrite:
                after_deploy_file_path = await get_filepath_from_user(
                    deploy_file_path.parent
                )
    else:
        after_deploy_file_path = deploy_file_path

    return after_deploy_file_path


def update_ignore_flags_in_yaml(yaml_data: dict, ignore_warning_flags: dict):
    for queue in yaml_data[settings.DEPLOY_KEY_QUEUES]:
        if (queue_id := queue.get("id", None)) not in ignore_warning_flags:
            continue
        queue[settings.DEPLOY_KEY_IGNORE_DEPLOY_WARNINGS] = ignore_warning_flags.get(
            queue_id, False
        )


def generate_deploy_timestamp():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )
