import pytest

from deployment_manager.commands.download.subdirectory import Subdirectory


@pytest.fixture
def test_subdir():
    return Subdirectory(name="test-subdir", regex="TEST", include=True, object_ids=[])


@pytest.fixture
def prod_subdir():
    return Subdirectory(name="prod-subdir", regex="PROD", include=True, object_ids=[])
