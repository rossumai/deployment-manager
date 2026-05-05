"""Tests for HookReferenceReplacer — run_after chain handling."""

from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock

import pytest
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.hook_reference_replacer import (
    HookReferenceReplacer,
)

# Trigger model rebuilds
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)
from deployment_manager.commands.deploy.subcommands.run.models import Target


def _make_parent():
    parent = MagicMock()
    parent.deploy_file.source_client._http_client.base_url = "https://src.rossum.app/api/v1"
    parent.deploy_file.client._http_client.base_url = "https://tgt.rossum.app/api/v1"
    return parent


@pytest.mark.asyncio
class TestReplaceHookRunAfterList:
    async def test_replaces_mapped_hooks(self):
        rr = HookReferenceReplacer(parent_object_reference=_make_parent())
        targets = [Target(id=600001)]
        lookup = defaultdict(dict)
        lookup[500010][Resource.Hook] = targets
        reverse = defaultdict(dict)

        obj = {"run_after": ["https://src.rossum.app/api/v1/hooks/500010"]}
        result = await rr.replace_hook_run_after_list(
            object=obj,
            target_index=0,
            target_objects_count=1,
            lookup_table=lookup,
            reverse_lookup_table=reverse,
            use_dummy_references=True,
        )
        assert result == ["https://tgt.rossum.app/api/v1/hooks/600001"]

    async def test_empty_run_after(self):
        rr = HookReferenceReplacer(parent_object_reference=_make_parent())
        result = await rr.replace_hook_run_after_list(
            object={"run_after": []},
            target_index=0,
            target_objects_count=1,
            lookup_table={},
            reverse_lookup_table={},
            use_dummy_references=True,
        )
        assert result == []

    async def test_missing_chain_hook_skips_to_predecessor(self):
        """A→B→C where B isn't deployed: A ends up calling C's predecessor resolution."""
        parent = _make_parent()
        # predecessor B's source has run_after = [A]
        predecessor_hook = MagicMock()
        predecessor_hook.run_after = ["https://src.rossum.app/api/v1/hooks/500010"]
        # Include the rest of required Hook dataclass fields
        import dataclasses

        @dataclasses.dataclass
        class FakeHook:
            run_after: list

        parent.deploy_file.source_client.retrieve_hook = AsyncMock(
            return_value=FakeHook(run_after=["https://src.rossum.app/api/v1/hooks/500010"])
        )

        rr = HookReferenceReplacer(parent_object_reference=parent)
        # A has target id 600010
        lookup = defaultdict(dict)
        lookup[500010][Resource.Hook] = [Target(id=600010)]
        # B (500020) is NOT in lookup — simulating "B was not deployed"
        reverse = defaultdict(dict)

        obj = {"run_after": ["https://src.rossum.app/api/v1/hooks/500020"]}
        result = await rr.replace_hook_run_after_list(
            object=obj,
            target_index=0,
            target_objects_count=1,
            lookup_table=lookup,
            reverse_lookup_table=reverse,
            use_dummy_references=True,
        )
        # Since B has no target, we walk up to its predecessor A → target 600010
        assert result == ["https://tgt.rossum.app/api/v1/hooks/600010"]


@pytest.mark.asyncio
class TestFindMissingHookRunAfter:
    async def test_returns_empty_on_error(self):
        parent = _make_parent()
        # retrieve_hook raises
        parent.deploy_file.source_client.retrieve_hook = AsyncMock(side_effect=RuntimeError("boom"))

        rr = HookReferenceReplacer(parent_object_reference=parent)
        result = await rr.find_missing_hook_run_after(
            predecessor_url="https://src.rossum.app/api/v1/hooks/999",
            lookup_table={},
            reverse_lookup_table={},
            target_objects_count=1,
            target_index=0,
        )
        assert result == []
