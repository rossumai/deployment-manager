# Take a JSON object / path and apply the release file to it
# Check the changes to be deployed or mock the API request and check after that
from copy import deepcopy
import datetime
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
from tests.conftest import TEST_DATA_PATH, tmp_path

TEST_DEPLOY_FILE_BASE_PATH = Path("tests/deploy/run/deploy_files")


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
        tmp_path
        / TEST_DIR_NAME
        / TEST_SUBDIR_NAME
        / "workspaces"
        / "some_ws_[1]"
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


@pytest_asyncio.fixture(scope="function")
async def ws_and_queue_project_path(tmp_path):
    ws_data = await read_json(TEST_DATA_PATH / "workspace.json")
    queue_data = await read_json(TEST_DATA_PATH / "queue" / "queue.json")

    ws_data["queues"] = [queue_data["url"]]
    queue_data["workspace"] = [ws_data["url"]]

    tmp_ws_path: Path = (
        tmp_path
        / TEST_DIR_NAME
        / TEST_SUBDIR_NAME
        / "workspaces"
        / templatize_name_id(ws_data["name"], ws_data["id"])
        / "workspace.json"
    )
    await write_json(tmp_ws_path, ws_data)

    tmp_queue_path = (
        tmp_ws_path.parent
        / "queues"
        / templatize_name_id(queue_data["name"], queue_data["id"])
    )
    await write_json(tmp_queue_path / "queue.json", queue_data)

    await write_json(
        tmp_queue_path / "schema.json",
        await read_json(TEST_DATA_PATH / "queue" / "schema.json"),
    )
    return Path(tmp_path)


@pytest.fixture()
def target_org_url():
    return "second_org"


@pytest.mark.asyncio
async def test_initialize_fails_with_incorrect_path(target_org_url: str):
    yaml = await load_deploy_yaml("basic_ws_deploy.yaml")
    deploy_file_ws_object = yaml.data[Settings.DEPLOY_KEY_WORKSPACES][0]
    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    mock_api_client = AsyncMock()

    await workspace_release.initialize(
        auto_delete=False,
        yaml=yaml,
        client=mock_api_client,
        source_client=None,
        source_dir_path=Path("./whatever/workspace.json"),
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        force_deploy=False,
        ignore_timestamp_mismatches={},
    )

    assert workspace_release.initialize_failed


@pytest.mark.asyncio
async def test_initialize_fails_with_incorrect_name(
    basic_ws_project_path: Path, target_org_url: str
):
    yaml = await load_deploy_yaml("basic_ws_deploy.yaml")
    deploy_file_ws_object = yaml.data[Settings.DEPLOY_KEY_WORKSPACES][0]
    deploy_file_ws_object["name"] = "some_other_name"
    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME

    await workspace_release.initialize(
        auto_delete=False,
        yaml=yaml,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        force_deploy=False,
        ignore_timestamp_mismatches={},
    )

    assert workspace_release.initialize_failed


@pytest.mark.asyncio
async def test_workspace_deploy_object_correct(
    basic_ws_project_path: Path, target_org_url: str
):
    yaml = await load_deploy_yaml("basic_ws_deploy.yaml")
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_ws_object = yaml.data[Settings.DEPLOY_KEY_WORKSPACES][0]

    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    await workspace_release.initialize(
        auto_delete=False,
        yaml=yaml,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        force_deploy=False,
        ignore_timestamp_mismatches={},
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
    target_org_url: str,
):
    yaml = await load_deploy_yaml("multi_target_ws_deploy.yaml")
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_ws_object = yaml.data[Settings.DEPLOY_KEY_WORKSPACES][0]

    workspace_release = WorkspaceRelease(**deploy_file_ws_object)
    await workspace_release.initialize(
        auto_delete=False,
        yaml=yaml,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        force_deploy=False,
        ignore_timestamp_mismatches={},
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
    target_org_url: str,
):
    yaml = await load_deploy_yaml("multi_target_update_ws_deploy.yaml")
    mock_api_client = AsyncMock()
    source_dir_path = basic_ws_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_ws_object = yaml.data[Settings.DEPLOY_KEY_WORKSPACES][0]

    workspace_release = WorkspaceRelease(**deploy_file_ws_object)

    # This is done because deploy() will update some of the values with mocks
    original_deploy_file_ws_object = deepcopy(deploy_file_ws_object)

    await workspace_release.initialize(
        auto_delete=False,
        yaml=yaml,
        client=mock_api_client,
        source_client=None,
        source_dir_path=source_dir_path,
        target_org_url=target_org_url,
        plan_only=False,
        is_same_org_deploy=False,
        last_deploy_timestamp=None,
        force_deploy=False,
        ignore_timestamp_mismatches={},
    )

    ws_object = deepcopy(workspace_release.data)

    expected_calls = [
        call(
            resource=Resource.Workspace,
            id_=original_deploy_file_ws_object["targets"][0]["id"],
            data={
                **ws_object,
                "organization": target_org_url,
                "queues": [],
                **original_deploy_file_ws_object["targets"][0]["attribute_override"],
            },
        ),
        call(
            resource=Resource.Workspace,
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
    # The path is dynamic (tmp_path) and cannot be in the yaml in advance
    deploy_file_queue_object[Settings.DEPLOY_KEY_BASE_PATH] = str(
        source_dir_path / "workspaces" / "some_ws_[1]"
    )

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
        force_deploy=False,
        unselected_hooks=[],
        ignore_timestamp_mismatches={},
        workspace_targets={},
        hook_targets={},
    )

    await queue_release.deploy()

    assert queue_release.schema_release.initialize_failed
    assert queue_release.deploy_failed


@pytest.mark.asyncio
async def test_ws_has_target_queues_and_queues_have_target_ws(
    ws_and_queue_project_path: Path, target_org_url: str
):
    yaml = await load_deploy_yaml("ws_and_queue_deploy.yaml")
    source_dir_path = ws_and_queue_project_path / TEST_DIR_NAME / TEST_SUBDIR_NAME
    deploy_file_ws_object = yaml.data[Settings.DEPLOY_KEY_WORKSPACES][0]
    deploy_file_queue_object = yaml.data[Settings.DEPLOY_KEY_QUEUES][0]
    deploy_file_schema_object = deploy_file_queue_object[Settings.DEPLOY_KEY_SCHEMA]
    # The path is dynamic (tmp_path) and cannot be in the yaml in advance
    deploy_file_queue_object[Settings.DEPLOY_KEY_BASE_PATH] = str(
        source_dir_path
        / "workspaces"
        / templatize_name_id(deploy_file_ws_object["name"], deploy_file_ws_object["id"])
    )

    # This is done because deploy() will update some of the values with mocks
    original_deploy_file_ws_object = deepcopy(deploy_file_ws_object)
    original_deploy_file_queue_object = deepcopy(deploy_file_queue_object)
    original_deploy_file_schema_object = deepcopy(deploy_file_schema_object)

    source_org = Organization(
        id="source_org_id",
        name="source_org",
        url="",
        workspaces=[],
        users=[],
        organization_group="",
        is_trial=False,
        created_at="",
    )
    target_org = Organization(
        id="target_org_id",
        name="target_org",
        url=target_org_url,
        workspaces=[],
        users=[],
        organization_group="",
        is_trial=False,
        created_at="",
    )

    release_file = ReleaseFile(
        **yaml.data,
        client=ElisAPIClient(token="a"),
        source_client=ElisAPIClient(token="b"),
        source_dir_path=source_dir_path,
        yaml=yaml,
        source_org=source_org,
        target_org=target_org,
    )
    mock_api_client = AsyncMock()
    release_file.client = mock_api_client

    ws_object = await read_json(
        source_dir_path
        / "workspaces"
        / templatize_name_id(deploy_file_ws_object["name"], deploy_file_ws_object["id"])
        / "workspace.json"
    )
    schema_object = await read_json(
        Path(deploy_file_queue_object[Settings.DEPLOY_KEY_BASE_PATH])
        / "queues"
        / templatize_name_id(
            deploy_file_queue_object["name"], deploy_file_queue_object["id"]
        )
        / "schema.json"
    )
    queue_object = await read_json(
        Path(deploy_file_queue_object[Settings.DEPLOY_KEY_BASE_PATH])
        / "queues"
        / templatize_name_id(
            deploy_file_queue_object["name"], deploy_file_queue_object["id"]
        )
        / "queue.json"
    )

    TARGET_WS_ID, TARGET_SCHEMA_ID, TARGET_QUEUE_ID = 111, 222, 333

    ws_mock_result = {
        "id": TARGET_WS_ID,
        "name": ws_object["name"],
        "url": ws_object["url"].replace(str(ws_object["id"]), str(TARGET_WS_ID)),
    }
    schema_mock_result = {
        "id": TARGET_SCHEMA_ID,
        "name": schema_object["name"],
        "url": schema_object["url"].replace(
            str(schema_object["id"]), str(TARGET_SCHEMA_ID)
        ),
    }
    queue_mock_result = {
        "id": TARGET_SCHEMA_ID,
        "name": queue_object["name"],
        "url": queue_object["url"].replace(
            str(queue_object["id"]), str(TARGET_QUEUE_ID)
        ),
    }
    # Gets return from "Elis API" and updates the targets
    # Important for queue.schema dependency replacement
    mock_api_client._http_client.create.side_effect = [
        ws_mock_result,
        schema_mock_result,
        queue_mock_result,
    ]
    await release_file.deploy_workspaces()

    await release_file.deploy_queues()

    ws_release = release_file.workspaces[0]
    queue_release = release_file.queues[0]

    expected_calls = [
        call(
            resource=Resource.Workspace,
            id_=TARGET_WS_ID,
            data={
                **ws_object,
                "organization": target_org_url,
                **ws_mock_result,
                "queues": [queue_mock_result["url"]],
            },
        ),
        call(
            resource=Resource.Schema,
            id_=TARGET_SCHEMA_ID,
            data={
                **schema_object,
                **schema_mock_result,
                "queues": [queue_mock_result["url"]],
            },
        ),
        call(
            Resource.Queue,
            id_=TARGET_QUEUE_ID,
            data={
                **queue_object,
                **queue_mock_result,
                "workspace": ws_mock_result["url"],
            },
        ),
    ]

    actual_calls = mock_api_client._http_client.update.call_args_list
    for actual, expected in zip(actual_calls, expected_calls):
        assert actual == expected

    # await workspace_release.initialize(
    #     auto_delete=False,
    #     yaml=yaml,
    #     client=mock_api_client,
    #     source_client=None,
    #     source_dir_path=source_dir_path,
    #     target_org_url=target_org_url,
    #     plan_only=False,
    #     is_same_org_deploy=False,
    #     last_deploy_timestamp=None,
    #     ignore_timestamp_mismatch=True,
    # )

    # await queue_release.initialize(
    #     auto_delete=False,
    #     yaml=yaml,
    #     client=AsyncMock(),
    #     source_client=None,
    #     source_dir_path=source_dir_path,
    #     plan_only=False,
    #     is_same_org_deploy=False,
    #     last_deploy_timestamp=None,
    #     ignore_timestamp_mismatch=True,
    #     schema_ignore_timestamp_mismatch=True,
    #     inbox_ignore_timestamp_mismatch=True,
    #     workspace_targets={},
    #     hook_targets={},
    # )

    # await queue_release.deploy()


# Test attribute override with pipes

# Test no timestamp on object works
