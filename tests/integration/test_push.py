"""End-to-end push flow against an in-memory virtual Rossum org.

Flow:
  1. Build a virtual org and pull it locally (same as pull integration tests)
  2. Modify local JSON files
  3. Simulate git status so PRD sees them as changed
  4. Run the upload flow with a pre-injected virtual client
  5. Verify the virtual org received the updates
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.download.directory import DownloadOrganizationDirectory
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.commands.upload.directory import UploadOrganizationDirectory
from deployment_manager.commands.upload.upload import upload_destinations
from deployment_manager.utils.consts import GIT_CHARACTERS, settings
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org

SOURCE_DIR_NAME = "source"
SUBDIR_NAME = "primary"


async def _prepare_project(tmp_path: Path, org) -> None:
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


async def _inject_download_client(directory, client):
    if not directory.project_path:
        directory.project_path = Path(".")
    directory.client = client
    directory.changed_files = []


async def _inject_upload_client(directory, client):
    if not directory.project_path:
        directory.project_path = Path(".")
    directory.client = client


def _patch_git_empty(monkeypatch):
    def fake_run(*args, **kwargs):
        return MagicMock(stdout="", returncode=0)

    monkeypatch.setattr("deployment_manager.common.git.subprocess.run", fake_run)


def _patch_git_with_changes(monkeypatch, changed_files: list[str]):
    """Mock the `git status` call to report the given files as modified."""
    lines = "\n".join(f" M {path}" for path in changed_files) + "\n"

    call_count = [0]

    def fake_run(*args, **kwargs):
        m = MagicMock(returncode=0)
        call_count[0] += 1
        # First and third run() calls are `git config core.quotePath`; second is `git status`
        m.stdout = lines if call_count[0] == 2 else ""
        return m

    monkeypatch.setattr("deployment_manager.common.git.subprocess.run", fake_run)


async def _pull_initial(tmp_path: Path, client):
    """Seed the local project with a pulled copy of the virtual org."""
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
        await download_destinations(
            destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
            project_path=Path("."),
        )


@pytest.mark.asyncio
async def test_push_updates_workspace(tmp_path: Path, monkeypatch):
    """Edit workspace.json locally, push it, verify remote got updated payload."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)
    await _pull_initial(tmp_path, client)

    # Edit workspace.json
    ws_path = tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME / "workspaces" / "WS1_[500001]" / "workspace.json"
    ws_data = json.loads(await ws_path.read_text())
    ws_data["name"] = "WS1 Renamed"
    await ws_path.write_text(json.dumps(ws_data, indent=2))

    rel_path = "source/primary/workspaces/WS1_[500001]/workspace.json"
    _patch_git_with_changes(monkeypatch, [rel_path])

    # Patch download_destinations inside upload (called after push) to avoid loop
    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
                    project_path=Path("."),
                )

    # Virtual org should now have the new name
    ws_in_org = org._stores["workspaces"][500001]
    assert ws_in_org["name"] == "WS1 Renamed"


@pytest.mark.asyncio
async def test_push_rejects_stale_timestamp(tmp_path: Path, monkeypatch):
    """If the remote modified_at differs from local (stale), push must refuse."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    client = VirtualRossumClient(org)
    await _pull_initial(tmp_path, client)

    # Simulate someone else editing remote by updating modified_at on remote
    org._stores["workspaces"][500001]["modified_at"] = "2030-01-01T00:00:00.000000Z"

    # Edit locally
    ws_path = tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME / "workspaces" / "WS1_[500001]" / "workspace.json"
    ws_data = json.loads(await ws_path.read_text())
    ws_data["name"] = "WS1 Local Edit"
    await ws_path.write_text(json.dumps(ws_data, indent=2))

    _patch_git_with_changes(monkeypatch, ["source/primary/workspaces/WS1_[500001]/workspace.json"])

    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
                    project_path=Path("."),
                )

    # Remote should NOT have the local edit
    assert org._stores["workspaces"][500001]["name"] == "WS1"


@pytest.mark.asyncio
async def test_push_force_overwrites_stale_timestamp(tmp_path: Path, monkeypatch):
    """`--force` should bypass the timestamp check."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    client = VirtualRossumClient(org)
    await _pull_initial(tmp_path, client)

    org._stores["workspaces"][500001]["modified_at"] = "2030-01-01T00:00:00.000000Z"

    ws_path = tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME / "workspaces" / "WS1_[500001]" / "workspace.json"
    ws_data = json.loads(await ws_path.read_text())
    ws_data["name"] = "WS1 Forced"
    await ws_path.write_text(json.dumps(ws_data, indent=2))

    _patch_git_with_changes(monkeypatch, ["source/primary/workspaces/WS1_[500001]/workspace.json"])

    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
                    project_path=Path("."),
                    force=True,
                )

    assert org._stores["workspaces"][500001]["name"] == "WS1 Forced"


@pytest.mark.asyncio
async def test_push_hook_py_edit_updates_json_code(tmp_path: Path, monkeypatch):
    """Editing the .py file for a hook should update the JSON's config.code, then push it."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    client = VirtualRossumClient(org)
    await _pull_initial(tmp_path, client)

    # Edit the hook's .py file
    hook_py_path = tmp_path / SOURCE_DIR_NAME / SUBDIR_NAME / "hooks" / "MyHook_[500003].py"
    new_code = "def rossum_hook_request_handler(payload):\n    return {'updated': True}\n"
    await hook_py_path.write_text(new_code)

    # Simulate git status reporting the .py as modified
    _patch_git_with_changes(monkeypatch, ["source/primary/hooks/MyHook_[500003].py"])

    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
                    project_path=Path("."),
                )

    # Remote hook's code should now contain 'updated'
    remote_hook = org._stores["hooks"][500003]
    assert "'updated': True" in remote_hook["config"]["code"]


@pytest.mark.asyncio
async def test_push_no_changes_does_not_call_api(tmp_path: Path, monkeypatch):
    """If git status reports no changes, no push requests should happen."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    client = VirtualRossumClient(org)
    await _pull_initial(tmp_path, client)

    # Capture any update/create calls on the mock API
    originals_workspaces = dict(org._stores["workspaces"])

    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE_DIR_NAME) / SUBDIR_NAME,),
                    project_path=Path("."),
                )

    # Store unchanged (modulo modified_at refresh, which shouldn't happen at all here)
    assert org._stores["workspaces"] == originals_workspaces


@pytest.mark.asyncio
async def test_git_characters_covered():
    """Sanity: ensure the op-code we use in tests is the "updated" code."""
    assert GIT_CHARACTERS.UPDATED == "M"
