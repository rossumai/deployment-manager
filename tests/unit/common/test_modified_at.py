from unittest.mock import AsyncMock, MagicMock

import pytest
from rossum_api.domain_logic.resources import Resource

from deployment_manager.common.modified_at import check_modified_timestamp


@pytest.mark.asyncio
class TestCheckModifiedTimestamp:
    async def test_timestamps_match(self):
        client = MagicMock()
        client._http_client.fetch_one = AsyncMock(return_value={"modified_at": "2024-01-01T00:00:00Z"})
        result = await check_modified_timestamp(
            client, Resource.Hook, 1, {"modified_at": "2024-01-01T00:00:00Z"}
        )
        assert result is True

    async def test_timestamps_differ(self):
        client = MagicMock()
        client._http_client.fetch_one = AsyncMock(return_value={"modified_at": "2024-02-02T00:00:00Z"})
        result = await check_modified_timestamp(
            client, Resource.Hook, 1, {"modified_at": "2024-01-01T00:00:00Z"}
        )
        assert result is False

    async def test_missing_local_ts(self):
        """Default to empty string on both sides: a local without modified_at matches a remote without modified_at."""
        client = MagicMock()
        client._http_client.fetch_one = AsyncMock(return_value={})
        assert await check_modified_timestamp(client, Resource.Hook, 1, {}) is True

    async def test_missing_local_but_remote_has(self):
        client = MagicMock()
        client._http_client.fetch_one = AsyncMock(return_value={"modified_at": "2024"})
        assert await check_modified_timestamp(client, Resource.Hook, 1, {}) is False
