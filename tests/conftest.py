import pytest
from rossum_api import ElisAPIClient


@pytest.fixture
def client():
    return ElisAPIClient()
