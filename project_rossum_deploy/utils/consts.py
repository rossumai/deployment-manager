from enum import StrEnum
import logging
import os
import re

import dotenv
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)

dotenv.load_dotenv(dotenv_path=".env", override=True, verbose=True)

DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"

API_SUFFIX_RE = re.compile(r"/api/v\d+$")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_BASE: str = "https://you-forgot-to-cd-into-project.com"

    @field_validator("API_BASE")
    @classmethod
    def check_api_base_suffix(cls, v: str) -> str:
        if DEBUG_MODE:
            return v

        if not bool(API_SUFFIX_RE.search(v)):
            raise ValueError('API_BASE must end with "/api/v*".')
        return v

    # Empty string gives an API error even if there is username and password
    TOKEN: str = "dummy_token"
    USERNAME: str = ""
    PASSWORD: str = ""

    @model_validator(mode="after")
    def check_token_or_username_password(self) -> "Settings":
        if DEBUG_MODE:
            return self

        if not self.TOKEN and (not self.USERNAME or not self.PASSWORD):
            raise ValueError(
                "Either TOKEN or USERNAME+PASSWORD have to be defined in .env."
            )
        return self

    MAPPING_FILENAME: str = "mapping.yaml"

    TO_API_BASE: str = ""

    @field_validator("TO_API_BASE")
    @classmethod
    def check_to_api_base_suffix(cls, v: str) -> str:
        if DEBUG_MODE:
            return v

        if v and not bool(API_SUFFIX_RE.search(v)):
            raise ValueError('TO_API_BASE must end with "/api/v*".')
        return v

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


settings = Settings()


class GIT_CHARACTERS(StrEnum):
    DELETED = "D"
    UPDATED = "M"
    CREATED = "??"
