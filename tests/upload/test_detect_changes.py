import os
from unittest.mock import AsyncMock

import pytest
from anyio import Path

from deployment_manager.commands.download.saver import WorkspaceSaver
from deployment_manager.commands.download.subdirectory import (
    Subdirectory,
    create_subdir_configuration,
)
from deployment_manager.commands.upload.directory import (
    ChangedObject,
    UploadOrganizationDirectory,
)
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import GIT_CHARACTERS
from deployment_manager.utils.functions import templatize_name_id
from tests.upload.utils import initialize_git_repo


@pytest.fixture
def test_workspace_path(workspace_json: dict, tmp_path: Path, test_subdir: Subdirectory):
    workspace_saver = WorkspaceSaver(
        base_path=tmp_path,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir],
    )
    object_path = workspace_saver.construct_object_path(subdir=test_subdir, object=workspace_json)
    assert object_path == (
        tmp_path
        / test_subdir.name
        / "workspaces"
        / templatize_name_id(workspace_json["name"], workspace_json["id"])
        / "workspace.json"
    )


@pytest.mark.asyncio
async def test_detect_subdir(workspace_json: dict, tmp_path: Path, test_subdir: Subdirectory):
    TEST_ORG_NAME = "test-org"

    workspace_saver = WorkspaceSaver(
        base_path=tmp_path / TEST_ORG_NAME,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[test_subdir],
    )
    await workspace_saver.save_downloaded_objects()
    object_path = workspace_saver.construct_object_path(subdir=test_subdir, object=workspace_json)
    initialize_git_repo(tmp_path)

    workspace_json["name"] = "Testing change"
    await write_object_to_json(object_path, workspace_json)

    upload_dir = UploadOrganizationDirectory(
        name=TEST_ORG_NAME,
        project_path=tmp_path,
        upload_all=False,
        force=False,
        indexed_only=False,
        subdirectories={test_subdir.name: {"include": True, "object_ids": [workspace_json["id"]]}},
        org_id=-1,
        api_base="https://example.com",
    )

    # Needs to be done so that the git status command works properly
    prev_cwd = os.getcwd()  # Save the current working directory
    os.chdir(tmp_path)  # Change working directory
    await upload_dir.prepare_changed_objects()
    os.chdir(prev_cwd)

    assert upload_dir.changed_objects == [
        ChangedObject(
            operation=GIT_CHARACTERS.UPDATED,
            path=object_path.relative_to(tmp_path),  # The paths from git status are not absolute
            data=workspace_json,
        )
    ]


@pytest.mark.asyncio
async def test_detect_ignores_unincluded_subdir(
    workspace_json, tmp_path, test_subdir: Subdirectory, prod_subdir: Subdirectory
):
    TEST_ORG_NAME = "test-org"

    workspace_saver = WorkspaceSaver(
        base_path=tmp_path / TEST_ORG_NAME,
        objects=[workspace_json],
        changed_files=[],
        download_all=False,
        subdirs=[prod_subdir],
    )
    await workspace_saver.save_downloaded_objects()
    object_path = workspace_saver.construct_object_path(subdir=test_subdir, object=workspace_json)
    initialize_git_repo(tmp_path)

    workspace_json["name"] = "Testing change"
    await write_object_to_json(object_path, workspace_json)

    upload_dir = UploadOrganizationDirectory.model_construct(
        name=TEST_ORG_NAME,
        client=AsyncMock(),
        project_path=tmp_path,
        upload_all=False,
        force=False,
        indexed_only=False,
        subdirectories=create_subdir_configuration(
            {
                test_subdir.name: {"include": True, "object_ids": []},
                prod_subdir.name: {
                    "include": False,
                    "object_ids": [workspace_json["id"]],
                },
            }
        ),
        org_id=-1,
        api_base="https://example.com",
    )

    # Needs to be done so that the git status command works properly
    prev_cwd = os.getcwd()  # Save the current working directory
    os.chdir(tmp_path)  # Change working directory
    await upload_dir.prepare_changed_objects()
    os.chdir(prev_cwd)

    assert upload_dir.changed_objects == []
