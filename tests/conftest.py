import os
from anyio import Path
import pytest
from rossum_api import ElisAPIClient

from project_rossum_deploy.utils.consts import settings

base_url = os.getenv("SOURCE_API_BASE")
username = os.getenv("SOURCE_USERNAME")
password = os.getenv("SOURCE_PASSWORD")


@pytest.fixture
def client():
    settings.SOURCE_API_BASE = base_url
    settings.SOURCE_USERNAME = username
    settings.TARGET_PASSWORD = password
    settings.TARGET_API_BASE = base_url
    settings.SOURCE_USERNAME = username
    settings.TARGET_PASSWORD = password
    return ElisAPIClient(
        base_url=base_url,
        username=username,
        password=password,
    )


target_base_url = os.getenv("TARGET_API_BASE")
target_username = os.getenv("TARGET_USERNAME")
target_password = os.getenv("TARGET_PASSWORD")


@pytest.fixture
def target_client():
    settings.SOURCE_API_BASE = base_url
    settings.SOURCE_USERNAME = username
    settings.SOURCE_PASSWORD = password
    settings.TARGET_API_BASE = target_base_url
    settings.TARGET_USERNAME = target_username
    settings.TARGET_PASSWORD = target_password

    return ElisAPIClient(
        base_url=target_base_url,
        username=target_username,
        password=target_password,
    )


# To use anyio instead of pathlib
@pytest.fixture(scope="function")
def tmp_path(tmp_path):
    return Path(tmp_path)
