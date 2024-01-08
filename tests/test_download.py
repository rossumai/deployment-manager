import pytest

from rossum_api import ElisAPIClient

# Download the reference org

# repull new project for each test
# check = mapping is correct + correct files

# TEST: compare pull and reference

# TEST: Change something on Rossum, pull and see if the change was there
# Changes: remove reference, different name
# Revert back afterwards

# TEST: Create object and pull
# check that it is put either into source or target based on user
# check that objects like queues are determined automatically
# Revert back afterwards

# TEST: Create object and pull, delete object in Rossum
# check that the file is no longer present


@pytest.mark.asyncio
async def test_download_files(client: ElisAPIClient):
    organizations = [org async for org in client.list_all_organizations()]

    print(organizations)
