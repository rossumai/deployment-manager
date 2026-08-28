"""Integration tests for `prd2 deploy revert` — deletes target objects previously deployed."""

import pathlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.deploy.subcommands.revert.revert import revert_release_file

# Importing the orchestrator triggers the pydantic forward-ref rebuilds
# (revert models reference Target/TargetWithDefault with forward refs to DeployObject)
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (  # noqa: F401
    DeployOrchestrator,
)
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import settings
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org


def _mock_confirm(monkeypatch, answer: bool):
    m = MagicMock()
    m.ask_async = AsyncMock(return_value=answer)
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.revert.revert.questionary.confirm",
        lambda *a, **kw: m,
    )


@pytest.mark.asyncio
async def test_revert_deletes_workspace_target(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, True)

    # Same-org setup: the 'target' workspace was created by a prior deploy
    org = build_simple_org()
    target_ws = org.add_workspace(name="Deployed WS", id_=800001)

    # Minimal project config + org file
    config = {
        "directories": {
            "source": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
            "target": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))
    await (tmp_path / "target" / "primary").mkdir(parents=True, exist_ok=True)
    await write_object_to_json(
        tmp_path / "target" / "organization.json",
        deepcopy(org._stores["organizations"][org.org_id]),
    )

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: org.org_id,
        settings.DEPLOY_KEY_WORKSPACES: [
            {"id": 500001, "name": "WS1", "targets": [{"id": target_ws["id"]}]}
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        "engines": [],
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "revert_me.yaml"
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.revert.revert.download_destinations",
        _noop_download,
    )

    client = VirtualRossumClient(org)
    await revert_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        target_client=client,
    )

    # Target workspace is gone; source workspace remains
    assert target_ws["id"] not in org._stores["workspaces"]
    assert 500001 in org._stores["workspaces"]

    # deployed_org_id cleared in deploy file
    rewritten = yaml.safe_load(pathlib.Path(deploy_file_path).read_text())
    assert rewritten[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] is None


@pytest.mark.asyncio
async def test_revert_declined_by_user_keeps_objects(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, False)

    org = build_simple_org()
    target_ws = org.add_workspace(name="Deployed WS", id_=800001)

    config = {
        "directories": {
            "source": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
            "target": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: org.org_id,
        settings.DEPLOY_KEY_WORKSPACES: [
            {"id": 500001, "name": "WS1", "targets": [{"id": target_ws["id"]}]}
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        "engines": [],
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "no_revert.yaml"
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    client = VirtualRossumClient(org)
    await revert_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        target_client=client,
    )

    # Both workspaces still exist
    assert target_ws["id"] in org._stores["workspaces"]


@pytest.mark.asyncio
async def test_revert_deletes_queues_before_engines(tmp_path: Path, monkeypatch):
    """The API refuses to delete an engine with active queues, so queues must be reverted first."""
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, True)

    from deployment_manager.commands.deploy.subcommands.revert import revert_deploy_file as rdf

    calls: list[str] = []

    def _recorder(name):
        async def _method(self, *args, **kwargs):
            calls.append(name)

        return _method

    for name in (
        "display_reverted_organization",
        "revert_hooks",
        "revert_rules",
        "revert_engines",
        "revert_queues",
        "revert_labels",
        "revert_workspaces",
    ):
        monkeypatch.setattr(
            rdf.RevertDeployFile,
            name,
            _recorder("org" if name == "display_reverted_organization" else name.removeprefix("revert_")),
        )

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_URL: "https://x.rossum.app/api/v1",
        settings.DEPLOY_KEY_TARGET_DIR: "",
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: 42,
        settings.DEPLOY_KEY_WORKSPACES: [],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        "engines": [],
        "rules": [],
        "labels": [],
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "order.yaml"
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    await revert_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        target_client=VirtualRossumClient(build_simple_org()),
    )

    # plan phase, then apply phase: rules before queues, queues before engines, in both
    expected_phase = ["hooks", "rules", "queues", "engines", "labels", "workspaces"]
    assert calls == ["org", *expected_phase, *expected_phase]


@pytest.mark.asyncio
async def test_revert_deletes_rule_target(tmp_path: Path, monkeypatch):
    """Rules listed in the deploy file must be deleted on revert (previously ignored entirely)."""
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, True)

    org = build_simple_org()
    # A rule that a prior deploy created on the target.
    from rossum_api.domain_logic.resources import Resource

    target_rule_id = 700123
    org._store(Resource.Rule)[target_rule_id] = {
        "id": target_rule_id,
        "name": "Deployed Rule",
        "url": org._build_url(Resource.Rule, target_rule_id),
    }

    config = {
        "directories": {
            "source": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
            "target": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: org.org_id,
        settings.DEPLOY_KEY_WORKSPACES: [],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        "engines": [],
        "rules": [{"id": 1, "name": "Rule", "targets": [{"id": target_rule_id}]}],
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "revert_rule.yaml"
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    await revert_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        target_client=VirtualRossumClient(org),
    )

    # Rule target deleted from the org, and its id cleared in the (rewritten) deploy file
    assert target_rule_id not in org._store(Resource.Rule)
    rewritten = yaml.safe_load(pathlib.Path(deploy_file_path).read_text())
    assert rewritten["rules"][0]["targets"][0]["id"] is None


@pytest.mark.asyncio
async def test_revert_deletes_label_target(tmp_path: Path, monkeypatch):
    """Labels listed in the deploy file must be deleted on revert (previously ignored entirely)."""
    monkeypatch.chdir(tmp_path)
    _mock_confirm(monkeypatch, True)

    org = build_simple_org()
    target_label_id = 700456
    # Labels are stored under the CustomResource.Label key ("labels").
    org._stores["labels"][target_label_id] = {
        "id": target_label_id,
        "name": "Deployed Label",
        "url": f"{org.base_url}/labels/{target_label_id}",
    }

    config = {
        "directories": {
            "source": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
            "target": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: org.org_id,
        settings.DEPLOY_KEY_WORKSPACES: [],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        "engines": [],
        "rules": [],
        "labels": [{"id": 1, "name": "Label", "targets": [{"id": target_label_id}]}],
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "revert_label.yaml"
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    await revert_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        target_client=VirtualRossumClient(org),
    )

    assert target_label_id not in org._stores["labels"]
    rewritten = yaml.safe_load(pathlib.Path(deploy_file_path).read_text())
    assert rewritten["labels"][0]["targets"][0]["id"] is None
