from enum import StrEnum
import json
import logging
import os
from pathlib import Path
import re

import click

from project_rossum_deploy.utils.functions import adjust_keys


logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)

DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"

API_SUFFIX_RE = re.compile(r"/api/v\d+$")


class Settings:
    def __init__(self):
        cred_path = Path("./") / self.CREDENTIALS_FILENAME
        if not cred_path.exists():
            raise click.ClickException(
                f"{self.CREDENTIALS_FILENAME} not found in the current directory."
            )
        credentials = json.loads(cred_path.read_text())
        credentials = adjust_keys(credentials)

        self.API_BASE = credentials["source"]["api_base"]
        self.USERNAME = credentials["source"].get("username", None)
        self.PASSWORD = credentials["source"].get("password", None)
        self.TOKEN = credentials["source"].get("token", None)

        if not credentials.get("use_same_org_as_target", False):
            self.IS_PROJECT_IN_SAME_ORG = False
            if "target" not in credentials:
                raise click.ClickException(
                    'Missing target credentials. If you are targetting the same org, set "use_same_org_as_target": true.'
                )
            self.TO_API_BASE = credentials["target"]["api_base"]
            self.TO_USERNAME = credentials["target"].get("username", None)
            self.TO_PASSWORD = credentials["target"].get("password", None)
            self.TO_TOKEN = credentials["target"].get("token", None)

            # Can't fool us that easily
            if self.API_BASE == self.TO_API_BASE and (
                (
                    self.USERNAME == self.TO_USERNAME
                    and self.PASSWORD == self.TO_PASSWORD
                )
                or self.TOKEN == self.TO_TOKEN
            ):
                self.IS_PROJECT_IN_SAME_ORG = True
        else:
            self.IS_PROJECT_IN_SAME_ORG = True
            self.TO_API_BASE = credentials["source"]["api_base"]
            self.TO_USERNAME = credentials["source"].get("username", None)
            self.TO_PASSWORD = credentials["source"].get("password", None)
            self.TO_TOKEN = credentials["source"].get("token", None)

    IS_PROJECT_IN_SAME_ORG: bool = False

    API_BASE: str = "https://you-forgot-to-cd-into-project.com"
    # Empty string gives an API error even if there is username and password
    TOKEN: str = "dummy_token"
    USERNAME: str = ""
    PASSWORD: str = ""

    MAPPING_FILENAME: str = "mapping.yaml"
    CREDENTIALS_FILENAME: str = "credentials.json"

    TO_API_BASE: str = ""
    TO_TOKEN: str = "dummy_token"
    TO_USERNAME: str = ""
    TO_PASSWORD: str = ""

    SOURCE_DIRNAME: str = "source"
    TARGET_DIRNAME: str = "target"

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

    INITIALIZE_COMMAND_NAME: str = "init"
    DOWNLOAD_COMMAND_NAME: str = "pull"
    UPLOAD_COMMAND_NAME: str = "push"
    MIGRATE_COMMAND_NAME: str = "release"

    @property
    def API_URL(self):
        return self.API_BASE.rstrip("/")

    @property
    def TO_API_URL(self):
        return self.TO_API_BASE.rstrip("/")


class GIT_CHARACTERS(StrEnum):
    DELETED = "D"
    UPDATED = "M"
    CREATED = "??"


settings = Settings()
