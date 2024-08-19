from enum import StrEnum
import json
import logging
from pathlib import Path
import re
import sys
import click
import httpx

from rich.prompt import Prompt
from rich.console import Console
from rich.panel import Panel
from rossum_api.api_client import Resource
import yaml


logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)


API_SUFFIX_RE = re.compile(r"/api/v\d+$")

ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD = "$prd_ref"
ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD = "$source_value"


def display_error(error_msg: str, exception: Exception = None):
    console = Console()
    if exception:
        logging.exception(exception)
    console.print(Panel(error_msg), style="bold red")


def display_warning(msg: str, exception: Exception = None):
    console = Console()
    if exception:
        logging.exception(exception)
    console.print(Panel(msg), style="bold yellow")


def validate_token(base_url: str, token: str, destination: str):
    req = httpx.get(
        url=base_url + "/auth/user",
        headers={"Authorization": f"Bearer {token}"},
    )
    is_token_valid = req.status_code == 200

    if not is_token_valid:
        new_token = Prompt.ask(
            f"Token for {base_url} is invalid or expired. Provide a new one"
        )
        req = httpx.get(
            url=base_url + "/auth/user",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        is_token_valid = req.status_code == 200

        if is_token_valid:
            cred_path = Path("./") / settings.CREDENTIALS_FILENAME
            credentials = json.load(cred_path.open("r"))
            if destination == "source":
                settings.SOURCE_TOKEN = new_token
            elif destination == "target":
                settings.TARGET_TOKEN = new_token
            credentials[destination]["token"] = new_token
            json.dump(credentials, cred_path.open("w"), indent=2)
        else:
            raise click.ClickException(f"Token for {base_url} is invalid or expired.")


try:

    class Settings:
        def __init__(self):
            cred_path = Path("./") / self.CREDENTIALS_FILENAME
            if not cred_path.exists():
                return
            credentials = json.loads(cred_path.read_text())

            if not isinstance(credentials, dict):
                raise click.ClickException(
                    f"{self.CREDENTIALS_FILENAME} is not a valid dictionary."
                )

            config_path = Path("./") / self.CONFIG_FILENAME
            if not config_path.exists():
                return
            config = yaml.safe_load(config_path.open("r"))

            if not isinstance(config, dict):
                raise click.ClickException(
                    f"{self.CONFIG_FILENAME} is not a valid dictionary."
                )

            self.SOURCE_API_BASE = config.get("source_api_base")

            self.SOURCE_USERNAME = credentials.get(self.SOURCE_DIRNAME, {}).get(
                "username", None
            )
            self.SOURCE_PASSWORD = credentials.get(self.SOURCE_DIRNAME, {}).get(
                "password", None
            )
            self.SOURCE_TOKEN = credentials.get(self.SOURCE_DIRNAME, {}).get(
                "token", None
            )

            if not config.get("use_same_org_as_target", False):
                self.IS_PROJECT_IN_SAME_ORG = False
                if "target" not in credentials:
                    raise click.ClickException(
                        f'Missing target credentials. If you are targetting the same org, set "use_same_org_as_target": true in {self.CONFIG_FILENAME}.'
                    )
                self.TARGET_API_BASE = config.get("target_api_base")

                self.TARGET_USERNAME = credentials.get(self.TARGET_DIRNAME, {}).get(
                    "username", None
                )
                self.TARGET_PASSWORD = credentials.get(self.TARGET_DIRNAME, {}).get(
                    "password", None
                )
                self.TARGET_TOKEN = credentials.get(self.TARGET_DIRNAME, {}).get(
                    "token", None
                )
            else:
                self.IS_PROJECT_IN_SAME_ORG = True

        IS_PROJECT_IN_SAME_ORG: bool = False

        SOURCE_API_BASE: str = ""
        # Empty string gives an API error even if there is username and password
        SOURCE_TOKEN: str = "dummy_token"
        SOURCE_USERNAME: str = ""
        SOURCE_PASSWORD: str = ""

        MAPPING_FILENAME: str = "mapping.yaml"
        CONFIG_FILENAME: str = "prd_config.yaml"
        CREDENTIALS_FILENAME: str = "credentials.json"
        MAPPING_KEYS_ORDER: list = ["comment", "id", "name", "ignore", "targets"]

        TARGET_API_BASE: str = ""
        TARGET_TOKEN: str = "dummy_token"
        TARGET_USERNAME: str = ""
        TARGET_PASSWORD: str = ""

        BOTH_DESTINATIONS: str = "both"
        SOURCE_DIRNAME: str = "source"
        TARGET_DIRNAME: str = "target"
        UNUSED_SCHEMAS: str = "unused_schemas"

        ORGANIZATION_FIELDS: list[str] = ["ui_settings", "metadata"]
        PRIVATE_HOOK_DUMMY_URL: str = "https://example.com"
        MAPPING_UPPERCASE_FIELDS: list[str] = [
            "organization",
            "workspaces",
            "queues",
            "inbox",
            "schemas",
            "hooks",
        ]
        MAPPING_TRAVERSE_IGNORE_FIELDS: list[str] = ["targets"]

        MIGRATE_MAPPING_COMMAND_NAME: str = "migrate-mapping"
        INITIALIZE_COMMAND_NAME: str = "init"
        DOWNLOAD_COMMAND_NAME: str = "pull"
        UPLOAD_COMMAND_NAME: str = "push"
        PURGE_COMMAND_NAME: str = "purge"
        MIGRATE_COMMAND_NAME: str = "release"

        IGNORED_KEYS: dict = {
            Resource.Queue: ["counts", "users", "workflows"],
            Resource.Hook: ["status"],
        }

        FORMULA_DIR_PREFIX: str = "formulas:"

        @property
        def SOURCE_API_URL(self):
            return self.SOURCE_API_BASE.rstrip("/")

        @property
        def TARGET_API_URL(self):
            return self.TARGET_API_BASE.rstrip("/")

    class GIT_CHARACTERS(StrEnum):
        DELETED = "D"
        UPDATED = "M"
        PARTIALLY_UPADTED = "MM"
        CREATED = "??"
        CREATED_STAGED = "A"

    settings = Settings()

    if not settings.IS_PROJECT_IN_SAME_ORG:
        settings.IGNORED_KEYS[Resource.Queue].extend(
            ["dedicated_engine", "engine", "generic_engine"]
        )

except Exception as e:
    display_error(f"Error while initializing PRD settings: {str(e)}", e)
    sys.exit(1)


class PrdVersionException(Exception): ...


def create_mismatch_warning(resource, id):
    return f'WARNING: Could not {settings.UPLOAD_COMMAND_NAME} {resource} with ID "{id}". Rossum has a version with a different timestamp.\n This means that the object was updated without PRD. Please stash your changes for these objects and run {settings.DOWNLOAD_COMMAND_NAME} first or use the --force option.'
