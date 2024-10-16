import re
import questionary
from ruamel.yaml import YAML

from project_rossum_deploy.commands.migrate.helpers import get_token_owner
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


async def ensure_token_owner(release, client):
    if not settings.IS_PROJECT_IN_SAME_ORG:
        if not release.token_owner_id:
            token_owner_from_remote = await get_token_owner(client)
            if token_owner_from_remote:
                release.token_owner_id = token_owner_from_remote.id
            else:
                release.token_owner_id = await questionary.text(
                    "Please input user ID of the hook token owner (e.g., 938382):"
                ).ask_async()


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
