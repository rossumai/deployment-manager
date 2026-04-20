"""Tests for deploy/common/helpers.py - config lookup, admin check."""

from unittest.mock import MagicMock

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.deploy.common.helpers import (
    get_api_url_from_config,
    get_directory_from_config,
    get_org_id_from_config,
    is_user_admin,
)
from deployment_manager.utils.consts import settings


def _make_config(tmp_path: Path, data: dict):
    import pathlib

    pathlib.Path(tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(data))


@pytest.mark.asyncio
class TestGetApiUrlFromConfig:
    async def test_returns_api_base_for_configured_org(self, tmp_path):
        _make_config(
            tmp_path,
            {
                "directories": {
                    "sandbox": {"api_base": "https://sandbox.rossum.app/api/v1"},
                    "prod": {"api_base": "https://prod.rossum.app/api/v1"},
                }
            },
        )
        assert await get_api_url_from_config(tmp_path, "sandbox") == "https://sandbox.rossum.app/api/v1"
        assert await get_api_url_from_config(tmp_path, "prod") == "https://prod.rossum.app/api/v1"

    async def test_unknown_org_returns_empty(self, tmp_path):
        _make_config(tmp_path, {"directories": {"sandbox": {"api_base": "https://a"}}})
        assert await get_api_url_from_config(tmp_path, "missing") == ""

    async def test_no_config_returns_empty(self, tmp_path):
        assert await get_api_url_from_config(tmp_path, "whatever") == ""


@pytest.mark.asyncio
class TestGetDirectoryFromConfig:
    async def test_returns_org_subtree(self, tmp_path):
        _make_config(
            tmp_path,
            {
                "directories": {
                    "sandbox": {
                        "api_base": "https://a",
                        "org_id": 42,
                        "subdirectories": {"dev": {}},
                    }
                }
            },
        )
        result = await get_directory_from_config(tmp_path, "sandbox")
        assert result["org_id"] == 42
        assert "dev" in result["subdirectories"]

    async def test_missing_org_returns_empty(self, tmp_path):
        _make_config(tmp_path, {"directories": {}})
        assert await get_directory_from_config(tmp_path, "foo") == {}


@pytest.mark.asyncio
class TestGetOrgIdFromConfig:
    async def test_returns_int(self, tmp_path):
        _make_config(tmp_path, {"directories": {"sandbox": {"org_id": "123"}}})
        result = await get_org_id_from_config(tmp_path, "sandbox")
        assert result == 123

    async def test_missing_returns_none(self, tmp_path):
        _make_config(tmp_path, {"directories": {}})
        # missing org id converts to "" which int() rejects; falls through to None
        assert await get_org_id_from_config(tmp_path, "missing") is None


def _make_role(url, name):
    """MagicMock's `name` kwarg is reserved; use configure_mock for .name attribute."""
    role = MagicMock(url=url)
    role.name = name
    return role


class TestIsUserAdmin:
    def test_user_with_admin_role_returns_true(self):
        admin_role = _make_role("https://api/v1/groups/1", "admin")
        other_role = _make_role("https://api/v1/groups/2", "annotator")
        user = MagicMock(groups=["https://api/v1/groups/1"])

        assert is_user_admin(user, [admin_role, other_role]) is True

    def test_user_with_org_admin_role(self):
        org_admin = _make_role("https://api/v1/groups/5", "organization_group_admin")
        user = MagicMock(groups=["https://api/v1/groups/5"])

        assert is_user_admin(user, [org_admin]) is True

    def test_non_admin_user(self):
        other = _make_role("https://api/v1/groups/2", "annotator")
        user = MagicMock(groups=["https://api/v1/groups/2"])
        assert is_user_admin(user, [other]) is False

    def test_empty_roles(self):
        user = MagicMock(groups=["https://api/v1/groups/1"])
        assert is_user_admin(user, []) is False
