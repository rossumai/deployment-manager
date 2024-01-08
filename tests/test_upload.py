import pytest

from rossum_api import ElisAPIClient

# Download the reference org

# repull new project for each test

# TEST: change a name, push, pull
# check that there is a file with a different name
# change it back afterwards

# TEST: add some random file, push
# check that it was ignored

# TEST: create object, pull, delete locally, push
# check that after pulling, the object does not exist locally

# TEST: change mapping org target to something else, push
# check that push failed


@pytest.mark.asyncio
async def test_upload_files(client: ElisAPIClient):
    organizations = [org async for org in client.list_all_organizations()]

    print(organizations)
