import io
import pytest
import pytest_asyncio

from rossum_api import ElisAPIClient
from rossum_api.api_client import Resource

from project_rossum_deploy.commands.download.download import download_organization
from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import read_json, templatize_name_id
from tests.utils.compare import ensure_downloaded_object, compare_projects
from tests.utils.consts import REFERENCE_PROJECT_PATH, UPDATED_NAME


@pytest.mark.asyncio
async def test_fresh_download(client: ElisAPIClient, tmp_path):
    await download_organization(client=client, org_path=tmp_path)

    await compare_projects(tmp_path, REFERENCE_PROJECT_PATH)


@pytest.mark.asyncio
async def test_second_download_idempotency(
    client: ElisAPIClient, monkeypatch, tmp_path
):
    await download_organization(client=client, org_path=tmp_path)

    # Confirm configuration overwriting
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    await download_organization(client=client, org_path=tmp_path)

    await compare_projects(tmp_path, REFERENCE_PROJECT_PATH)


@pytest_asyncio.fixture(scope="function")
async def new_workspace(client: ElisAPIClient):
    workspace = await client.create_new_workspace(
        {
            "name": "temp_ws",
            "organization": (await client.retrieve_own_organization()).url,
        }
    )

    yield workspace

    await client.delete_workspace(workspace.id)


@pytest.mark.asyncio
async def test_rossum_created_file_downloaded(
    client: ElisAPIClient, tmp_path, new_workspace
):
    await download_organization(client=client, org_path=tmp_path)

    with pytest.raises(AssertionError):
        await compare_projects(tmp_path, REFERENCE_PROJECT_PATH)

    new_ws_path = (
        tmp_path
        / settings.SOURCE_DIRNAME
        / "workspaces"
        / templatize_name_id(new_workspace.name, new_workspace.id)
        / "workspace.json"
    )
    await ensure_downloaded_object(
        tmp_path=tmp_path,
        expected_path=new_ws_path,
        object_type="workspaces",
        reference=new_workspace,
    )


@pytest.mark.asyncio
async def test_rossum_deleted_file_absent(client: ElisAPIClient, monkeypatch, tmp_path):
    deleted_ws = await client.create_new_workspace(
        {
            "name": "temp_ws",
            "organization": (await client.retrieve_own_organization()).url,
        }
    )
    # Make sure the project was downloaded WITH the workspace
    await download_organization(client=client, org_path=tmp_path)
    await client.delete_workspace(deleted_ws.id)

    # Confirm configuration overwriting
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    await download_organization(client=client, org_path=tmp_path)

    await compare_projects(tmp_path, REFERENCE_PROJECT_PATH)


@pytest_asyncio.fixture(scope="function")
async def old_schema(client: ElisAPIClient):
    mapping = await read_mapping(REFERENCE_PROJECT_PATH / settings.MAPPING_FILENAME)
    old_schema = mapping["organization"]["schemas"][0]
    await client._http_client.update(
        resource=Resource.Schema, id_=old_schema["id"], data={"name": UPDATED_NAME}
    )

    yield old_schema

    await client._http_client.update(
        resource=Resource.Schema,
        id_=old_schema["id"],
        data={"name": old_schema["name"]},
    )


@pytest.mark.asyncio
async def test_rossum_updated_file_downloaded(
    client: ElisAPIClient, tmp_path, old_schema
):
    await download_organization(client=client, org_path=tmp_path)

    with pytest.raises(AssertionError):
        await compare_projects(tmp_path, REFERENCE_PROJECT_PATH)

    updated_schema_path = (
        tmp_path
        / settings.SOURCE_DIRNAME
        / "schemas"
        / f"{templatize_name_id(UPDATED_NAME, old_schema['id'])}.json"
    )
    assert await updated_schema_path.exists()
    assert UPDATED_NAME == (await read_json(updated_schema_path))["name"]

    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)

    found = False
    for schema_mapping in mapping["organization"]["schemas"]:
        if old_schema["name"] == schema_mapping["name"]:
            break
        elif (
            old_schema["id"] == schema_mapping["id"]
            and UPDATED_NAME == schema_mapping["name"]
        ):
            found = True
            break

    assert found


@pytest_asyncio.fixture(scope="function")
async def fixture_tuple(tmp_path, client: ElisAPIClient):
    await download_organization(client=client, org_path=tmp_path)
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)

    mapping["organization"]["target"] = mapping["organization"]["id"]
    await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)

    schema = await client.create_new_schema({"name": "source schema", "content": []})

    yield tmp_path, schema

    await client.delete_schema(schema.id)


@pytest.mark.asyncio
async def test_rossum_created_file_put_into_source(
    client: ElisAPIClient, fixture_tuple, monkeypatch
):
    tmp_path, new_schema = fixture_tuple

    # Confirm the new object should be in source
    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    await download_organization(client=client, org_path=tmp_path)

    new_schema_path = (
        tmp_path
        / settings.SOURCE_DIRNAME
        / "schemas"
        / f"{templatize_name_id(new_schema.name, new_schema.id)}.json"
    )
    await ensure_downloaded_object(
        tmp_path=tmp_path,
        expected_path=new_schema_path,
        object_type="schemas",
        reference=new_schema,
    )


@pytest.mark.asyncio
async def test_rossum_created_file_put_into_target(
    client: ElisAPIClient, fixture_tuple, monkeypatch
):
    tmp_path, new_schema = fixture_tuple

    # Pretend the schema is a target
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    mapping["organization"]["schemas"][0]["target"] = new_schema.id
    await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)

    monkeypatch.setattr("sys.stdin", io.StringIO("y"))
    await download_organization(client=client, org_path=tmp_path)

    new_schema_path = (
        tmp_path
        / settings.TARGET_DIRNAME
        / "schemas"
        / f"{templatize_name_id(new_schema.name, new_schema.id)}.json"
    )
    await ensure_downloaded_object(
        tmp_path=tmp_path,
        expected_path=new_schema_path,
        object_type="schemas",
        reference=new_schema,
    )
