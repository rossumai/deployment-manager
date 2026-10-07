"""Tests for initialize command. The add_subdirs helper is tested pure.
The full CLI is mocked because it requires extensive interactive prompts."""

import json
import pathlib
import subprocess
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from anyio import Path

from deployment_manager.commands.initialize import (
    MODIFIED_BY_FILTER_NAME,
    add_subdirs,
    setup_modified_by_filter,
)
from deployment_manager.utils.consts import settings


@pytest.mark.asyncio
class TestAddSubdirs:
    async def test_add_single_subdir(self, monkeypatch):
        # First call to confirm says False so loop exits after first entry
        confirm_values = iter([False])

        def confirm_factory(*a, **kw):
            m = AsyncMock()
            m.ask_async = AsyncMock(side_effect=lambda: next(confirm_values))
            return m

        text_values = iter(["dev", "DEV"])

        def text_factory(*a, **kw):
            m = AsyncMock()
            m.ask_async = AsyncMock(side_effect=lambda: next(text_values))
            return m

        monkeypatch.setattr("deployment_manager.commands.initialize.questionary.confirm", confirm_factory)
        monkeypatch.setattr("deployment_manager.commands.initialize.questionary.text", text_factory)

        directories = {"my-org": {settings.CONFIG_KEY_SUBDIRECTORIES: {}}}
        await add_subdirs(directories, org_dir_name="my-org")

        assert "dev" in directories["my-org"][settings.CONFIG_KEY_SUBDIRECTORIES]
        assert directories["my-org"][settings.CONFIG_KEY_SUBDIRECTORIES]["dev"] == {settings.DOWNLOAD_KEY_REGEX: "DEV"}

    async def test_add_multiple_subdirs(self, monkeypatch):
        # loop: enters first automatically (empty subdirs); confirm True -> add another; then False
        confirm_values = iter([True, False])

        def confirm_factory(*a, **kw):
            m = AsyncMock()
            m.ask_async = AsyncMock(side_effect=lambda: next(confirm_values))
            return m

        text_values = iter(["dev", "DEV", "prod", "PROD"])

        def text_factory(*a, **kw):
            m = AsyncMock()
            m.ask_async = AsyncMock(side_effect=lambda: next(text_values))
            return m

        monkeypatch.setattr("deployment_manager.commands.initialize.questionary.confirm", confirm_factory)
        monkeypatch.setattr("deployment_manager.commands.initialize.questionary.text", text_factory)

        directories = {"my-org": {settings.CONFIG_KEY_SUBDIRECTORIES: {}}}
        await add_subdirs(directories, org_dir_name="my-org")

        subdirs = directories["my-org"][settings.CONFIG_KEY_SUBDIRECTORIES]
        assert set(subdirs.keys()) == {"dev", "prod"}


def _git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _write_json(path: pathlib.Path, data: dict):
    path.write_text(json.dumps(data, indent=2))


@pytest.mark.asyncio
class TestModifiedByFilter:
    @pytest_asyncio.fixture
    async def repo(self, tmp_path):
        repo = pathlib.Path(str(tmp_path))
        _git(repo, "init", "-q")
        await setup_modified_by_filter(Path(repo))
        return repo

    async def test_writes_gitattributes_and_git_config(self, repo):
        assert (repo / ".gitattributes").read_text() == f"*.json filter={MODIFIED_BY_FILTER_NAME}\n"
        assert _git(repo, "config", f"filter.{MODIFIED_BY_FILTER_NAME}.clean").strip()

    async def test_is_idempotent_and_keeps_existing_attributes(self, tmp_path):
        repo = pathlib.Path(str(tmp_path))
        _git(repo, "init", "-q")
        (repo / ".gitattributes").write_text("*.png binary")
        await setup_modified_by_filter(Path(repo))
        await setup_modified_by_filter(Path(repo))
        assert (repo / ".gitattributes").read_text() == f"*.png binary\n*.json filter={MODIFIED_BY_FILTER_NAME}\n"

    @pytest.mark.parametrize("modified_by_last", [True, False])
    async def test_modified_by_only_change_is_invisible_and_blob_stays_valid(self, repo, modified_by_last):
        def queue(modified_by):
            data = {"id": 1, "name": "q"}
            if modified_by_last:
                return {**data, "modified_by": modified_by}
            return {"modified_by": modified_by, **data}

        path = repo / "queue.json"
        _write_json(path, queue("https://x.rossum.app/api/v1/users/8"))
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "init")

        _write_json(path, queue("https://x.rossum.app/api/v1/users/9"))
        assert _git(repo, "status", "--porcelain") == ""

        assert json.loads(_git(repo, "show", "HEAD:queue.json"))["modified_by"] is None

    async def test_other_changes_are_still_tracked(self, repo):
        path = repo / "queue.json"
        _write_json(path, {"id": 1, "name": "q", "modified_by": "https://x/users/8"})
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "init")

        _write_json(path, {"id": 1, "name": "renamed", "modified_by": "https://x/users/9"})
        assert "queue.json" in _git(repo, "status", "--porcelain")
