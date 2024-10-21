import re
from anyio import Path
from pydantic import BaseModel, ValidationError
import questionary
from rossum_api import ElisAPIClient, APIClientError
from ruamel.yaml import YAML

from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import display_error, settings


class DeployYaml:
    RELEASE_KEYWORD_REGEX = re.compile(r"^release(_(\w)+)?$")

    def __init__(self, file: str):
        self._yaml = YAML()
        # Used also by auto-formatting in VSCode
        self._yaml.indent(mapping=2, sequence=4, offset=2)
        self._yaml.preserve_quotes = True
        self.data = self._yaml.load(file)

    def get_object_in_yaml(self, type: str, id: int):
        objects = self.data.get(type, [])
        for object in objects:
            if object.get("id", None) == id:
                return object
        return None

    def save_to_file(self, file_path: str):
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


# TODO: username + password support
class Credentials(BaseModel):
    token: str


# TODO: more robust (all scenarios)
async def get_target_credentials(org_path: Path, yaml_data: dict):
    target_dir = yaml_data.get(settings.DEPLOY_KEY_TARGET_DIR, None)
    target_url = yaml_data[settings.DEPLOY_KEY_TARGET_URL]

    if target_dir:
        target_credentials_path = org_path / target_dir / "credentials.yaml"
        if await target_credentials_path.exists():
            data = await YAML.load(await target_credentials_path.get_text())
        else:
            target_credentials_path = org_path / target_dir / "credentials.json"
            data = await read_json(target_credentials_path)

        try:
            return Credentials(**data)
        except ValidationError:
            display_error(f"Invalid token in {target_credentials_path} try again.")
            return await get_token_from_user(target_url)

    return await get_token_from_user(target_url)


async def get_token_from_user(target_url: str):
    try:
        token = await questionary.text("Enter token for the target API:").ask_async()
        await ElisAPIClient(base_url=target_url, token=token).request(
            "get", "auth/user"
        )
        return Credentials(token=token)
    except APIClientError as e:
        if e.status_code == 401:
            display_error(f'Invalid target API token "{token}" try again.')
            return await get_token_from_user(target_url)
