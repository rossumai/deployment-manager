"""Tests for initialize command. The add_subdirs helper is tested pure.
The full CLI is mocked because it requires extensive interactive prompts."""

from unittest.mock import AsyncMock

import pytest

from deployment_manager.commands.initialize import add_subdirs
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
        assert directories["my-org"][settings.CONFIG_KEY_SUBDIRECTORIES]["dev"] == {
            settings.DOWNLOAD_KEY_REGEX: "DEV"
        }

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
