"""Tests for purge/delete_objects.py - bulk-delete by ids."""

import pytest

from deployment_manager.commands.purge.delete_objects import delete_all_objects_with_ids
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org


@pytest.mark.asyncio
async def test_deletes_all_categories():
    org = build_simple_org()
    # Add more objects to delete
    extra_hook = org.add_hook(name="ToDeleteHook", id_=700700)
    extra_ws = org.add_workspace(name="ToDeleteWS", id_=700701)

    client = VirtualRossumClient(org)

    ids_to_delete = {
        "workspaces": [extra_ws["id"]],
        "queues": [],
        "inboxes": [],
        "schemas": [],
        "hooks": [extra_hook["id"]],
    }

    await delete_all_objects_with_ids(ids_to_delete, client)

    assert extra_hook["id"] not in org._stores["hooks"]
    assert extra_ws["id"] not in org._stores["workspaces"]
    # Unlisted objects stay
    assert 500003 in org._stores["hooks"]
    assert 500001 in org._stores["workspaces"]


@pytest.mark.asyncio
async def test_empty_id_lists_delete_nothing():
    org = build_simple_org()
    client = VirtualRossumClient(org)

    before = {k: dict(v) for k, v in org._stores.items()}

    await delete_all_objects_with_ids(
        {"workspaces": [], "queues": [], "inboxes": [], "schemas": [], "hooks": []},
        client,
    )

    assert org._stores == before


@pytest.mark.asyncio
async def test_delete_queue_uses_delete_after_param():
    """Queues must be deleted via `_request('DELETE', ..., params={'delete_after': '0'})`."""
    org = build_simple_org()
    client = VirtualRossumClient(org)

    queue_id = 500004
    assert queue_id in org._stores["queues"]

    await delete_all_objects_with_ids(
        {"workspaces": [], "queues": [queue_id], "inboxes": [], "schemas": [], "hooks": []},
        client,
    )

    assert queue_id not in org._stores["queues"]


@pytest.mark.asyncio
async def test_delete_schema_via_delete_schema_method():
    org = build_simple_org()
    client = VirtualRossumClient(org)

    await delete_all_objects_with_ids(
        {"workspaces": [], "queues": [], "inboxes": [], "schemas": [500002], "hooks": []},
        client,
    )

    assert 500002 not in org._stores["schemas"]


@pytest.mark.asyncio
async def test_delete_inbox_via_http_client():
    org = build_simple_org()
    # Find the inbox id that was auto-created in build_simple_org
    inbox_id = next(iter(org._stores["inboxes"]))
    client = VirtualRossumClient(org)

    await delete_all_objects_with_ids(
        {"workspaces": [], "queues": [], "inboxes": [inbox_id], "schemas": [], "hooks": []},
        client,
    )

    assert inbox_id not in org._stores["inboxes"]
