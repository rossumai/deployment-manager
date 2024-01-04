from enum import StrEnum
import logging
from typing import Optional

import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)


dotenv.load_dotenv()


class Settings(BaseSettings):
    API_BASE: str = "https://you-forgot-to-cd-into-project.com"
    USERNAME: str = ""
    PASSWORD: str = ""

    MAPPING_FILENAME: str = "mapping.yaml"

    TO_API_BASE: Optional[str] = None
    TO_USERNAME: Optional[str] = None
    TO_PASSWORD: Optional[str] = None

    SOURCE_DIRNAME: str = "source"
    TARGET_DIRNAME: str = "target"

    ORGANIZATION_FIELDS: list[str] = ["ui_settings", "metadata"]

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

    class Config:
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def API_URL(self):
        return self.API_BASE.rstrip("/") + "/api/v1"

    @property
    def TO_API_URL(self):
        return self.TO_API_BASE.rstrip("/") + "/api/v1"


settings = Settings()

class GIT_CHARACTERS(StrEnum):
    DELETED = 'D'
    UPDATED = 'M'
    CREATED = '??'

# Outside of Settings so that it can be referenced
PUSH_IGNORED_FIELDS = [
    settings.MAPPING_FILENAME,
    '.gitignore'
]