import os

import pytest
import pytest_asyncio
from anyio import Path

from deployment_manager.common.read_write import read_object_from_json, write_object_to_json
from deployment_manager.utils.consts import settings
from rossum_api import ElisAPIClient

base_url = os.environ.get("SOURCE_API_BASE")
username = os.environ.get("SOURCE_USERNAME")
password = os.environ.get("SOURCE_PASSWORD")


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


target_base_url = os.environ.get("TARGET_API_BASE")
target_username = os.environ.get("TARGET_USERNAME")
target_password = os.environ.get("TARGET_PASSWORD")


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


TEST_DATA_PATH = Path("tests/test_data")


@pytest_asyncio.fixture(scope="function")
async def workspace_json_path(tmp_path):
    data = await read_object_from_json(TEST_DATA_PATH / "workspace.json")
    tmp_ws_path = tmp_path / "workspace.json"
    await write_object_to_json(tmp_ws_path, data)
    return tmp_ws_path


@pytest_asyncio.fixture(scope="function")
async def workspace_json():
    return await read_object_from_json(TEST_DATA_PATH / "workspace.json")
