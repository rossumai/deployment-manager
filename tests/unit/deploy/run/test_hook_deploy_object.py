"""Tests for HookDeployObject.find_template_for_hook — gating of the source-org template lookup."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.hook_deploy_object import (
    HookDeployObject,
)

# Trigger model rebuild for forward refs (deploy_file: DeployOrchestrator)
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)


def _aiter(items):
    """Return an async-generator function yielding ``items`` (mimics fetch_all_by_url)."""

    async def _gen(*args, **kwargs):
        for item in items:
            yield item

    return _gen


def _make_deploy_file(target_templates, *, local_deploy, is_same_org=False):
    deploy_file = MagicMock()
    deploy_file.is_same_org = is_same_org
    deploy_file.local_deploy = local_deploy
    deploy_file.client._http_client.fetch_all_by_url = _aiter(target_templates)
    deploy_file.source_client.request_json = AsyncMock(return_value={"name": "My Template"})
    return deploy_file


@pytest.mark.asyncio
class TestFindTemplateForHook:
    async def test_local_deploy_matches_target_template_by_id(self):
        """With --ld the hook_template id is matched against TARGET templates, with no source call."""
        hook = HookDeployObject(
            id=1, name="h", data={"hook_template": "https://src.rossum.app/api/v1/hook_templates/55"}
        )
        # Target template has the SAME id but a DIFFERENT name — proving the match is by id, not name.
        hook.deploy_file = _make_deploy_file(
            [{"id": 55, "name": "Target Side Name", "url": "https://tgt.rossum.app/api/v1/hook_templates/55"}],
            local_deploy=True,
        )

        result = await hook.find_template_for_hook()

        hook.deploy_file.source_client.request_json.assert_not_awaited()
        assert result == "https://tgt.rossum.app/api/v1/hook_templates/55"

    async def test_local_deploy_falls_back_to_prompt_when_id_absent(self, monkeypatch):
        """With --ld, if the id is not present in the target org, fall back to the user prompt (still no source call)."""
        hook = HookDeployObject(
            id=1, name="h", data={"hook_template": "https://src.rossum.app/api/v1/hook_templates/55"}
        )
        hook.deploy_file = _make_deploy_file(
            [{"id": 900, "name": "Other", "url": "https://tgt.rossum.app/api/v1/hook_templates/900"}],
            local_deploy=True,
        )

        async def fake_prompt(self, hook_templates):
            return "PROMPTED_TEMPLATE_URL"

        monkeypatch.setattr(HookDeployObject, "get_hook_template_from_user", fake_prompt)

        result = await hook.find_template_for_hook()

        hook.deploy_file.source_client.request_json.assert_not_awaited()
        assert result == "PROMPTED_TEMPLATE_URL"

    async def test_cross_org_matches_template_via_source_name(self):
        """Without --ld the source template is fetched and matched against target templates by name."""
        hook = HookDeployObject(
            id=1, name="h", data={"hook_template": "https://src.rossum.app/api/v1/hook_templates/55"}
        )
        hook.deploy_file = _make_deploy_file(
            [{"name": "My Template", "url": "https://tgt.rossum.app/api/v1/hook_templates/900"}],
            local_deploy=False,
        )

        result = await hook.find_template_for_hook()

        hook.deploy_file.source_client.request_json.assert_awaited_once()
        assert result == "https://tgt.rossum.app/api/v1/hook_templates/900"
