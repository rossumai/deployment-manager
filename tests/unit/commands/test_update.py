from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from deployment_manager.commands.update import get_latest_version, get_specific_version


def _make_async_client_mock(response_status: int, response_json: dict):
    """Create a MagicMock that mimics `async with httpx.AsyncClient() as client`."""
    response = MagicMock()
    response.status_code = response_status
    response.json = MagicMock(return_value=response_json)

    client_instance = AsyncMock()
    client_instance.get = AsyncMock(return_value=response)

    async_client_cm = MagicMock()
    async_client_cm.__aenter__ = AsyncMock(return_value=client_instance)
    async_client_cm.__aexit__ = AsyncMock(return_value=False)

    return async_client_cm


@pytest.mark.asyncio
class TestGetLatestVersion:
    async def test_finds_whl_asset(self):
        release_info = {
            "tag_name": "v1.2.3",
            "assets": [
                {"name": "something.txt", "browser_download_url": "https://a"},
                {"name": "deployment_manager-1.2.3-py3-none-any.whl", "browser_download_url": "https://whl"},
            ],
        }
        cm = _make_async_client_mock(httpx.codes.OK, release_info)
        with patch("httpx.AsyncClient", return_value=cm):
            url, version = await get_latest_version()
            assert url == "https://whl"
            assert version == "1.2.3"

    async def test_strips_leading_v(self):
        release_info = {"tag_name": "V3.4.5", "assets": [{"name": "x.whl", "browser_download_url": "u"}]}
        cm = _make_async_client_mock(httpx.codes.OK, release_info)
        with patch("httpx.AsyncClient", return_value=cm):
            _, version = await get_latest_version()
            assert version == "3.4.5"

    async def test_no_whl_returns_nones(self):
        release_info = {"tag_name": "v1.2.3", "assets": [{"name": "x.txt", "browser_download_url": "u"}]}
        cm = _make_async_client_mock(httpx.codes.OK, release_info)
        with patch("httpx.AsyncClient", return_value=cm):
            url, version = await get_latest_version()
            assert url is None
            assert version is None

    async def test_http_error_returns_nones(self):
        cm = _make_async_client_mock(500, {})
        with patch("httpx.AsyncClient", return_value=cm):
            url, version = await get_latest_version()
            assert url is None
            assert version is None

    async def test_no_assets(self):
        cm = _make_async_client_mock(httpx.codes.OK, {"tag_name": "v1.0.0", "assets": []})
        with patch("httpx.AsyncClient", return_value=cm):
            url, version = await get_latest_version()
            assert url is None
            assert version is None


@pytest.mark.asyncio
class TestGetSpecificVersion:
    async def test_finds_whl(self):
        release_info = {
            "assets": [
                {"name": "deployment_manager-v1.0.0.whl", "browser_download_url": "https://whl"},
            ]
        }
        cm = _make_async_client_mock(httpx.codes.OK, release_info)
        with patch("httpx.AsyncClient", return_value=cm):
            url = await get_specific_version("v1.0.0")
            assert url == "https://whl"

    async def test_not_found_returns_none(self):
        cm = _make_async_client_mock(httpx.codes.NOT_FOUND, {})
        with patch("httpx.AsyncClient", return_value=cm):
            url = await get_specific_version("v99.99.99")
            assert url is None

    async def test_server_error_returns_none(self):
        cm = _make_async_client_mock(httpx.codes.INTERNAL_SERVER_ERROR, {})
        with patch("httpx.AsyncClient", return_value=cm):
            url = await get_specific_version("v1.0.0")
            assert url is None

    async def test_no_whl_asset_returns_none(self):
        release_info = {"assets": [{"name": "notes.txt", "browser_download_url": "u"}]}
        cm = _make_async_client_mock(httpx.codes.OK, release_info)
        with patch("httpx.AsyncClient", return_value=cm):
            url = await get_specific_version("v1.0.0")
            assert url is None

    async def test_url_uses_version_tag(self):
        """Verify the request URL contains the given version tag."""
        release_info = {"assets": [{"name": "x.whl", "browser_download_url": "u"}]}
        cm = _make_async_client_mock(httpx.codes.OK, release_info)

        captured = {}
        with patch("httpx.AsyncClient", return_value=cm):
            # Capture the URL passed into client.get()
            inner_client = cm.__aenter__.return_value

            async def fake_get(url):
                captured["url"] = url
                response = MagicMock()
                response.status_code = httpx.codes.OK
                response.json = MagicMock(return_value=release_info)
                return response

            inner_client.get = fake_get
            await get_specific_version("v7.8.9")
            assert "v7.8.9" in captured["url"]
