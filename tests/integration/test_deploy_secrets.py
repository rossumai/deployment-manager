"""Integration test: hook secrets are injected from `secrets_file` during deploy."""

import json
import pathlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.deploy.subcommands.run.run import deploy_release_file
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import settings
from deployment_manager.utils.functions import templatize_name_id
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org


async def _prepare_project(tmp_path: Path, org):
    config = {
        "directories": {
            "source": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
            "target": {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}},
        }
    }
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))


async def _write_source_tree(project_root: Path, org) -> None:
    await (project_root / "source" / "primary").mkdir(parents=True, exist_ok=True)
    await write_object_to_json(
        project_root / "source" / "organization.json",
        deepcopy(org._stores["organizations"][org.org_id]),
    )
    for h in org._stores["hooks"].values():
        hook_json = project_root / "source" / "primary" / "hooks" / f"{h['name']}_[{h['id']}].json"
        await write_object_to_json(hook_json, deepcopy(h))
        code = h.get("config", {}).get("code")
        if code and h.get("extension_source") != "rossum_store":
            await hook_json.with_suffix(".py").write_text(code)


def _patch_prompts(monkeypatch):
    confirm = MagicMock()
    confirm.ask_async = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.questionary.confirm",
        lambda *a, **kw: confirm,
    )


@pytest.mark.asyncio
async def test_deploy_injects_secrets_into_created_hook(tmp_path: Path, monkeypatch):
    """Secrets listed in secrets_file (keyed by templatized name_id) are sent with the hook."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    await _write_source_tree(tmp_path, org)

    # Write secrets file — key MUST match `templatize_name_id(name, id)` convention
    secrets_key = templatize_name_id("MyHook", 500003)
    secrets_file = tmp_path / "deploy_secrets" / "my_secrets.json"
    pathlib.Path(secrets_file.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(secrets_file).write_text(
        json.dumps({secrets_key: {"sftp_key": "PRIVATE_KEY_BLOB", "api_token": "xyz"}})
    )

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_TOKEN_OWNER: None,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: None,
        settings.DEPLOY_KEY_SECRETS_PATH: str(secrets_file),
        "patch_target_org": False,
        settings.DEPLOY_KEY_WORKSPACES: [],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [
            {"id": 500003, "name": "MyHook", "targets": [{"id": None}]}
        ],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/secrets.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "secrets.yaml"
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    hooks_before = set(org._stores["hooks"].keys())
    client = VirtualRossumClient(org)
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )

    new_hook_ids = set(org._stores["hooks"].keys()) - hooks_before
    assert len(new_hook_ids) == 1

    new_hook = org._stores["hooks"][new_hook_ids.pop()]
    # Secrets were sent along with the hook
    assert new_hook["secrets"] == {"sftp_key": "PRIVATE_KEY_BLOB", "api_token": "xyz"}


@pytest.mark.asyncio
async def test_deploy_without_secrets_file_leaves_hook_without_secrets(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch)

    org = build_simple_org()
    await _prepare_project(tmp_path, org)
    await _write_source_tree(tmp_path, org)

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_TOKEN_OWNER: None,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: None,
        # no secrets_file
        "patch_target_org": False,
        settings.DEPLOY_KEY_WORKSPACES: [],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [
            {"id": 500003, "name": "MyHook", "targets": [{"id": None}]}
        ],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/nosecrets.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "nosecrets.yaml"
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    hooks_before = set(org._stores["hooks"].keys())
    client = VirtualRossumClient(org)
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )

    new_hook_ids = set(org._stores["hooks"].keys()) - hooks_before
    new_hook = org._stores["hooks"][new_hook_ids.pop()]
    # The source hook has empty secrets; with no secrets_file, they stay empty
    assert new_hook["secrets"] == {}
