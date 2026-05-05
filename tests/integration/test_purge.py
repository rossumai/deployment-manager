"""Integration tests for the `prd2 purge` command.

Exercises the destructive object deletion flow using the virtual API.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.purge.directory import PurgeOrganizationDirectory
from deployment_manager.utils.consts import settings
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org


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


def _mock_confirm(monkeypatch, answer: bool):
    m = MagicMock()
    m.ask_async = AsyncMock(return_value=answer)
    monkeypatch.setattr(
        "deployment_manager.commands.purge.directory.questionary.confirm",
        lambda *a, **kw: m,
    )


@pytest.mark.asyncio
async def test_purge_deletes_workspaces_queues_hooks(tmp_path: Path, monkeypatch):
    """Delete workspaces, queues, hooks. Skipping schemas — there's a known upstream
    bug where the schema deletion path calls `extract_id_from_url` on an int."""
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, True)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)

    purge_dir = PurgeOrganizationDirectory(
        client=client,
        project_path=Path("."),
        name="source",
        org_id=org.org_id,
        purged_object_types=["workspaces", "queues", "hooks"],
        selected_subdirs=["primary"],
        subdirectories={},
    )

    await purge_dir.purge_organization()

    # Workspaces, queues and hooks purged
    assert org._stores["workspaces"] == {}
    assert org._stores["queues"] == {}
    assert org._stores["hooks"] == {}


@pytest.mark.asyncio
async def test_purge_single_type_only_deletes_that_type(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, True)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    ws_before = dict(org._stores["workspaces"])

    client = VirtualRossumClient(org)
    purge_dir = PurgeOrganizationDirectory(
        client=client,
        project_path=Path("."),
        name="source",
        org_id=org.org_id,
        purged_object_types=["hooks"],
        selected_subdirs=["primary"],
        subdirectories={},
    )

    await purge_dir.purge_organization()

    # Only hooks got removed; workspaces are untouched
    assert org._stores["hooks"] == {}
    assert org._stores["workspaces"] == ws_before


@pytest.mark.asyncio
async def test_purge_declined_by_user_deletes_nothing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, False)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)

    counts_before = {k: len(v) for k, v in org._stores.items()}

    client = VirtualRossumClient(org)
    purge_dir = PurgeOrganizationDirectory(
        client=client,
        project_path=Path("."),
        name="source",
        org_id=org.org_id,
        purged_object_types=[settings.ALL_OBJECTS],
        selected_subdirs=["primary"],
        subdirectories={},
    )

    await purge_dir.purge_organization()

    counts_after = {k: len(v) for k, v in org._stores.items()}
    assert counts_before == counts_after


@pytest.mark.asyncio
async def test_purge_unused_schemas_only(tmp_path: Path, monkeypatch):
    """An unused schema (not assigned to any queue) is deleted, used schemas stay."""
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, True)

    org = build_simple_org()
    # Add an extra schema that is NOT attached to any queue
    org.add_schema(name="Orphaned", id_=600001)

    await _prepare_project(tmp_path, org)

    client = VirtualRossumClient(org)
    purge_dir = PurgeOrganizationDirectory(
        client=client,
        project_path=Path("."),
        name="source",
        org_id=org.org_id,
        purged_object_types=[settings.UNUSED_SCHEMAS],
        selected_subdirs=["primary"],
        subdirectories={},
    )

    await purge_dir.purge_organization()

    # Orphaned schema gone; used schema (500002, attached to Q1) stays
    assert 600001 not in org._stores["schemas"]
    assert 500002 in org._stores["schemas"]
