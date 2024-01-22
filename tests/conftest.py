import os
from anyio import Path
import pytest
from rossum_api import ElisAPIClient

from project_rossum_deploy.utils.consts import settings

os.environ["DEBUG"] = "true"

base_url = "https://rdttest.rossum.app/api/v1"
username = "jan.sporek+rdttest@rossum.ai"
password = "^sE*bXs28%Hk%tMi9%Qtk@"


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


target_base_url = "https://deploymenttoolprod.rossum.app/api/v1"
target_username = "jan.sporek+deploymenttoolprod@rossum.ai"
target_password = "pZg!&DB5%zH4t*5AY5689V"


@pytest.fixture
def target_client():
    return ElisAPIClient(
        base_url=target_base_url,
        username=target_username,
        password=target_password,
    )


# To use anyio instead of pathlib
@pytest.fixture(scope="function")
def tmp_path(tmp_path):
    return Path(tmp_path)
