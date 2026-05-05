import json
import pathlib

import pytest
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.deploy.subcommands.run.merge.state import (
    DeploymentEntry,
    DeployState,
    LastAppliedEntry,
    ResourceDeployments,
)


class TestLastAppliedEntry:
    def test_default_values(self):
        entry = LastAppliedEntry()
        assert entry.forward is None
        assert entry.reverse is None
        assert entry.derived_fields == []

    def test_with_values(self):
        entry = LastAppliedEntry(forward={"x": 1}, derived_fields=["a.b"])
        assert entry.forward == {"x": 1}
        assert "a.b" in entry.derived_fields


class TestDeploymentEntry:
    def test_default(self):
        de = DeploymentEntry()
        assert isinstance(de.last_applied, LastAppliedEntry)


class TestResourceDeployments:
    def test_default(self):
        rd = ResourceDeployments()
        assert rd.deployments == {}

    def test_with_deployment(self):
        rd = ResourceDeployments(deployments={42: DeploymentEntry()})
        assert 42 in rd.deployments


class TestDeployState:
    def test_default_all_empty(self):
        state = DeployState()
        for field in [
            "organizations",
            "hooks",
            "labels",
            "email_templates",
            "schemas",
            "rules",
            "queues",
            "inboxes",
            "workspaces",
            "engines",
            "engine_fields",
        ]:
            assert getattr(state, field) == {}

    def test_load_deploy_state_missing_file(self, tmp_path):
        path = pathlib.Path(tmp_path / "no-such-state.json")
        state = DeployState.load_deploy_state(path)
        assert isinstance(state, DeployState)
        # Empty since missing
        assert state.hooks == {}

    def test_load_deploy_state_valid_file(self, tmp_path):
        path = pathlib.Path(tmp_path / "state.json")
        data = {
            "hooks": {
                "1": {
                    "deployments": {
                        "100": {
                            "last_applied": {
                                "forward": {"name": "hookname"},
                                "reverse": None,
                                "derived_fields": [],
                            }
                        }
                    }
                }
            }
        }
        path.write_text(json.dumps(data))
        state = DeployState.load_deploy_state(path)
        assert 1 in state.hooks
        assert 100 in state.hooks[1].deployments
        assert state.hooks[1].deployments[100].last_applied.forward == {"name": "hookname"}

    def test_get_last_applied_forward(self):
        state = DeployState()
        state.hooks[1] = ResourceDeployments(
            deployments={
                10: DeploymentEntry(
                    last_applied=LastAppliedEntry(
                        forward={"name": "n"}, derived_fields=["x.y"]
                    )
                )
            }
        )
        result = state.get_last_applied(Resource.Hook, source_id=1, target_id=10, direction="forward")
        assert result["name"] == "n"
        assert result["derived_fields"] == ["x.y"]

    def test_get_last_applied_missing(self):
        state = DeployState()
        result = state.get_last_applied(Resource.Hook, source_id=1, target_id=999, direction="forward")
        assert result is None

    def test_get_last_applied_reverse_when_none(self):
        state = DeployState()
        state.hooks[1] = ResourceDeployments(
            deployments={
                10: DeploymentEntry(
                    last_applied=LastAppliedEntry(forward={"name": "n"})
                )
            }
        )
        result = state.get_last_applied(Resource.Hook, source_id=1, target_id=10, direction="reverse")
        assert result is None


@pytest.mark.asyncio
async def test_write_deploy_state_creates_file(tmp_path):
    import anyio

    state = DeployState()
    state.hooks[1] = ResourceDeployments(
        deployments={
            10: DeploymentEntry(
                last_applied=LastAppliedEntry(forward={"foo": "bar"})
            )
        }
    )
    path = anyio.Path(tmp_path) / "deploy_state.json"
    await state.write_deploy_state(path)
    assert await path.exists()
    content = json.loads(await path.read_text())
    assert "hooks" in content
    assert content["hooks"]["1"]["deployments"]["10"]["last_applied"]["forward"] == {"foo": "bar"}
