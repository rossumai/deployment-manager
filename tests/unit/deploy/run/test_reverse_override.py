"""Tests for deploy/subcommands/run/reverse_override.py — `prd2 deploy template reverse`."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.reverse_override import (
    ObjectConfigReverser,
    QueueConfigReverse,
    reverse_source_target_in_yaml,
)
from deployment_manager.utils.consts import settings


def _make_client(fetch_one_responses: dict | None = None, request_json_responses: dict | None = None):
    """Build an async client mock that returns mapped responses by id or url."""
    client = MagicMock()
    client._http_client = MagicMock()
    client._http_client.fetch_one = AsyncMock(
        side_effect=lambda resource, id_: (fetch_one_responses or {}).get((resource, id_))
    )
    client.request_json = AsyncMock(
        side_effect=lambda method, url: (request_json_responses or {}).get(url)
    )
    return client


class TestReverseAttributeOverride:
    def test_uses_value_from_source_object_when_jmespath_resolves(self):
        reverser = ObjectConfigReverser(prev_source_client=MagicMock(), prev_target_client=MagicMock())
        prev_source = {"name": "DEV-name"}
        attribute_override = {"name": "PROD-name"}
        reverser.reverse_attribute_override(prev_source, attribute_override)
        assert attribute_override["name"] == "DEV-name"

    def test_jmespath_miss_currently_raises(self):
        # The function has a latent bug: when the JMESPath query returns None it
        # sets new_value = prev_value, but then immediately overwrites it with
        # result[0] (TypeError). This test documents the current behavior so the
        # next change to this function notices.
        reverser = ObjectConfigReverser(prev_source_client=MagicMock(), prev_target_client=MagicMock())
        prev_source = {"unrelated": "x"}
        attribute_override = {"missing.key": "fallback-value"}
        with pytest.raises(TypeError):
            reverser.reverse_attribute_override(prev_source, attribute_override)


@pytest.mark.asyncio
class TestObjectConfigReverser:
    async def test_swaps_source_and_target_ids(self):
        prev_source = {"id": 100, "name": "src-name"}
        prev_target = {"id": 200, "name": "tgt-name"}
        source_client = _make_client(
            fetch_one_responses={(Resource.Workspace, 100): prev_source}
        )
        target_client = _make_client(
            fetch_one_responses={(Resource.Workspace, 200): prev_target}
        )
        reverser = ObjectConfigReverser(prev_source_client=source_client, prev_target_client=target_client)

        obj = {"id": 100, "name": "old", "targets": [{"id": 200, "attribute_override": {}}]}
        await reverser.reverse_config(obj, Resource.Workspace)

        # IDs swapped
        assert obj["id"] == 200
        assert obj["targets"][0]["id"] == 100
        # Name updated to target's name
        assert obj["name"] == "tgt-name"

    async def test_skips_when_target_count_not_one(self):
        # Multi-target reverse is not supported — function returns without touching attributes
        source_client = MagicMock()
        target_client = MagicMock()
        reverser = ObjectConfigReverser(prev_source_client=source_client, prev_target_client=target_client)
        obj = {"id": 1, "targets": [{"id": 2}, {"id": 3}]}
        await reverser.reverse_config(obj, Resource.Workspace)
        # No fetch was made
        assert source_client._http_client.fetch_one.called is False


@pytest.mark.asyncio
class TestQueueConfigReverse:
    async def test_swaps_ids_and_rewrites_base_path(self):
        prev_source = {"id": 100, "name": "src-q", "workspace": "https://api/workspaces/55"}
        prev_target = {"id": 200, "name": "tgt-q", "workspace": "https://api/workspaces/77"}
        # Inbox/schema fetched too:
        prev_source_inbox = {"id": 300}
        prev_source_schema = {"id": 400}

        source_client = _make_client(
            fetch_one_responses={
                (Resource.Queue, 100): prev_source,
                (Resource.Inbox, 300): prev_source_inbox,
                (Resource.Schema, 400): prev_source_schema,
            },
            request_json_responses={
                "https://api/workspaces/55": {"id": 55, "name": "src-ws"},
            },
        )
        target_client = _make_client(
            fetch_one_responses={(Resource.Queue, 200): prev_target},
            request_json_responses={
                "https://api/workspaces/77": {"id": 77, "name": "tgt-ws"},
            },
        )

        queue_reverser = QueueConfigReverse(
            prev_source_client=source_client,
            prev_target_client=target_client,
            prev_source_dir="src_dir",
            prev_target_dir="tgt_dir",
        )

        obj = {
            "id": 100,
            "name": "old",
            "targets": [{"id": 200, "attribute_override": {}}],
            settings.DEPLOY_KEY_BASE_PATH: "src_dir/x/workspaces/src-ws_[55]",
            settings.DEPLOY_KEY_SCHEMA: {
                "id": 400,
                "targets": [{"id": 401, "attribute_override": {}}],
            },
            settings.DEPLOY_KEY_INBOX: {
                "id": 300,
                "targets": [{"id": 301, "attribute_override": {}}],
            },
        }

        await queue_reverser.reverse_config(obj, Resource.Queue)

        # Top-level IDs swapped
        assert obj["id"] == 200
        assert obj["targets"][0]["id"] == 100
        assert obj["name"] == "tgt-q"
        # base_path rewritten: src_dir → tgt_dir, src-ws_[55] → tgt-ws_[77]
        assert obj[settings.DEPLOY_KEY_BASE_PATH] == "tgt_dir/x/workspaces/tgt-ws_[77]"
        # Sub-objects (schema, inbox) IDs swapped too
        assert obj[settings.DEPLOY_KEY_SCHEMA]["id"] == 401
        assert obj[settings.DEPLOY_KEY_SCHEMA]["targets"][0]["id"] == 400
        assert obj[settings.DEPLOY_KEY_INBOX]["id"] == 301
        assert obj[settings.DEPLOY_KEY_INBOX]["targets"][0]["id"] == 300


@pytest.mark.asyncio
class TestReverseSourceTargetInYaml:
    async def test_swaps_dirs_urls_and_clears_unselected_hooks(self):
        # Build a minimal DeployYaml-shaped object (only .data is used)
        yaml_obj = SimpleNamespace(
            data={
                settings.DEPLOY_KEY_SOURCE_DIR: "src",
                settings.DEPLOY_KEY_TARGET_DIR: "tgt",
                settings.DEPLOY_KEY_SOURCE_URL: "https://src/api",
                settings.DEPLOY_KEY_TARGET_URL: "https://tgt/api",
                settings.DEPLOY_KEY_TOKEN_OWNER: 999,
                settings.DEPLOY_KEY_DEPLOYED_ORG_ID: 1,
                settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS: [42, 43],
                settings.DEPLOY_KEY_REVERSE_MAPPING: True,
                settings.DEPLOY_KEY_WORKSPACES: [],
                settings.DEPLOY_KEY_QUEUES: [],
                settings.DEPLOY_KEY_HOOKS: [],
            }
        )
        # Same-org case (both clients point to the same org id)
        source_org = SimpleNamespace(id=10)
        target_org = SimpleNamespace(id=10)

        result = await reverse_source_target_in_yaml(
            yaml=yaml_obj,
            source_org=source_org,
            target_org=target_org,
            prev_source_client=MagicMock(),
            prev_target_client=MagicMock(),
        )

        assert result.data[settings.DEPLOY_KEY_SOURCE_DIR] == "tgt"
        assert result.data[settings.DEPLOY_KEY_TARGET_DIR] == "src"
        assert result.data[settings.DEPLOY_KEY_SOURCE_URL] == "https://tgt/api"
        assert result.data[settings.DEPLOY_KEY_TARGET_URL] == "https://src/api"
        # source_org.id flows into deployed_org_id
        assert result.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] == 10
        assert result.data[settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS] == []
        assert result.data[settings.DEPLOY_KEY_REVERSE_MAPPING] is False
        # Same-org → token_owner stays
        assert result.data[settings.DEPLOY_KEY_TOKEN_OWNER] == 999

    async def test_does_not_mutate_input_yaml(self):
        yaml_obj = SimpleNamespace(
            data={
                settings.DEPLOY_KEY_SOURCE_DIR: "src",
                settings.DEPLOY_KEY_TARGET_DIR: "tgt",
                settings.DEPLOY_KEY_SOURCE_URL: "u1",
                settings.DEPLOY_KEY_TARGET_URL: "u2",
                settings.DEPLOY_KEY_TOKEN_OWNER: 1,
                settings.DEPLOY_KEY_DEPLOYED_ORG_ID: 1,
                settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS: [],
                settings.DEPLOY_KEY_REVERSE_MAPPING: True,
                settings.DEPLOY_KEY_WORKSPACES: [],
                settings.DEPLOY_KEY_QUEUES: [],
                settings.DEPLOY_KEY_HOOKS: [],
            }
        )
        before = dict(yaml_obj.data)
        await reverse_source_target_in_yaml(
            yaml=yaml_obj,
            source_org=SimpleNamespace(id=1),
            target_org=SimpleNamespace(id=1),
            prev_source_client=MagicMock(),
            prev_target_client=MagicMock(),
        )
        # Input yaml was deep-copied internally
        assert yaml_obj.data == before
