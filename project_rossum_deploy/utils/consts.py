from enum import StrEnum
import logging

import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)


dotenv.load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    API_BASE: str = "https://you-forgot-to-cd-into-project.com"
    TOKEN: str = ""
    USERNAME: str = ""
    PASSWORD: str = ""

    MAPPING_FILENAME: str = "mapping.yaml"

    TO_API_BASE: str = ""
    TO_TOKEN: str = ""
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
        return self.API_BASE.rstrip("/") + "/api/v1"

    @property
    def TO_API_URL(self):
        return self.TO_API_BASE.rstrip("/") + "/api/v1"


settings = Settings()


class GIT_CHARACTERS(StrEnum):
    DELETED = "D"
    UPDATED = "M"
    CREATED = "??"


# Outside of Settings so that it can be referenced
PUSH_IGNORED_FIELDS = [settings.MAPPING_FILENAME, ".gitignore"]
