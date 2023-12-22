import logging
from typing import Optional

import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)


dotenv.load_dotenv()


class Settings(BaseSettings):
    API_BASE: str = 'https://you-forgot-to-cd-into-project.com'
    USERNAME: str = ''
    PASSWORD: str = ''

    MAPPING_FILENAME: str = 'mapping.yaml'

    TO_API_BASE: Optional[str] = None
    TO_USERNAME: Optional[str] = None
    TO_PASSWORD: Optional[str] = None

    class Config:
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def API_URL(self):
        return self.API_BASE.rstrip('/') + '/api/v1'

settings = Settings()

if not settings.TO_API_BASE:
    settings.TO_API_BASE = settings.API_BASE
if not settings.TO_USERNAME:
    settings.TO_USERNAME = settings.USERNAME
if not settings.TO_PASSWORD:
    settings.TO_PASSWORD = settings.PASSWORD
