# Take a JSON object / path and apply the release file to it
# Check the changes to be deployed or mock the API request and check after that
from copy import deepcopy
import os
from anyio import Path
from pydantic import ValidationError
import pytest
from unittest.mock import AsyncMock, call
from rossum_api import ElisAPIClient
from rossum_api.models.organization import Organization
from rossum_api.api_client import Resource

import pytest_asyncio

from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.run.release_file import ReleaseFile
from deployment_manager.commands.deploy.subcommands.run.workspace_release import (
    WorkspaceRelease,
)
from deployment_manager.common.read_write import read_json, write_json
from deployment_manager.utils.consts import Settings
from deployment_manager.utils.functions import templatize_name_id
from tests.conftest import TEST_DATA_PATH

TEST_DEPLOY_FILE_BASE_PATH = Path("tests/deploy/run/deploy_files")


@pytest_asyncio.fixture
async def basic_ws_deploy_file():
    release_file = await (
        TEST_DEPLOY_FILE_BASE_PATH / "basic_ws_deploy.yaml"
    ).read_text()
    return DeployYaml(release_file)


@pytest_asyncio.fixture
async def multi_target_ws_deploy_file():
    release_file = await (
        TEST_DEPLOY_FILE_BASE_PATH / "multi_target_ws_deploy.yaml"
    ).read_text()
    return DeployYaml(release_file)


@pytest_asyncio.fixture
async def multi_target_update_ws_deploy_file():
    release_file = await (
        TEST_DEPLOY_FILE_BASE_PATH / "multi_target_update_ws_deploy.yaml"
    ).read_text()
    return DeployYaml(release_file)


async def load_deploy_yaml(deploy_file_name: str):
    release_file = await (TEST_DEPLOY_FILE_BASE_PATH / deploy_file_name).read_text()
    return DeployYaml(release_file)


TEST_DIR_NAME = "test-org"
TEST_SUBDIR_NAME = "test"


@pytest_asyncio.fixture(scope="function")
async def basic_ws_project_path(tmp_path):
    data = await read_json(TEST_DATA_PATH / "workspace.json")
    tmp_ws_path = (
        tmp_path
        / TEST_DIR_NAME
        / TEST_SUBDIR_NAME
        / "workspaces"
        / templatize_name_id(data["name"], data["id"])
        / "workspace.json"
    )
    await write_json(tmp_ws_path, data)
    return Path(tmp_path)


@pytest_asyncio.fixture(scope="function")
async def basic_queue_project_path(tmp_path):
    queue_data = await read_json(TEST_DATA_PATH / "queue" / "queue.json")
    tmp_queue_path = (
        Path("test-org/test/workspaces/some_ws_[1]")
        / "queues"
        / templatize_name_id(queue_data["name"], queue_data["id"])
    )

    await write_json(tmp_queue_path / "queue.json", queue_data)
    await write_json(
        tmp_queue_path / "inbox.json",
        await read_json(TEST_DATA_PATH / "queue" / "inbox.json"),
    )
    await write_json(
        tmp_queue_path / "schema.json",
        await read_json(TEST_DATA_PATH / "queue" / "schema.json"),
    )
    return Path(tmp_path)


@pytest.fixture()
def target_org_url():
    return "second_org"


@pytest.mark.asyncio
async def test_initialize_fails_with_incorrect_path(
    basic_ws_deploy_file: DeployYaml, target_org_url: str
):
    deploy_file_ws_object = basic_ws_deploy_file.data[Settings.DEPLOY_KEY_WORKSPACES][0]
    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    mock_api_client = AsyncMock()

    await workspace_release.initialize(
        auto_delete=False,
        yaml=basic_ws_deploy_file,
        client=mock_api_client,
        source_client=None,
        source_dir_path=Path("./whatever/workspace.json"),
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        ignore_timestamp_mismatch=True,
    )

    assert workspace_release.initialize_failed


@pytest.mark.asyncio
async def test_initialize_fails_with_incorrect_name(
    basic_ws_project_path: Path, basic_ws_deploy_file: DeployYaml, target_org_url: str
):
    deploy_file_ws_object = basic_ws_deploy_file.data[Settings.DEPLOY_KEY_WORKSPACES][0]
    deploy_file_ws_object["name"] = "some_other_name"
    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME

    await workspace_release.initialize(
        auto_delete=False,
        yaml=basic_ws_deploy_file,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        ignore_timestamp_mismatch=True,
    )

    assert workspace_release.initialize_failed


@pytest.mark.asyncio
async def test_workspace_deploy_object_correct(
    basic_ws_project_path: Path, basic_ws_deploy_file: DeployYaml, target_org_url: str
):
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_ws_object = basic_ws_deploy_file.data[Settings.DEPLOY_KEY_WORKSPACES][0]

    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    await workspace_release.initialize(
        auto_delete=False,
        yaml=basic_ws_deploy_file,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        ignore_timestamp_mismatch=True,
    )

    ws_object = deepcopy(workspace_release.data)

    await workspace_release.deploy()

    expected_payload = {
        **ws_object,
        "organization": target_org_url,
        "queues": [],
        **deploy_file_ws_object["targets"][0]["attribute_override"],
    }

    mock_api_client._http_client.create.assert_called_once_with(
        Resource.Workspace, expected_payload
    )


@pytest.mark.asyncio
async def test_workspace_deploy_twice_for_two_targets(
    basic_ws_project_path: Path,
    multi_target_ws_deploy_file: DeployYaml,
    target_org_url: str,
):
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_ws_object = multi_target_ws_deploy_file.data[
        Settings.DEPLOY_KEY_WORKSPACES
    ][0]

    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    await workspace_release.initialize(
        auto_delete=False,
        yaml=multi_target_ws_deploy_file,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        ignore_timestamp_mismatch=True,
    )

    ws_object = deepcopy(workspace_release.data)

    await workspace_release.deploy()

    expected_calls = [
        call(
            Resource.Workspace,
            {
                **ws_object,
                "organization": target_org_url,
                "queues": [],
                **deploy_file_ws_object["targets"][0]["attribute_override"],
            },
        ),
        call(
            Resource.Workspace,
            {
                **ws_object,
                "organization": target_org_url,
                "queues": [],
                **deploy_file_ws_object["targets"][1]["attribute_override"],
            },
        ),
    ]

    actual_calls = mock_api_client._http_client.create.call_args_list
    for actual, expected in zip(actual_calls, expected_calls):
        assert actual == expected


@pytest.mark.asyncio
async def test_workspace_deploy_updates_correct_targets(
    basic_ws_project_path: Path,
    multi_target_update_ws_deploy_file: DeployYaml,
    target_org_url: str,
):
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_ws_object = multi_target_update_ws_deploy_file.data[
        Settings.DEPLOY_KEY_WORKSPACES
    ][0]

    workspace_release = WorkspaceRelease(**deploy_file_ws_object)

    # This is done because deploy() will update some of the values with mocks
    original_deploy_file_ws_object = deepcopy(deploy_file_ws_object)

    await workspace_release.initialize(
        auto_delete=False,
        yaml=multi_target_update_ws_deploy_file,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        ignore_timestamp_mismatch=True,
    )

    ws_object = deepcopy(workspace_release.data)

    expected_calls = [
        call(
            Resource.Workspace,
            id_=original_deploy_file_ws_object["targets"][0]["id"],
            data={
                **ws_object,
                "organization": target_org_url,
                "queues": [],
                **original_deploy_file_ws_object["targets"][0]["attribute_override"],
            },
        ),
        call(
            Resource.Workspace,
            id_=original_deploy_file_ws_object["targets"][1]["id"],
            data={
                **ws_object,
                "organization": target_org_url,
                "queues": [],
                **original_deploy_file_ws_object["targets"][1]["attribute_override"],
            },
        ),
    ]

    await workspace_release.deploy()

    actual_calls = mock_api_client._http_client.update.call_args_list
    for actual, expected in zip(actual_calls, expected_calls):
        assert actual == expected


@pytest.mark.asyncio
async def test_no_inbox_ok(
    basic_queue_project_path: Path,
):
    yaml = await load_deploy_yaml("no_inbox_deploy.yaml")
    mock_api_client = AsyncMock()
    source_dir_path = basic_queue_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_queue_object = yaml.data[Settings.DEPLOY_KEY_QUEUES][0]

    # This is done because deploy() will update some of the values with mocks
    original_deploy_file_queue_object = deepcopy(deploy_file_queue_object)

    release_file = ReleaseFile(
        **yaml.data,
        client=ElisAPIClient(token="a"),
        source_client=ElisAPIClient(token="b"),
        source_dir_path=source_dir_path,
        yaml=yaml,
        source_org=Organization.__new__(Organization),
        target_org=Organization.__new__(Organization),
    )

    release_file.client = mock_api_client
    queue_release = release_file.queues[0]

    await queue_release.initialize(
        auto_delete=False,
        yaml=yaml,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        ignore_timestamp_mismatch=True,
        schema_ignore_timestamp_mismatch=True,
        inbox_ignore_timestamp_mismatch=True,
        workspace_targets={},
        hook_targets={},
    )

    # Gets return from "Elis API" and updates the targets
    # Important for queue.schema dependency replacement
    mock_api_client._http_client.update.return_value = [
        {"id": original_deploy_file_queue_object["schema"]["targets"][0]["id"]},
        {"id": original_deploy_file_queue_object["targets"][0]["id"]},
    ]

    await queue_release.deploy()

    queue_object = deepcopy(queue_release.data)
    schema_object = deepcopy(queue_release.schema_release.data)

    expected_calls = [
        call(
            Resource.Schema,
            id_=original_deploy_file_queue_object["schema"]["targets"][0]["id"],
            data={**schema_object, "queues": []},
        ),
        call(
            Resource.Queue,
            id_=original_deploy_file_queue_object["targets"][0]["id"],
            data={
                **queue_object,
                "organization": target_org_url,
            },
        ),
    ]

    actual_calls = mock_api_client._http_client.update.call_args_list
    for actual, expected in zip(actual_calls, expected_calls):
        assert actual == expected


@pytest.mark.asyncio
async def test_no_schema_not_ok(
    basic_queue_project_path: Path,
):
    yaml = await load_deploy_yaml("no_schema_deploy.yaml")
    source_dir_path = basic_queue_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME

    with pytest.raises(ValidationError):
        ReleaseFile(
            **yaml.data,
            client=ElisAPIClient(token="a"),
            source_client=ElisAPIClient(token="b"),
            source_dir_path=source_dir_path,
            yaml=yaml,
            source_org=Organization.__new__(Organization),
            target_org=Organization.__new__(Organization),
        )


@pytest.mark.asyncio
async def test_no_schema_path_not_ok(
    basic_queue_project_path: Path,
):
    yaml = await load_deploy_yaml("no_inbox_deploy.yaml")
    source_dir_path = basic_queue_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_queue_object = yaml.data[Settings.DEPLOY_KEY_QUEUES][0]

    schema_path = (
        Path(deploy_file_queue_object[Settings.DEPLOY_KEY_BASE_PATH])
        / "queues"
        / templatize_name_id(
            deploy_file_queue_object["name"], deploy_file_queue_object["id"]
        )
        / "schema.json"
    )
    os.remove(schema_path)

    release_file = ReleaseFile(
        **yaml.data,
        client=ElisAPIClient(token="a"),
        source_client=ElisAPIClient(token="b"),
        source_dir_path=source_dir_path,
        yaml=yaml,
        source_org=Organization.__new__(Organization),
        target_org=Organization.__new__(Organization),
    )

    queue_release = release_file.queues[0]

    await queue_release.initialize(
        auto_delete=False,
        yaml=yaml,
        client=AsyncMock(),
        source_client=None,
        source_dir_path=source_dir_path,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        ignore_timestamp_mismatch=True,
        schema_ignore_timestamp_mismatch=True,
        inbox_ignore_timestamp_mismatch=True,
        workspace_targets={},
        hook_targets={},
    )

    await queue_release.deploy()

    assert queue_release.schema_release.initialize_failed
    assert queue_release.deploy_failed


# Test that ws gets its queues overwritten

# Test attribute override with pipes
