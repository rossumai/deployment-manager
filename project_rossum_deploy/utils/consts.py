from enum import StrEnum
import json
import logging
import os
from pathlib import Path
import re
import sys
import click
import httpx

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)

DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"

API_SUFFIX_RE = re.compile(r"/api/v\d+$")

ATTRIBUTE_OVERRIDE_TARGET_REFERENCE_KEYWORD = "$prd_ref"
ATTRIBUTE_OVERRIDE_SOURCE_REFERENCE_KEYWORD = "$source_value"

FORMULA_SEPARATOR = "### PRD-only, do not remove this line ##################################"

FORMULA_HEADER = """from project_rossum_deploy.utils.formula_builtins import (
    D,  # noqa: F401
    date,  # noqa: F401
    fallback,  # noqa: F401
    is_set,  # noqa: F401
    timedelta,  # noqa: F401
    re,  # noqa: F401
    substitute,  # noqa: F401
)
import unittest.mock

fields = unittest.mock.Mock()
# Add dummy values to test:
{header_mock_fields}

row = unittest.mock.Mock()
# Add dummy values to test:
{line_item_mock_fields}

### PRD-only, do not remove this line ##################################


"""

FORMULA_FOOTER = """


### PRD-only, do not remove this line ##################################

# Add the variable to be returned:
if __name__ == '__main__':
    print()
"""

try:

    class Settings:
        def __init__(self):
            def validate_token(base_url: str, token: str) -> bool:
                req = httpx.get(
                    url=base_url + "/auth/user",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if req.status_code == 200:
                    return True
                return False

            if DEBUG_MODE:
                return

            cred_path = Path("./") / self.CREDENTIALS_FILENAME
            if not cred_path.exists():
                click.echo(
                    f"WARNING: {self.CREDENTIALS_FILENAME} not found in the current directory."
                )
                return

            credentials = json.loads(cred_path.read_text())

            self.SOURCE_API_BASE = credentials["source"]["api_base"]
            self.SOURCE_USERNAME = credentials["source"].get("username", None)
            self.SOURCE_PASSWORD = credentials["source"].get("password", None)
            self.SOURCE_TOKEN = credentials["source"].get("token", None)
            if self.SOURCE_TOKEN:
                token_valid = validate_token(self.SOURCE_API_BASE, self.SOURCE_TOKEN)
                if not token_valid:
                    raise click.ClickException("Source token is invalid or expired.")

            if not credentials.get("use_same_org_as_target", False):
                self.IS_PROJECT_IN_SAME_ORG = False
                if "target" not in credentials or not credentials.get("target", {}).get(
                    "api_base", ""
                ):
                    raise click.ClickException(
                        'Missing target credentials. If you are targetting the same org, set "use_same_org_as_target": true.'
                    )
                self.TARGET_API_BASE = credentials["target"]["api_base"]
                self.TARGET_USERNAME = credentials["target"].get("username", None)
                self.TARGET_PASSWORD = credentials["target"].get("password", None)
                self.TARGET_TOKEN = credentials["target"].get("token", None)
                if self.TARGET_TOKEN:
                    token_valid = validate_token(
                        self.TARGET_API_BASE, self.TARGET_TOKEN
                    )
                    if not token_valid:
                        raise click.ClickException(
                            "Target token is invalid or expired."
                        )
            else:
                self.IS_PROJECT_IN_SAME_ORG = True
                self.TARGET_API_BASE = credentials["source"]["api_base"]
                self.TARGET_USERNAME = credentials["source"].get("username", None)
                self.TARGET_PASSWORD = credentials["source"].get("password", None)
                self.TARGET_TOKEN = credentials["source"].get("token", None)

        IS_PROJECT_IN_SAME_ORG: bool = False

        SOURCE_API_BASE: str = "https://you-forgot-to-cd-into-project.com"
        # Empty string gives an API error even if there is username and password
        SOURCE_TOKEN: str = "dummy_token"
        SOURCE_USERNAME: str = ""
        SOURCE_PASSWORD: str = ""

        MAPPING_FILENAME: str = "mapping.yaml"
        CREDENTIALS_FILENAME: str = "credentials.json"
        MAPPING_KEYS_ORDER: list = ["id", "name", "target_object"]

        TARGET_API_BASE: str = ""
        TARGET_TOKEN: str = "dummy_token"
        TARGET_USERNAME: str = ""
        TARGET_PASSWORD: str = ""

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

        IGNORED_KEYS: dict = {"queue": ["counts"]}

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
        CREATED = "??"
        CREATED_STAGED = "A"

    settings = Settings()

except Exception as e:
    logging.error(f"Error while initializing PRD settings: {e}")
    sys.exit(1)
