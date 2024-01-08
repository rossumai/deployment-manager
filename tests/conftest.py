import pytest
from rossum_api import ElisAPIClient


@pytest.fixture
def client():
    return ElisAPIClient(
        base_url="https://rdttest.rossum.app/api/v1",
        username="jan.sporek+rdttest@rossum.ai",
        password="^sE*bXs28%Hk%tMi9%Qtk@",
    )
