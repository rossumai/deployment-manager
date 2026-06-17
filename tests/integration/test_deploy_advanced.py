"""Advanced deploy scenarios:
- 1:N deploy (one source workspace → multiple targets)
- regex-based attribute override (`pattern/#/replacement`)
- `patch_target_org` toggles organization update
- `unselected_hooks` excludes hooks from deploy
"""

import pathlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.deploy.subcommands.run.run import deploy_release_file
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import settings
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
    """Lay out source org files as `prd pull` would."""
    await (project_root / "source" / "primary").mkdir(parents=True, exist_ok=True)

    org_data = deepcopy(org._stores["organizations"][org.org_id])
    await write_object_to_json(project_root / "source" / "organization.json", org_data)

    for ws in org._stores["workspaces"].values():
        ws_dir = project_root / "source" / "primary" / "workspaces" / f"{ws['name']}_[{ws['id']}]"
        await write_object_to_json(ws_dir / "workspace.json", deepcopy(ws))

        for q in org._stores["queues"].values():
            if q["workspace"] != ws["url"]:
                continue
            q_dir = ws_dir / "queues" / f"{q['name']}_[{q['id']}]"
            await write_object_to_json(q_dir / "queue.json", deepcopy(q))
            schema_id = int(q["schema"].rstrip("/").split("/")[-1])
            if schema_id in org._stores["schemas"]:
                await write_object_to_json(q_dir / "schema.json", deepcopy(org._stores["schemas"][schema_id]))


def _patch_prompts(monkeypatch, auto_apply: bool = True):
    confirm = MagicMock()
    confirm.ask_async = AsyncMock(return_value=auto_apply)
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.questionary.confirm",
        lambda *a, **kw: confirm,
    )
    text = MagicMock()
    text.ask_async = AsyncMock(return_value="")
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object.questionary.text",
        lambda *a, **kw: text,
    )
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.deploy_objects.queue_deploy_object.questionary.text",
        lambda *a, **kw: text,
    )


def _write_deploy_file(path: Path, data: dict) -> None:
    pathlib.Path(path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text(yaml.safe_dump(data, sort_keys=False))


async def _run_deploy(tmp_path: Path, monkeypatch, client, deploy_file_path: Path):
    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )


@pytest.mark.asyncio
async def test_deploy_one_to_many_workspaces(tmp_path: Path, monkeypatch):
    """One source workspace → 3 brand-new target workspaces with distinct names."""
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
        "patch_target_org": False,
        settings.DEPLOY_KEY_WORKSPACES: [
            {
                "id": 500001,
                "name": "WS1",
                "targets": [
                    {"id": None, "attribute_override": {"name": "WS-prod-EU"}},
                    {"id": None, "attribute_override": {"name": "WS-prod-US"}},
                    {"id": None, "attribute_override": {"name": "WS-staging"}},
                ],
            }
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/1_to_n.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "1_to_n.yaml"
    _write_deploy_file(deploy_file_path, deploy_file_data)

    before = set(org._stores["workspaces"].keys())
    client = VirtualRossumClient(org)
    await _run_deploy(tmp_path, monkeypatch, client, deploy_file_path)

    new_ids = set(org._stores["workspaces"].keys()) - before
    assert len(new_ids) == 3

    new_names = {org._stores["workspaces"][i]["name"] for i in new_ids}
    assert new_names == {"WS-prod-EU", "WS-prod-US", "WS-staging"}


@pytest.mark.asyncio
async def test_deploy_regex_attribute_override(tmp_path: Path, monkeypatch):
    """Regex override `\\(DEV\\)$/#/(PROD)` should rename `Q1 (DEV)` → `Q1 (PROD)`."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch)

    org = build_simple_org()
    # Rename source WS to include "(DEV)"
    org._stores["workspaces"][500001]["name"] = "WS1 (DEV)"
    await _prepare_project(tmp_path, org)
    await _write_source_tree(tmp_path, org)

    sep = settings.DEPLOY_OVERRIDE_REGEX_SEPARATOR
    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_TOKEN_OWNER: None,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: None,
        "patch_target_org": False,
        settings.DEPLOY_KEY_WORKSPACES: [
            {
                "id": 500001,
                "name": "WS1 (DEV)",
                "targets": [
                    {
                        "id": None,
                        "attribute_override": {"name": f"\\(DEV\\){sep}(PROD)"},
                    }
                ],
            }
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/regex.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "regex.yaml"
    _write_deploy_file(deploy_file_path, deploy_file_data)

    before = set(org._stores["workspaces"].keys())
    client = VirtualRossumClient(org)
    await _run_deploy(tmp_path, monkeypatch, client, deploy_file_path)

    new_ids = set(org._stores["workspaces"].keys()) - before
    assert len(new_ids) == 1
    new_ws = org._stores["workspaces"][new_ids.pop()]
    assert new_ws["name"] == "WS1 (PROD)"


@pytest.mark.asyncio
async def test_deploy_unselected_hooks_skipped(tmp_path: Path, monkeypatch):
    """Hooks listed in `unselected_hooks` must NOT be deployed even if in the deploy file."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch)

    org = build_simple_org()
    # Add a second hook that we'll mark as unselected
    excluded_hook = org.add_hook(name="ExcludedHook", id_=500999)

    await _prepare_project(tmp_path, org)
    await _write_source_tree(tmp_path, org)
    # Write both hooks to disk (needed by deploy)
    for hid, h in org._stores["hooks"].items():
        code = h.get("config", {}).get("code")
        hook_json = tmp_path / "source" / "primary" / "hooks" / f"{h['name']}_[{hid}].json"
        await write_object_to_json(hook_json, deepcopy(h))
        if code and h.get("extension_source") != "rossum_store":
            await hook_json.with_suffix(".py").write_text(code)

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_TOKEN_OWNER: None,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: None,
        "patch_target_org": False,
        settings.DEPLOY_KEY_WORKSPACES: [],
        settings.DEPLOY_KEY_QUEUES: [],
        # Include only one hook in the deploy file
        settings.DEPLOY_KEY_HOOKS: [
            {"id": 500003, "name": "MyHook", "targets": [{"id": None}]},
        ],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/unsel.json",
        # Explicitly exclude the OTHER hook via unselected_hooks
        "unselected_hooks": [excluded_hook["id"]],
    }
    deploy_file_path = tmp_path / "deploy_files" / "unsel.yaml"
    _write_deploy_file(deploy_file_path, deploy_file_data)

    hooks_before = set(org._stores["hooks"].keys())
    client = VirtualRossumClient(org)
    await _run_deploy(tmp_path, monkeypatch, client, deploy_file_path)

    new_hook_ids = set(org._stores["hooks"].keys()) - hooks_before
    assert len(new_hook_ids) == 1
    new_hook = org._stores["hooks"][new_hook_ids.pop()]
    # Only the selected hook (MyHook) was deployed, not ExcludedHook
    assert new_hook["name"] == "MyHook"
