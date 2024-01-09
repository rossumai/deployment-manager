import io
import os
import subprocess
import pytest
import pytest_asyncio

from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource


from project_rossum_deploy.commands.download.download import download_organization
from project_rossum_deploy.commands.upload import upload_project
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    read_json,
    templatize_name_id,
    write_json,
)
from tests.utils.consts import UPDATED_NAME

# Download the reference org

# repull new project for each test

# TEST: change a name, push, pull
# check that there is a file with a different name
# change it back afterwards

# TEST: add some random file, push
# check that it was ignored

# TEST: modify something in both destinations
# Check that only the selected destination got updated

# TEST: create object, pull, delete locally, push
# check that after pulling, the object does not exist locally

# TEST: change mapping org target to something else, push
# check that push failed


async def setup_project(client: ElisAPIClient, tmp_path):
    await download_organization(client=client, org_path=tmp_path)

    # Commit to a git repo so that the following update can be diffed
    os.chdir(tmp_path)
    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "init"])


@pytest_asyncio.fixture(scope="function")
async def updated_file_tuple(client: ElisAPIClient, tmp_path):
    await setup_project(client, tmp_path)

    updated_file_path = await anext(
        (tmp_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
    )
    updated_file = await read_json(updated_file_path)
    updated_file["active"] = False
    await write_json(updated_file_path, updated_file)

    yield tmp_path, updated_file_path, updated_file

    await client._http_client.update(
        resource=Resource.Hook,
        id_=updated_file["id"],
        data={"active": True},
    )


@pytest.mark.skip
@pytest.mark.asyncio
async def test_push_updated_file(
    client: ElisAPIClient, updated_file_tuple, monkeypatch
):
    tmp_path, updated_file_path, updated_file = updated_file_tuple

    await upload_project(
        destination=settings.SOURCE_DIRNAME, org_path=tmp_path, client=client
    )

    # Confirm configuration overwriting
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    await download_organization(client=client, org_path=tmp_path)
    redownloaded_file = await read_json(updated_file_path)

    assert redownloaded_file == updated_file


@pytest_asyncio.fixture(scope="function")
async def updated_file_name_tuple(client: ElisAPIClient, tmp_path):
    await setup_project(client, tmp_path)

    updated_file_path = await anext(
        (tmp_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
    )
    updated_file = await read_json(updated_file_path)
    previous_name = updated_file["name"]
    updated_file["name"] = UPDATED_NAME
    await write_json(updated_file_path, updated_file)

    yield tmp_path, updated_file_path, updated_file

    await client._http_client.update(
        resource=Resource.Hook,
        id_=updated_file["id"],
        data={"name": previous_name},
    )


@pytest.mark.skip
@pytest.mark.asyncio
async def test_push_updated_file_name_changed(
    client: ElisAPIClient, updated_file_name_tuple, monkeypatch
):
    tmp_path, previous_file_path, updated_file = updated_file_name_tuple

    await upload_project(
        destination=settings.SOURCE_DIRNAME, org_path=tmp_path, client=client
    )

    # Confirm configuration overwriting
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    await download_organization(client=client, org_path=tmp_path)
    redownloaded_file = await read_json(
        previous_file_path.with_stem(
            templatize_name_id(UPDATED_NAME, updated_file["id"])
        )
    )

    assert not (await previous_file_path.exists())
    assert redownloaded_file == updated_file


# @pytest.mark.asyncio
# async def test_push_deleted_file(
#     client: ElisAPIClient, updated_file_name_tuple, monkeypatch
# ):
#     tmp_path, previous_file_path, updated_file = updated_file_name_tuple

#     await upload_project(
#         destination=settings.SOURCE_DIRNAME, org_path=tmp_path, client=client
#     )

#     # Confirm configuration overwriting
#     monkeypatch.setattr("sys.stdin", io.StringIO("y"))
#     await download_organization(client=client, org_path=tmp_path)
#     redownloaded_file = await read_json(
#         previous_file_path.with_stem(
#             templatize_name_id(UPDATED_NAME, updated_file["id"])
#         )
#     )

#     assert not (await previous_file_path.exists())
#     assert redownloaded_file == updated_file
