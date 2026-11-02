import asyncio
from unittest.mock import MagicMock

import pytest
from rossum_api import APIClientError
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.download.downloader import TYPES_WITH_COMPLETE_LIST_PAYLOAD, Downloader


def _make_downloader(lists: dict, details: dict | None = None):
    http = MagicMock()

    def fetch_all(type):
        async def gen():
            value = lists[type]
            if isinstance(value, Exception):
                raise value
            for item in value:
                yield item

        return gen()

    async def fetch_one(type, object_id):
        return (details or {})[(type, object_id)]

    http.fetch_all = MagicMock(side_effect=fetch_all)
    http.fetch_one = MagicMock(side_effect=fetch_one)
    client = MagicMock()
    client._http_client = http
    return Downloader.model_construct(client=client), http


@pytest.mark.asyncio
async def test_skip_refetch_types_use_list_items_in_order():
    items = [{"id": 2, "name": "b"}, {"id": 1, "name": "a"}]
    downloader, http = _make_downloader({Resource.Hook: items})
    result = await downloader.download_remote_objects(Resource.Hook)
    assert result == items
    http.fetch_one.assert_not_called()


@pytest.mark.asyncio
async def test_other_types_are_refetched():
    downloader, http = _make_downloader(
        {Resource.Schema: [{"id": 1}, {"id": 2}]},
        {(Resource.Schema, 1): {"id": 1, "content": []}, (Resource.Schema, 2): {"id": 2, "content": []}},
    )
    result = await downloader.download_remote_objects(Resource.Schema)
    assert result == [{"id": 1, "content": []}, {"id": 2, "content": []}]
    assert http.fetch_one.call_count == 2


@pytest.mark.asyncio
async def test_inaccessible_type_returns_empty_with_check_access():
    err = APIClientError("GET", "http://x/rules", 403, "forbidden")
    downloader, http = _make_downloader({Resource.Rule: err})
    assert await downloader.download_remote_objects(Resource.Rule, check_access=True) == []
    http.fetch_all.assert_called_once()


@pytest.mark.asyncio
async def test_error_without_check_access_propagates():
    err = APIClientError("GET", "http://x/hooks", 403, "forbidden")
    downloader, _ = _make_downloader({Resource.Hook: err})
    with pytest.raises(APIClientError):
        await downloader.download_remote_objects(Resource.Hook)


@pytest.mark.asyncio
async def test_fetch_one_shares_single_semaphore_across_types():
    in_flight = 0
    peak = 0

    async def fetch_one(type, object_id):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return {"id": object_id}

    downloader, http = _make_downloader(
        {Resource.Queue: [{"id": i} for i in range(10)], Resource.Schema: [{"id": i} for i in range(10)]}
    )
    http.fetch_one = fetch_one
    downloader._fetch_semaphore = asyncio.Semaphore(3)
    await asyncio.gather(
        downloader.download_remote_objects(Resource.Queue), downloader.download_remote_objects(Resource.Schema)
    )
    assert peak == 3


@pytest.mark.asyncio
async def test_error_after_first_item_propagates_with_check_access():
    err = APIClientError("GET", "http://x/rules?page=2", 503, "unavailable")

    async def gen():
        yield {"id": 1}
        raise err

    downloader, http = _make_downloader({})
    http.fetch_all = MagicMock(side_effect=lambda type: gen())
    with pytest.raises(APIClientError):
        await downloader.download_remote_objects(Resource.Rule, check_access=True)


def test_queue_and_schema_not_in_complete_list_payload_types():
    assert Resource.Queue not in TYPES_WITH_COMPLETE_LIST_PAYLOAD
    assert Resource.Schema not in TYPES_WITH_COMPLETE_LIST_PAYLOAD
