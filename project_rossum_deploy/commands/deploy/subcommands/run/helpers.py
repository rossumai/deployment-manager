import re
from typing import Any
from anyio import Path
from ruamel.yaml import YAML

from project_rossum_deploy.commands.deploy.common.helpers import (
    get_api_url_from_config,
    get_token_from_cred_file,
    validate_credentials,
)
from project_rossum_deploy.commands.deploy.common.helpers import get_api_url_from_user
from project_rossum_deploy.commands.deploy.common.helpers import get_token_from_user
from project_rossum_deploy.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from project_rossum_deploy.utils.consts import display_error, settings


class DeployYaml:
    RELEASE_KEYWORD_REGEX = re.compile(r"^release(_(\w)+)?$")

    def __init__(self, file: str):
        self._yaml = YAML()
        # Used also by auto-formatting in VSCode
        self._yaml.indent(mapping=2, sequence=4, offset=2)
        self._yaml.preserve_quotes = True
        self.data = self._yaml.load(file)

    def save_to_file(self, file_path: str | Path):
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
    base_path: Path, org_name: str, type: str, yaml_data: dict
):
    if type == settings.TARGET_DIRNAME:
        api_url = yaml_data.get(settings.DEPLOY_KEY_TARGET_URL, None)
    else:
        api_url = yaml_data.get(settings.DEPLOY_KEY_SOURCE_URL, None)

    if not api_url and org_name:
        api_url = await get_api_url_from_config(base_path=base_path, org_name=org_name)
    if not api_url:
        api_url = await get_api_url_from_user(type=type)

    token = await get_token_from_cred_file(base_path / org_name)
    if not token:
        token = await get_token_from_user(type=type)

    try:
        credentials = Credentials(token=token, url=api_url)
        await validate_credentials(credentials)
        return credentials
    except Exception as e:
        display_error(f"Error while getting credentials for {type}: {str(e)}")

    return None


def traverse_object(parent_object: dict | None, parent_key: str, value: Any):
    if isinstance(value, list):
        for i in value:
            yield from traverse_object(parent_object, parent_key, i)
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from traverse_object(value, k, v)
    elif isinstance(value, str) or isinstance(value, int):
        yield parent_object, parent_key, value
