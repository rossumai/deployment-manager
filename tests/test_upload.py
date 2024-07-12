import asyncio
import dataclasses
import os
import subprocess
from anyio import Path
import pytest
import pytest_asyncio

from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource


from project_rossum_deploy.commands.download.download import (
    download_organization_combined_source_target,
)
from project_rossum_deploy.common.mapping import read_mapping, write_mapping
from project_rossum_deploy.commands.upload.upload import upload_project
from project_rossum_deploy.common.read_write import read_json, write_json
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import (
    templatize_name_id,
)
from tests.utils.compare import is_object_equal
from tests.utils.consts import UPDATED_NAME

# TEST: change mapping org target to something else, push
# check that push failed


async def setup_project(client: ElisAPIClient, tmp_path):
    await download_organization_combined_source_target(client=client, org_path=tmp_path)

    # Commit to a git repo so that the following update can be diffed
    current_path = Path(__file__).parent.parent
    os.chdir(tmp_path)
    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "init"])
    os.chdir(current_path)


@pytest_asyncio.fixture(scope="function")
async def updated_file_tuple(client: ElisAPIClient, tmp_path):
    await setup_project(client, tmp_path)

    updated_file_path = await anext(
        (tmp_path / settings.SOURCE_DIRNAME / "hooks").iterdir()
    )
    updated_file = await read_json(updated_file_path)
    updated_file["active"] = False
    await write_json(updated_file_path, updated_file)

    settings.IS_PROJECT_IN_SAME_ORG = True

    # The command must be run from the directory because it is running 'git status' internally
    os.chdir(tmp_path)

    yield tmp_path, updated_file_path, updated_file

    await client._http_client.update(
        resource=Resource.Hook,
        id_=updated_file["id"],
        data={"active": True},
    )


@pytest.mark.asyncio
async def test_push_updated_file(
    client: ElisAPIClient, updated_file_tuple, monkeypatch: pytest.MonkeyPatch
):
    tmp_path, updated_file_path, updated_file = updated_file_tuple

    await upload_project(destination=settings.SOURCE_DIRNAME, client=client)

    redownloaded_file = await read_json(updated_file_path)

    assert is_object_equal(redownloaded_file, updated_file)


@pytest.mark.asyncio
async def test_push_ignored_non_staged_file(
    client: ElisAPIClient, updated_file_tuple, monkeypatch: pytest.MonkeyPatch
):
    tmp_path, updated_file_path, updated_file = updated_file_tuple

    await upload_project(
        destination=settings.SOURCE_DIRNAME, client=client, indexed_only=True
    )

    redownloaded_file = await client.retrieve_hook(updated_file["id"])
    assert redownloaded_file.active is True


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

    settings.IS_PROJECT_IN_SAME_ORG = True

    # The command must be run from the directory because it is running 'git status' internally
    os.chdir(tmp_path)

    yield tmp_path, updated_file_path, updated_file

    await client._http_client.update(
        resource=Resource.Hook,
        id_=updated_file["id"],
        data={"name": previous_name},
    )


@pytest.mark.asyncio
async def test_push_updated_file_name_changed(
    client: ElisAPIClient, updated_file_name_tuple, monkeypatch: pytest.MonkeyPatch
):
    tmp_path, previous_file_path, updated_file = updated_file_name_tuple

    await upload_project(destination=settings.SOURCE_DIRNAME, client=client)

    redownloaded_file = await read_json(
        previous_file_path.with_stem(
            templatize_name_id(UPDATED_NAME, updated_file["id"])
        )
    )

    assert not (await previous_file_path.exists())
    assert is_object_equal(redownloaded_file, updated_file)


@pytest_asyncio.fixture(scope="function")
async def source_and_target_schema(client: ElisAPIClient, tmp_path, monkeypatch):
    source_schema = await client.create_new_schema(
        {"name": "source_schema", "content": []}
    )
    target_schema = await client.create_new_schema(
        {"name": "target_schema", "content": []}
    )

    await download_organization_combined_source_target(client, org_path=tmp_path)

    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    mapping["organization"]["schemas"][0]["targets"][0] = {
        "target_id": target_schema.id
    }
    await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)

    await setup_project(client, tmp_path)

    settings.IS_PROJECT_IN_SAME_ORG = True
    # The command must be run from the directory because it is running 'git status' internally
    os.chdir(tmp_path)

    yield source_schema, target_schema

    # In case our test failed to delete the schema(s)
    try:
        await asyncio.gather(
            *[
                client.delete_schema(source_schema.id),
                client.delete_schema(target_schema.id),
            ]
        )
    except Exception:
        print("Schema already deleted.")


@pytest.mark.asyncio
async def test_push_ignores_file_from_target(
    client: ElisAPIClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_and_target_schema,
):
    source_schema, target_schema = source_and_target_schema

    source_schema_path = (
        tmp_path
        / settings.SOURCE_DIRNAME
        / "schemas"
        / f"{templatize_name_id(source_schema.name, source_schema.id)}.json"
    )
    updated_source_schema = await read_json(source_schema_path)
    updated_source_schema["metadata"] = {"key": "value"}
    await write_json(source_schema_path, updated_source_schema)

    target_schema_path = (
        tmp_path
        / settings.TARGET_DIRNAME
        / "schemas"
        / f"{templatize_name_id(target_schema.name, target_schema.id)}.json"
    )
    updated_target_schema = await read_json(target_schema_path)
    updated_target_schema["metadata"] = {"key": "value"}
    await write_json(target_schema_path, updated_target_schema)

    await upload_project(destination=settings.SOURCE_DIRNAME, client=client)

    redownloaded_source_schema = await read_json(source_schema_path)
    redownloaded_target_schema = await client.retrieve_schema(target_schema.id)

    assert is_object_equal(redownloaded_source_schema, updated_source_schema)
    assert dataclasses.asdict(redownloaded_target_schema)["metadata"] == {}


@pytest.mark.asyncio
async def test_push_ignores_file_from_source(
    client: ElisAPIClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_and_target_schema,
):
    source_schema, target_schema = source_and_target_schema

    source_schema_path = (
        tmp_path
        / settings.SOURCE_DIRNAME
        / "schemas"
        / f"{templatize_name_id(source_schema.name, source_schema.id)}.json"
    )
    updated_source_schema = await read_json(source_schema_path)
    updated_source_schema["metadata"] = {"key": "value"}
    await write_json(source_schema_path, updated_source_schema)

    target_schema_path = (
        tmp_path
        / settings.TARGET_DIRNAME
        / "schemas"
        / f"{templatize_name_id(target_schema.name, target_schema.id)}.json"
    )
    updated_target_schema = await read_json(target_schema_path)
    updated_target_schema["metadata"] = {"key": "value"}
    await write_json(target_schema_path, updated_target_schema)

    await upload_project(destination=settings.TARGET_DIRNAME, client=client)

    redownloaded_source_schema = await client.retrieve_schema(source_schema.id)
    redownloaded_target_schema = await read_json(target_schema_path)

    assert is_object_equal(redownloaded_target_schema, updated_target_schema)
    assert dataclasses.asdict(redownloaded_source_schema)["metadata"] == {}
