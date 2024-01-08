import io
import os
from anyio import Path
import pytest

from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.download.download import download_organization
from project_rossum_deploy.commands.download.helpers import delete_current_configuration
from tests.utils.compare import compare_projects
from tests.utils.consts import REFERENCE_PROJECT_PATH

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
async def test_fresh_download(client: ElisAPIClient, monkeypatch):
    temp_path = Path("temp_project")
    await temp_path.mkdir(exist_ok=True)

    # Should not be needed for fresh pulls without previous data
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))

    await download_organization(client=client, org_path=temp_path)

    await compare_projects(temp_path, REFERENCE_PROJECT_PATH)

    await delete_current_configuration(temp_path)