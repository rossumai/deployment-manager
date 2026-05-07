import json
import os
import pathlib
import subprocess
from unittest.mock import AsyncMock

import pytest
from anyio import Path
from rossum_api.domain_logic.resources import Resource

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
from tests.unit.upload.utils import initialize_git_repo


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


def test_build_deleted_skips_non_versioned_attributes_file():
    """non_versioned_object_attributes.json is silently skipped."""
    upload_dir = UploadOrganizationDirectory.model_construct(
        name="test-org",
        project_path=Path("/tmp"),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
    )
    result = upload_dir._build_deleted_changed_object(
        GIT_CHARACTERS.DELETED,
        Path("test-org/non_versioned_object_attributes.json"),
    )
    assert result is None


def test_build_deleted_skips_email_template_dir():
    """email_templates/*.json is silently skipped via the dir allow-list."""
    upload_dir = UploadOrganizationDirectory.model_construct(
        name="test-org",
        project_path=Path("/tmp"),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
    )
    result = upload_dir._build_deleted_changed_object(
        GIT_CHARACTERS.DELETED,
        Path("test-org/email_templates/welcome.json"),
    )
    assert result is None


def test_build_deleted_skips_formula_file():
    """Formula `.py` files under formulas/ are silently skipped."""
    upload_dir = UploadOrganizationDirectory.model_construct(
        name="test-org",
        project_path=Path("/tmp"),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
    )
    result = upload_dir._build_deleted_changed_object(
        GIT_CHARACTERS.DELETED,
        Path("test-org/workspaces/W_[1]/queues/Q_[2]/formulas/some_field.py"),
    )
    assert result is None


def test_build_deleted_skips_labels_dir():
    """labels/*.json is silently skipped via the dir allow-list."""
    upload_dir = UploadOrganizationDirectory.model_construct(
        name="test-org",
        project_path=Path("/tmp"),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
    )
    result = upload_dir._build_deleted_changed_object(
        GIT_CHARACTERS.DELETED,
        Path("test-org/labels/important.json"),
    )
    assert result is None


def _git_init_and_commit(tmp_path):
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "t"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )


def test_build_deleted_schema_recovers_id_from_git(tmp_path):
    """A deleted schema.json's id is recovered from git history so the
    DELETE op survives into the plan (previously dropped → orphaned schema)."""
    sync_root = pathlib.Path(str(tmp_path))
    org_name = "test-org"
    queue_dir = sync_root / org_name / "workspaces" / "W_[1]" / "queues" / "Q_[2]"
    queue_dir.mkdir(parents=True)
    schema_path = queue_dir / "schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "id": 555,
                "url": "https://x/api/v1/schemas/555",
                "name": "S",
                "content": [],
            }
        )
    )

    _git_init_and_commit(sync_root)
    schema_path.unlink()

    upload_dir = UploadOrganizationDirectory.model_construct(
        name=org_name,
        project_path=Path(tmp_path),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
    )

    rel_path = (
        Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[2]" / "schema.json"
    )

    prev_cwd = os.getcwd()
    os.chdir(str(sync_root))
    try:
        result = upload_dir._build_deleted_changed_object(GIT_CHARACTERS.DELETED, rel_path)
    finally:
        os.chdir(prev_cwd)

    assert result is not None
    assert result.data["id"] == 555
    assert result.data["url"] == "https://x/api/v1/schemas/555"
    assert result.resolved_type == Resource.Schema


def test_build_deleted_inbox_recovers_id_from_git(tmp_path):
    """Same as above, for inbox.json."""
    sync_root = pathlib.Path(str(tmp_path))
    org_name = "test-org"
    queue_dir = sync_root / org_name / "workspaces" / "W_[1]" / "queues" / "Q_[2]"
    queue_dir.mkdir(parents=True)
    inbox_path = queue_dir / "inbox.json"
    inbox_path.write_text(
        json.dumps(
            {
                "id": 777,
                "url": "https://x/api/v1/inboxes/777",
                "name": "I",
            }
        )
    )

    _git_init_and_commit(sync_root)
    inbox_path.unlink()

    upload_dir = UploadOrganizationDirectory.model_construct(
        name=org_name,
        project_path=Path(tmp_path),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
    )

    rel_path = (
        Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[2]" / "inbox.json"
    )

    prev_cwd = os.getcwd()
    os.chdir(str(sync_root))
    try:
        result = upload_dir._build_deleted_changed_object(GIT_CHARACTERS.DELETED, rel_path)
    finally:
        os.chdir(prev_cwd)

    assert result is not None
    assert result.data["id"] == 777
    assert result.resolved_type == Resource.Inbox


def test_build_deleted_schema_returns_none_when_git_recovery_fails(tmp_path):
    """Schema deleted but never in git: silently skip (return None)."""
    sync_root = pathlib.Path(str(tmp_path))
    org_name = "test-org"
    queue_dir = sync_root / org_name / "workspaces" / "W_[1]" / "queues" / "Q_[2]"
    queue_dir.mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=str(sync_root), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t"],
        cwd=str(sync_root),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "t"],
        cwd=str(sync_root),
        check=True,
        capture_output=True,
    )

    upload_dir = UploadOrganizationDirectory.model_construct(
        name=org_name,
        project_path=Path(tmp_path),
        subdirectories={},
        org_id=-1,
        api_base="https://example.com",
    )

    rel_path = (
        Path(org_name) / "workspaces" / "W_[1]" / "queues" / "Q_[2]" / "schema.json"
    )

    prev_cwd = os.getcwd()
    os.chdir(str(sync_root))
    try:
        result = upload_dir._build_deleted_changed_object(GIT_CHARACTERS.DELETED, rel_path)
    finally:
        os.chdir(prev_cwd)

    assert result is None
