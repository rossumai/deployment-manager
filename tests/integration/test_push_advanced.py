"""Advanced push scenarios: CREATE of new objects and --all re-upload."""

import json
from unittest.mock import MagicMock, patch

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.download.directory import DownloadOrganizationDirectory
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.commands.upload.directory import UploadOrganizationDirectory
from deployment_manager.commands.upload.upload import upload_destinations
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import settings
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org

SOURCE = "source"
SUB = "primary"


async def _prepare_project(tmp_path: Path, org):
    config = {
        "directories": {
            SOURCE: {
                "org_id": org.org_id,
                "api_base": org.base_url,
                "subdirectories": {SUB: {"regex": ""}},
            }
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))
    await (tmp_path / SOURCE / SUB).mkdir(parents=True, exist_ok=True)


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


def _patch_git_with_changes(monkeypatch, change_lines: list[str]):
    """`change_lines` already include the opcode prefix (e.g., ' M path', '?? path')."""
    output = "\n".join(change_lines) + "\n"

    call_count = [0]

    def fake_run(*args, **kwargs):
        m = MagicMock(returncode=0)
        call_count[0] += 1
        m.stdout = output if call_count[0] == 2 else ""
        return m

    monkeypatch.setattr("deployment_manager.common.git.subprocess.run", fake_run)


async def _pull_initial(client):
    with patch.object(
        DownloadOrganizationDirectory,
        "initialize",
        lambda self: _inject_download_client(self, client),
    ):
        await download_destinations(
            destinations=(Path(SOURCE) / SUB,),
            project_path=Path("."),
        )


@pytest.mark.asyncio
async def test_push_all_uploads_every_file(tmp_path: Path, monkeypatch):
    """`--all` extends the list of git-reported changes with every other file."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    client = VirtualRossumClient(org)
    await _pull_initial(client)

    # Freeze the hook's modified_at so we can verify it gets re-updated by the push
    org._stores["hooks"][500003]["modified_at"] = "2020-01-01T00:00:00.000000Z"

    # Simulate one trivially reported change so prepare_changed_objects doesn't bail early
    _patch_git_with_changes(
        monkeypatch,
        [f" M {SOURCE}/{SUB}/workspaces/WS1_[500001]/workspace.json"],
    )

    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE) / SUB,),
                    project_path=Path("."),
                    upload_all=True,
                    force=True,
                )

    # The hook (which wasn't in the git-reported change list) must have been touched
    # because --all includes unmodified files.
    assert org._stores["hooks"][500003]["modified_at"] != "2020-01-01T00:00:00.000000Z"


@pytest.mark.asyncio
async def test_push_creates_new_object_from_untracked_json(tmp_path: Path, monkeypatch):
    """An untracked local JSON (id/url that returns 404) → API create() is called."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    client = VirtualRossumClient(org)
    await _pull_initial(client)

    # User creates a NEW hook JSON pointing at a non-existent remote ID
    new_hook_path = tmp_path / SOURCE / SUB / "hooks" / "BrandNewHook_[999999].json"
    new_hook_data = {
        "id": 999999,
        "name": "BrandNewHook",
        "url": f"{org.base_url}/hooks/999999",
        "type": "function",
        "events": ["annotation_content.user_update"],
        "active": True,
        "queues": [],
        "run_after": [],
        "config": {
            "code": "def rossum_hook_request_handler(payload):\n    return {'created': True}\n",
            "runtime": "python3.8",
        },
        "extension_source": "custom",
        "secrets": {},
        "sideload": [],
        "token_owner": None,
        "guide": "",
        "metadata": {},
    }
    await write_object_to_json(new_hook_path, new_hook_data)

    # Git shows this as untracked
    _patch_git_with_changes(monkeypatch, [f"?? {SOURCE}/{SUB}/hooks/BrandNewHook_[999999].json"])

    hooks_before = set(org._stores["hooks"].keys())

    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE) / SUB,),
                    project_path=Path("."),
                )

    hooks_after = set(org._stores["hooks"].keys())
    new_ids = hooks_after - hooks_before
    assert len(new_ids) == 1
    new_hook = org._stores["hooks"][new_ids.pop()]
    assert new_hook["name"] == "BrandNewHook"
    assert "'created': True" in new_hook["config"]["code"]


@pytest.mark.asyncio
async def test_push_untracked_file_but_remote_exists_becomes_update(tmp_path: Path, monkeypatch):
    """If an untracked local file points at an existing remote object, op-code changes to UPDATE."""
    monkeypatch.chdir(tmp_path)
    _patch_git_empty(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    client = VirtualRossumClient(org)
    await _pull_initial(client)

    # Remove the pulled workspace file then re-create it without committing (git says untracked)
    ws_path = tmp_path / SOURCE / SUB / "workspaces" / "WS1_[500001]" / "workspace.json"
    ws_data = json.loads(await ws_path.read_text())
    ws_data["name"] = "Pushed From Untracked"
    await ws_path.write_text(json.dumps(ws_data, indent=2))

    _patch_git_with_changes(
        monkeypatch,
        [f"?? {SOURCE}/{SUB}/workspaces/WS1_[500001]/workspace.json"],
    )

    async def _noop_download(*args, **kwargs):
        return

    with patch.object(UploadOrganizationDirectory, "initialize", lambda self: _inject_upload_client(self, client)):
        with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_download_client(self, client)):
            with patch("deployment_manager.commands.upload.upload.download_destinations", _noop_download):
                await upload_destinations(
                    destinations=(Path(SOURCE) / SUB,),
                    project_path=Path("."),
                    force=True,  # skip timestamp check
                )

    # Workspace must have been UPDATED (not recreated as new) — same id, new name
    assert org._stores["workspaces"][500001]["name"] == "Pushed From Untracked"
    # No extra workspace created
    assert len([k for k in org._stores["workspaces"]]) == 1
