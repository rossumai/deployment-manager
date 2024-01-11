import os
from anyio import Path
import pytest
from rossum_api import ElisAPIClient

os.environ['DEBUG'] = 'true'

@pytest.fixture
def client():
    return ElisAPIClient(
        base_url="https://rdttest.rossum.app/api/v1",
        username="jan.sporek+rdttest@rossum.ai",
        password="^sE*bXs28%Hk%tMi9%Qtk@",
    )


# To use anyio instead of pathlib
@pytest.fixture(scope="function")
def tmp_path(tmp_path):
    return Path(tmp_path)
