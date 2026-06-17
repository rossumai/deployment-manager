"""Advanced pull scenarios: stale object removal + formula field extraction."""

from unittest.mock import MagicMock, patch

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.download.directory import DownloadOrganizationDirectory
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.utils.consts import settings
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org


async def _inject_client(directory, client):
    if not directory.project_path:
        directory.project_path = Path(".")
    directory.client = client
    directory.changed_files = []


def _patch_git(monkeypatch):
    def fake_run(*args, **kwargs):
        return MagicMock(stdout="", returncode=0)

    monkeypatch.setattr("deployment_manager.common.git.subprocess.run", fake_run)


async def _prepare_project(tmp_path: Path, org):
    config = {
        "directories": {
            "source": {
                "org_id": org.org_id,
                "api_base": org.base_url,
                "subdirectories": {"primary": {"regex": ""}},
            }
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))
    await (tmp_path / "source" / "primary").mkdir(parents=True, exist_ok=True)


@pytest.mark.asyncio
async def test_pull_removes_stale_local_files(tmp_path: Path, monkeypatch):
    """When a remote object is deleted, the local JSON is removed on the next pull."""
    _patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)

    org = build_simple_org()
    # Add an extra hook that we'll later delete remotely
    stale_hook = org.add_hook(name="WillBeDeleted", id_=500500)

    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)

    # Initial pull: both hooks saved
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
        await download_destinations(
            destinations=(Path("source") / "primary",),
            project_path=Path("."),
        )

    stale_path = tmp_path / "source" / "primary" / "hooks" / "WillBeDeleted_[500500].json"
    kept_path = tmp_path / "source" / "primary" / "hooks" / "MyHook_[500003].json"
    assert await stale_path.exists()
    assert await kept_path.exists()

    # Delete stale hook from remote
    del org._stores["hooks"][stale_hook["id"]]

    # Second pull should remove the local stale file
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
        await download_destinations(
            destinations=(Path("source") / "primary",),
            project_path=Path("."),
        )

    assert not await stale_path.exists()
    assert await kept_path.exists()


@pytest.mark.asyncio
async def test_pull_extracts_formula_fields_to_py_files(tmp_path: Path, monkeypatch):
    """A schema with formula fields → each formula is extracted into its own .py file
    inside a `formulas/` directory next to schema.json."""
    _patch_git(monkeypatch)
    monkeypatch.chdir(tmp_path)

    org = build_simple_org()
    # Replace the default schema with one that contains formula fields
    schema = org._stores["schemas"][500002]
    schema["content"] = [
        {
            "category": "section",
            "id": "computed",
            "children": [
                {
                    "category": "datapoint",
                    "id": "total_with_tax",
                    "type": "number",
                    "formula": "subtotal * (1 + tax_rate)",
                },
                {
                    "category": "datapoint",
                    "id": "plain_field",
                    "type": "string",
                },
            ],
        }
    ]

    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)
    with patch.object(DownloadOrganizationDirectory, "initialize", lambda self: _inject_client(self, client)):
        await download_destinations(
            destinations=(Path("source") / "primary",),
            project_path=Path("."),
        )

    q_dir = tmp_path / "source" / "primary" / "workspaces" / "WS1_[500001]" / "queues" / "Q1_[500004]"
    formula_file = q_dir / settings.FORMULA_DIR_NAME / "total_with_tax.py"
    assert await formula_file.exists()
    assert "subtotal * (1 + tax_rate)" in await formula_file.read_text()

    # Plain (non-formula) datapoint should NOT produce a .py file
    assert not await (q_dir / settings.FORMULA_DIR_NAME / "plain_field.py").exists()
