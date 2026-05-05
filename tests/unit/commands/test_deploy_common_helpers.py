"""Tests for deploy/common/helpers.py - config lookup, admin check, credential validation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from anyio import Path
from rossum_api import APIClientError

from deployment_manager.commands.deploy.common.helpers import (
    InvalidCredentialsException,
    get_api_url_from_config,
    get_directory_from_config,
    get_org_id_from_config,
    get_token_from_cred_file,
    is_user_admin,
    validate_credentials,
)
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import Credentials
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


def _write_creds(tmp_path: Path, data: dict):
    import pathlib

    pathlib.Path(tmp_path / settings.CREDENTIALS_FILENAME).write_text(yaml.safe_dump(data))


@pytest.mark.asyncio
class TestGetTokenFromCredFile:
    async def test_returns_empty_when_no_creds_file(self, tmp_path):
        result = await get_token_from_cred_file(tmp_path, "https://api")
        assert result == ""

    async def test_returns_token_when_valid(self, tmp_path):
        _write_creds(tmp_path, {settings.CONFIG_KEY_TOKEN: "tk_valid"})
        with patch(
            "deployment_manager.commands.deploy.common.helpers.validate_credentials",
            new=AsyncMock(),
        ):
            result = await get_token_from_cred_file(tmp_path, "https://api")
        assert result == "tk_valid"

    async def test_prompts_for_new_token_when_invalid(self, tmp_path):
        _write_creds(tmp_path, {settings.CONFIG_KEY_TOKEN: "tk_old"})
        # First validate raises (old token bad); after user provides "tk_new", second validate succeeds
        validate_calls = []

        async def fake_validate(creds):
            validate_calls.append(creds.token)
            if creds.token == "tk_old":
                raise InvalidCredentialsException("expired")

        with patch(
            "deployment_manager.commands.deploy.common.helpers.validate_credentials",
            new=fake_validate,
        ), patch(
            "deployment_manager.commands.deploy.common.helpers.get_token_from_user",
            new=AsyncMock(return_value="tk_new"),
        ), patch(
            "deployment_manager.commands.deploy.common.helpers.write_prd_cred_file",
            new=AsyncMock(),
        ) as write_mock:
            result = await get_token_from_cred_file(tmp_path, "https://api")
        assert result == "tk_new"
        # Both old and new tokens were validated
        assert validate_calls == ["tk_old", "tk_new"]
        write_mock.assert_awaited_once()

    async def test_returns_empty_on_unexpected_exception(self, tmp_path):
        _write_creds(tmp_path, {settings.CONFIG_KEY_TOKEN: "tk"})
        with patch(
            "deployment_manager.commands.deploy.common.helpers.validate_credentials",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            result = await get_token_from_cred_file(tmp_path, "https://api")
        assert result == ""


@pytest.mark.asyncio
class TestValidateCredentials:
    async def test_raises_when_url_missing(self):
        with pytest.raises(Exception, match=settings.CONFIG_KEY_API_BASE_URL):
            await validate_credentials(Credentials(token="tk", url=""))

    async def test_raises_when_token_missing(self):
        with pytest.raises(Exception, match=settings.CONFIG_KEY_TOKEN):
            await validate_credentials(Credentials(token="", url="https://api"))

    async def test_raises_invalid_creds_on_401(self):
        client = MagicMock()
        client.request = AsyncMock(side_effect=APIClientError("get", "auth/user", 401, "Unauthorized"))
        with patch(
            "deployment_manager.commands.deploy.common.helpers.CustomAsyncAPIClient",
            return_value=client,
        ):
            with pytest.raises(InvalidCredentialsException):
                await validate_credentials(Credentials(token="bad", url="https://api"))

    async def test_reraises_other_api_errors(self):
        client = MagicMock()
        client.request = AsyncMock(side_effect=APIClientError("get", "auth/user", 500, "Server Error"))
        with patch(
            "deployment_manager.commands.deploy.common.helpers.CustomAsyncAPIClient",
            return_value=client,
        ):
            with pytest.raises(APIClientError):
                await validate_credentials(Credentials(token="x", url="https://api"))

    async def test_silent_when_request_succeeds(self):
        client = MagicMock()
        client.request = AsyncMock(return_value={"id": 1})
        with patch(
            "deployment_manager.commands.deploy.common.helpers.CustomAsyncAPIClient",
            return_value=client,
        ):
            # Should return None and not raise
            result = await validate_credentials(Credentials(token="ok", url="https://api"))
        assert result is None
