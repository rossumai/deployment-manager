"""End-to-end pull flow against an in-memory virtual Rossum org.

Flow:
  1. Build a virtual org with 1 workspace, 1 queue (with schema+inbox), 1 hook
  2. Configure PRD project directory layout + prd_config.yaml
  3. Run `download_destinations(...)` with a pre-injected virtual client
  4. Verify the on-disk layout matches PRD's conventions
"""

from unittest.mock import patch

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.download.directory import DownloadOrganizationDirectory
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.common.read_write import read_object_from_json
from deployment_manager.utils.consts import settings
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org

SOURCE_DIR_NAME = "source"
SUBDIR_NAME = "primary"


async def _prepare_project(tmp_path, org):
    """Write prd_config.yaml and create the org+subdir layout."""
    config = {
        "directories": {
            SOURCE_DIR_NAME: {
                "org_id": org.org_id,
                "api_base": org.base_url,
                "subdirectories": {SUBDIR_NAME: {"regex": ""}},
            }
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))
    await (tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME).mkdir(parents=True, exist_ok=True)


def _patch_git(monkeypatch):
    """Stub out git calls in download.py so they don't touch the real git."""
    from unittest.mock import MagicMock

    def fake_run(*args, **kwargs):
        return MagicMock(stdout="", returncode=0)

    monkeypatch.setattr("deployment_manager.common.git.subprocess.run", fake_run)


@pytest.mark.asyncio
async def test_pull_creates_organization_file(tmp_path: Path, monkeypatch):
    """organization.json must be written with the full org payload."""
    _patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)
    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
        await download_destinations(
            destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
            project_path=tmp_path,
        )

    org_path = tmp_path / SOURCE_DIR_NAME / "organization.json"
    assert await org_path.exists()
    org_data = await read_object_from_json(org_path)
    assert org_data["id"] == org.org_id
    assert org_data["name"] == "virtual-org"


async def _inject_client(directory, client):
    """Replacement for OrganizationDirectory.initialize() that skips credentials."""
    if not directory.project_path:
        directory.project_path = Path(".")
    directory.client = client
    # Populate changed_files similarly to the real one but without git
    directory.changed_files = []


@pytest.mark.asyncio
async def test_pull_creates_workspace_queue_hook_files(tmp_path: Path, monkeypatch):
    """Each remote object must be saved at the expected PRD-convention path."""
    _patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)
    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
        await download_destinations(
            destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
            project_path=tmp_path,
        )

    subdir_root = tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME

    # Workspace
    ws_path = subdir_root / "workspaces" / "WS1_[500001]" / "workspace.json"
    assert await ws_path.exists()
    ws_data = await read_object_from_json(ws_path)
    assert ws_data["id"] == 500001
    assert ws_data["name"] == "WS1"

    # Queue and its siblings
    q_dir = subdir_root / "workspaces" / "WS1_[500001]" / "queues" / "Q1_[500004]"
    q_path = q_dir / "queue.json"
    schema_path = q_dir / "schema.json"
    inbox_path = q_dir / "inbox.json"

    assert await q_path.exists()
    assert await schema_path.exists()
    assert await inbox_path.exists()

    queue_data = await read_object_from_json(q_path)
    assert queue_data["id"] == 500004
    assert queue_data["schema"].endswith("/schemas/500002")
    # NON_PULLED_KEYS_PER_OBJECT for Queue: counts and users removed
    assert "counts" not in queue_data
    assert "users" not in queue_data

    schema_data = await read_object_from_json(schema_path)
    assert schema_data["id"] == 500002
    assert schema_data["content"][0]["id"] == "basic_info"

    # Hook: flat JSON file + extracted .py companion
    hook_path = subdir_root / "hooks" / "MyHook_[500003].json"
    hook_code_path = subdir_root / "hooks" / "MyHook_[500003].py"
    assert await hook_path.exists()
    assert await hook_code_path.exists()

    hook_data = await read_object_from_json(hook_path)
    assert hook_data["id"] == 500003
    # Hook.status key is stripped on pull
    assert "status" not in hook_data

    hook_code = await hook_code_path.read_text()
    assert "rossum_hook_request_handler" in hook_code


@pytest.mark.asyncio
async def test_pull_non_versioned_modified_at_split(tmp_path: Path, monkeypatch):
    """modified_at is stripped from the main JSON and written to the sidecar file.

    The non-versioned attribute logic uses `path.parents[-3]`, which only resolves
    to the org/subdir root if paths are relative. Run with project_path="." and chdir.
    """
    _patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)
    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
        await download_destinations(
            destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
            project_path=Path("."),
        )

    # The raw file must not contain modified_at
    import json

    raw = json.loads(
        await (tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME / "workspaces" / "WS1_[500001]" / "workspace.json").read_text()
    )
    assert "modified_at" not in raw

    # The sidecar exists at dir/subdir level: source/primary/
    nv_file = tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME / settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME
    assert await nv_file.exists()


@pytest.mark.asyncio
async def test_pull_multi_subdir_regex_routing(tmp_path: Path, monkeypatch):
    """A workspace with [PROD] in the name should be routed to the 'prod' subdir."""
    _patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)
    org = build_simple_org()
    # Add a PROD-tagged workspace
    org.add_workspace(name="WS2 [PROD]", id_=500999)

    config = {
        "directories": {
            SOURCE_DIR_NAME: {
                "org_id": org.org_id,
                "api_base": org.base_url,
                "subdirectories": {
                    "dev": {"regex": ""},
                    "prod": {"regex": "PROD"},
                },
            }
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))
    await (tmp_path / SOURCE_DIR_NAME / "dev").mkdir(parents=True, exist_ok=True)
    await (tmp_path / SOURCE_DIR_NAME / "prod").mkdir(parents=True, exist_ok=True)

    client = VirtualRossumClient(org)
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
        # Destination the "prod" subdir only
        await download_destinations(
            destinations=(Path(SOURCE_DIR_NAME) / "prod",),
            project_path=tmp_path,
        )

    # Only WS2 (PROD-tagged) should land in the prod subdir
    prod_ws = tmp_path / SOURCE_DIR_NAME / "prod" / "workspaces" / "WS2 [PROD]_[500999]" / "workspace.json"
    dev_ws_1 = tmp_path / SOURCE_DIR_NAME / "dev" / "workspaces" / "WS1_[500001]" / "workspace.json"

    assert await prod_ws.exists()
    # dev subdir was not included for this pull, so WS1 is not written
    assert not await dev_ws_1.exists()


@pytest.mark.asyncio
async def test_pull_is_idempotent(tmp_path: Path, monkeypatch):
    """Running pull twice with no remote changes should not re-modify files."""
    _patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)
    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)

    async def do_pull():
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
            await download_destinations(
                destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
                project_path=tmp_path,
            )

    await do_pull()
    ws_path = tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME / "workspaces" / "WS1_[500001]" / "workspace.json"
    first_mtime = (await ws_path.stat()).st_mtime

    # Second pull — remote unchanged → should_write_object must return False
    await do_pull()
    second_mtime = (await ws_path.stat()).st_mtime
    assert second_mtime == first_mtime
