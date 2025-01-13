from enum import Enum, StrEnum
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

MIGRATE_PLANNING_MODE_OBJECT_PLACEHOLDER = "ID-WOULD-BE-CREATED"

MAPPING_SELECTED_ATTRIBUTE = "selected"


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


def display_info(msg: str):
    console = Console()
    console.print(Panel(msg), style="bold")


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


class GIT_CHARACTERS(StrEnum):
    DELETED = "D"
    UPDATED = "M"
    PARTIALLY_UPADTED = "MM"
    CREATED = "??"
    CREATED_STAGED = "A"


QUEUE_ENGINE_ATTRIBUTES = ["dedicated_engine", "engine", "generic_engine"]

settings = None


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
        self.SOURCE_TOKEN = credentials.get(self.SOURCE_DIRNAME, {}).get("token", None)

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
    CREDENTIALS_FILENAME = "credentials.yaml"
    MAPPING_KEYS_ORDER: list = ["comment", "id", "name", "ignore", "targets"]

    TARGET_API_BASE: str = ""
    TARGET_TOKEN: str = "dummy_token"
    TARGET_USERNAME: str = ""
    TARGET_PASSWORD: str = ""

    BOTH_DESTINATIONS: str = "both"
    SOURCE_DIRNAME: str = "source"
    TARGET_DIRNAME: str = "target"
    UNUSED_SCHEMAS: str = "unused_schemas"
    ALL_OBJECTS: str = "all"

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

    NEW_COMMAND_NAME: str = "prd2"

    UPDATE_COMMAND_NAME: str = "update"
    MIGRATE_MAPPING_COMMAND_NAME: str = "migrate-mapping"
    INITIALIZE_COMMAND_NAME: str = "init"
    DOWNLOAD_COMMAND_NAME: str = "pull"
    UPLOAD_COMMAND_NAME: str = "push"
    PURGE_COMMAND_NAME: str = "purge"
    MIGRATE_COMMAND_NAME: str = "release"
    DEPLOY_COMMAND_NAME: str = "deploy"
    DEPLOY_RUN_COMMAND_NAME: str = "run"
    DEPLOY_REVERT_COMMAND_NAME: str = "revert"
    DEPLOY_TEMPLATE_COMMAND_NAME: str = "template"
    DEPLOY_TEMPLATE_INIT_COMMAND_NAME: str = "init"
    HOOK_COMMAND_NAME: str = "hook"
    HOOK_PAYLOAD_COMMAND_NAME: str = "payload"
    HOOK_TEST_COMMAND_NAME: str = "test"

    CONFIG_KEY_API_BASE_URL = "api_base"
    CONFIG_KEY_TOKEN = "token"
    CONFIG_KEY_DIRECTORIES = "directories"
    CONFIG_KEY_SUBDIRECTORIES = "subdirectories"

    # Pull consts
    DOWNLOAD_KEY_ORG_ID = "org_id"
    DOWNLOAD_KEY_REGEX = "regex"

    # Deploy consts
    DEPLOY_IGNORED_DIRS = [".git", "payloads", "deploy_files"]
    DEPLOY_OVERRIDE_REGEX_SEPARATOR = "/#/"
    DEPLOY_DEFAULT_TARGET_URL = "https://my-org.rossum.app/api/v1"
    DEFAULT_DEPLOY_PARENT = "deploy_files"
    DEFAULT_DEPLOY_SECRETS_PARENT = "deploy_secrets"
    DEPLOY_KEY_SECRETS_PATH = "secrets_file"
    DEPLOY_KEY_TARGETS = "targets"
    DEPLOY_KEY_OVERRIDES = "attribute_override"
    DEPLOY_KEY_DEPLOYED_ORG_ID = "deployed_org_id"
    DEPLOY_KEY_LAST_DEPLOYED_AT = "last_deployed_at"
    DEPLOY_KEY_TOKEN_OWNER = "token_owner_id"
    DEPLOY_KEY_SOURCE_DIR = "source_dir"
    DEPLOY_KEY_TARGET_DIR = "target_dir"
    DEPLOY_KEY_SOURCE_URL = "source_url"
    DEPLOY_KEY_TARGET_URL = "target_url"
    DEPLOY_KEY_BASE_PATH = "base_path"
    DEPLOY_KEY_REVERSE_MAPPING = "reverse_mapping_after_deploy"
    DEPLOY_KEY_IGNORE_DEPLOY_WARNINGS = "ignore_deploy_warnings"
    DEPLOY_KEY_UNSELECTED_HOOK_IDS = "unselected_hooks"
    DEPLOY_KEY_PATCH_TARGET_ORG = "patch_target_org"

    DEPLOY_KEY_WORKSPACES = "workspaces"
    DEPLOY_KEY_QUEUES = "queues"
    DEPLOY_KEY_SCHEMA = "schema"
    DEPLOY_KEY_INBOX = "inbox"
    DEPLOY_KEY_HOOKS = "hooks"

    UPDATE_PRINT_STR: str = "[blue]UPDATE[/blue]"
    CREATE_PRINT_STR: str = "[green]CREATE[/green]"
    DELETE_PRINT_STR: str = "[red]DELETE[/red]"
    PLAN_PRINT_STR: str = "[bold]PLAN:[/bold]"

    IGNORED_KEYS: dict = {
        Resource.Queue: ["counts", "users"],
        Resource.Hook: ["status"],
    }

    FORMULA_DIR_NAME: str = "formulas"
    RULES_DIR_NAME: str = "rules"

    @property
    def SOURCE_API_URL(self):
        return self.SOURCE_API_BASE.rstrip("/")

    @property
    def TARGET_API_URL(self):
        return self.TARGET_API_BASE.rstrip("/")


class PrdVersionException(Exception): ...


def migrate_config():
    config_path = Path("./") / Settings.CONFIG_FILENAME

    if config_path.exists():
        return

    credentials_path = Path("./") / Settings.CREDENTIALS_FILENAME
    if not credentials_path.exists():
        return

    credentials = json.loads(credentials_path.read_text())

    config = {
        "source_api_base": credentials.get("source", {}).get("api_base", ""),
        "use_same_org_as_target": credentials.get("use_same_org_as_target", True),
        "target_api_base": credentials.get("target", {}).get("api_base", ""),
    }

    with open(config_path, "w") as wf:
        yaml.dump(config, wf, sort_keys=False)


def initialize_settings():
    global settings
    try:
        migrate_config()
        settings = Settings()

    except Exception as e:
        display_error(f"Error while initializing PRD settings: {str(e)}", e)
        sys.exit(1)


initialize_settings()


class CustomResource(Enum):
    Rule = "rules"
