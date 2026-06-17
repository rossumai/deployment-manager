"""End-to-end deploy flow: virtual source org → virtual target org.

We use a SAME-ORG deploy (source_org.id == target_org.id) to avoid
token_owner and cross-org-specific prompts. This exercises:
  - loading deploy_file.yaml and orchestrator initialization
  - writing source objects to disk under source_dir
  - creating/updating target objects via the virtual API
  - reference replacement (workspace → organization, queue → workspace/schema)
  - deploy state persistence
"""

import json
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from anyio import Path

from deployment_manager.commands.deploy.subcommands.run.run import deploy_release_file
from deployment_manager.common.read_write import write_object_to_json
from deployment_manager.utils.consts import settings
from tests.integration.virtual_api import (
    VirtualRossumClient,
    VirtualRossumOrg,
    build_empty_target_org,
    build_simple_org,
)


async def _write_project_config(project_root: Path, org) -> None:
    """Write a minimal prd_config.yaml. Source and target dirs live side by side."""
    config = {
        "directories": {
            "source": {
                "org_id": org.org_id,
                "api_base": org.base_url,
                "subdirectories": {"primary": {"regex": ""}},
            },
            "target": {
                "org_id": org.org_id,
                "api_base": org.base_url,
                "subdirectories": {"primary": {"regex": ""}},
            },
        }
    }
    await (project_root / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))


async def _write_source_tree(project_root: Path, org) -> None:
    """Lay out the source org's files on disk the same way `prd pull` would."""
    await (project_root / "source" / "primary").mkdir(parents=True, exist_ok=True)

    # Organization
    org_data = deepcopy(org._stores["organizations"][org.org_id])
    await write_object_to_json(project_root / "source" / "organization.json", org_data)

    # Workspaces
    for ws in org._stores["workspaces"].values():
        ws_dir = project_root / "source" / "primary" / "workspaces" / f"{ws['name']}_[{ws['id']}]"
        await write_object_to_json(ws_dir / "workspace.json", deepcopy(ws))

        # Queues under this workspace
        for q in org._stores["queues"].values():
            if q["workspace"] != ws["url"]:
                continue
            q_dir = ws_dir / "queues" / f"{q['name']}_[{q['id']}]"
            await write_object_to_json(q_dir / "queue.json", deepcopy(q))

            # Schema
            schema_id = int(q["schema"].rstrip("/").split("/")[-1])
            schema = org._stores["schemas"].get(schema_id)
            if schema:
                await write_object_to_json(q_dir / "schema.json", deepcopy(schema))

            # Inbox
            if q.get("inbox"):
                inbox_id = int(q["inbox"].rstrip("/").split("/")[-1])
                inbox = org._stores["inboxes"].get(inbox_id)
                if inbox:
                    await write_object_to_json(q_dir / "inbox.json", deepcopy(inbox))


async def _write_hooks(project_root: Path, org) -> None:
    for h in org._stores["hooks"].values():
        hook_file = project_root / "source" / "primary" / "hooks" / f"{h['name']}_[{h['id']}].json"
        await write_object_to_json(hook_file, deepcopy(h))

        code = h.get("config", {}).get("code")
        if code and h.get("extension_source") != "rossum_store":
            suffix = ".py" if "python" in h.get("config", {}).get("runtime", "") else ".js"
            code_file = hook_file.with_suffix(suffix)
            await code_file.write_text(code)


def _patch_prompts(monkeypatch, auto_apply: bool = True):
    """Make all questionary prompts non-interactive."""
    confirm_mock = MagicMock()
    confirm_mock.ask_async = AsyncMock(return_value=auto_apply)
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.questionary.confirm",
        lambda *a, **kw: confirm_mock,
    )

    text_mock = MagicMock()
    text_mock.ask_async = AsyncMock(return_value="")
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.deploy_objects.base_deploy_object.questionary.text",
        lambda *a, **kw: text_mock,
    )

    # Also patch the queue's prompt_pending_warnings
    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.deploy_objects.queue_deploy_object.questionary.text",
        lambda *a, **kw: text_mock,
    )


def _write_deploy_file(deploy_file_path: Path, data: dict) -> None:
    # Use sync write since called outside async ctx
    import pathlib

    deploy_file_path.parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(str(deploy_file_path)).write_text(yaml.safe_dump(data, sort_keys=False))


@pytest.mark.asyncio
async def test_deploy_creates_new_workspace_in_same_org(tmp_path: Path, monkeypatch):
    """A workspace with target.id=None triggers a CREATE of a new workspace in the same org."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    org = build_simple_org()
    await _write_project_config(tmp_path, org)
    await _write_source_tree(tmp_path, org)

    # Minimal deploy file: just the single workspace, no queues/hooks
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
                "targets": [{"id": None}],
            }
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/state.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "basic_ws.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    # Also skip the follow-up pull at the end
    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    workspaces_before = set(org._stores["workspaces"].keys())

    client = VirtualRossumClient(org)
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )

    workspaces_after = set(org._stores["workspaces"].keys())
    # One new workspace should have been created in the org
    assert len(workspaces_after - workspaces_before) == 1

    new_ws_id = (workspaces_after - workspaces_before).pop()
    new_ws = org._stores["workspaces"][new_ws_id]
    assert new_ws["name"] == "WS1"
    # organization URL should be set to the org's URL
    assert new_ws["organization"] == org._stores["organizations"][org.org_id]["url"]


@pytest.mark.asyncio
async def test_deploy_updates_existing_workspace(tmp_path: Path, monkeypatch):
    """Target.id points to an existing workspace → deploy performs an UPDATE."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    org = build_simple_org()
    # Pre-create a target workspace
    target_ws = org.add_workspace(name="Target WS", id_=700001)

    await _write_project_config(tmp_path, org)
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
                    {
                        "id": target_ws["id"],
                        "attribute_override": {"name": "Renamed by deploy"},
                    }
                ],
            }
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/state.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "update_ws.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    client = VirtualRossumClient(org)
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )

    # Target workspace must be renamed (attribute_override applied)
    updated = org._stores["workspaces"][target_ws["id"]]
    assert updated["name"] == "Renamed by deploy"


@pytest.mark.asyncio
async def test_deploy_writes_state_and_updates_deploy_file(tmp_path: Path, monkeypatch):
    """After a successful deploy, the deploy file is rewritten with deployed_org_id and last_deployed_at."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    org = build_simple_org()
    await _write_project_config(tmp_path, org)
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
            {"id": 500001, "name": "WS1", "targets": [{"id": None}]}
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/state.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "state.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    client = VirtualRossumClient(org)
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )

    # Deploy file should have deployed_org_id and last_deployed_at set after success
    rewritten = yaml.safe_load(pathlib.Path(deploy_file_path).read_text())
    assert rewritten[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] == org.org_id
    assert rewritten[settings.DEPLOY_KEY_LAST_DEPLOYED_AT] is not None

    # A deploy state file must have been written
    state_file = tmp_path / "deploy_states" / "state.json"
    assert await state_file.exists()
    state = json.loads(await state_file.read_text())
    assert "workspaces" in state
    # The source workspace should now have a deployment entry
    assert "500001" in state["workspaces"]


@pytest.mark.asyncio
async def test_deploy_user_rejects_plan_makes_no_changes(tmp_path: Path, monkeypatch):
    """If the user answers 'no' to 'apply the plan?', nothing should be created."""
    monkeypatch.chdir(tmp_path)
    # User answers No to "apply the plan?"
    _patch_prompts(monkeypatch, auto_apply=False)

    org = build_simple_org()
    await _write_project_config(tmp_path, org)
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
            {"id": 500001, "name": "WS1", "targets": [{"id": None}]}
        ],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/state.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "rejected.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    workspaces_before = dict(org._stores["workspaces"])

    client = VirtualRossumClient(org)
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=False,  # Rely on the (mocked) questionary answer
        prefer="",
    )

    # No workspaces should have been created
    assert set(org._stores["workspaces"].keys()) == set(workspaces_before.keys())


@pytest.mark.asyncio
async def test_deploy_deploy_file_missing_required_keys(tmp_path: Path, monkeypatch):
    """If the deploy file is missing required keys, the command exits early without side effects."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch)

    org = build_simple_org()
    await _write_project_config(tmp_path, org)
    await _write_source_tree(tmp_path, org)

    # Missing source_dir
    deploy_file_path = tmp_path / "deploy_files" / "bad.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump({settings.DEPLOY_KEY_TARGET_URL: org.base_url}))

    client = VirtualRossumClient(org)
    # Should complete without raising
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )

    # No workspaces created
    assert 500001 in org._stores["workspaces"]  # only original source WS


async def _write_cross_org_project_config(project_root: Path, source_org: VirtualRossumOrg, target_org: VirtualRossumOrg) -> None:
    """Write prd_config.yaml with two distinct org directories."""
    config = {
        "directories": {
            "source": {
                "org_id": source_org.org_id,
                "api_base": source_org.base_url,
                "subdirectories": {"primary": {"regex": ""}},
            },
            "target": {
                "org_id": target_org.org_id,
                "api_base": target_org.base_url,
                "subdirectories": {"primary": {"regex": ""}},
            },
        }
    }
    await (project_root / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))


@pytest.mark.asyncio
async def test_deploy_hook_queue_references_remapped_to_target(tmp_path: Path, monkeypatch):
    """Same-org deploy of hook + queue: the hook.queues URL must be remapped
    from source queue ID to the newly-created target queue ID."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    org = build_simple_org()
    target_ws = org.add_workspace(name="Target WS", id_=700001)

    await _write_project_config(tmp_path, org)
    await _write_source_tree(tmp_path, org)
    await _write_hooks(tmp_path, org)

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: org.base_url,
        settings.DEPLOY_KEY_TOKEN_OWNER: None,
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: None,
        "patch_target_org": False,
        settings.DEPLOY_KEY_WORKSPACES: [
            {"id": 500001, "name": "WS1", "targets": [{"id": target_ws["id"]}]}
        ],
        settings.DEPLOY_KEY_QUEUES: [
            {
                "id": 500004,
                "name": "Q1",
                "ignore_deploy_warnings": True,
                "base_path": "source/primary/workspaces/WS1_[500001]",
                "targets": [{"id": None}],
                "schema": {"id": 500002, "targets": [{"id": None}]},
            }
        ],
        settings.DEPLOY_KEY_HOOKS: [
            {"id": 500003, "name": "MyHook", "targets": [{"id": None}]}
        ],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/hook_queue.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "hook_queue.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    queues_before = set(org._stores["queues"].keys())
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

    new_queue_ids = set(org._stores["queues"].keys()) - queues_before
    new_hook_ids = set(org._stores["hooks"].keys()) - hooks_before
    assert len(new_queue_ids) == 1
    assert len(new_hook_ids) == 1

    new_queue_id = new_queue_ids.pop()
    new_hook_id = new_hook_ids.pop()

    new_queue = org._stores["queues"][new_queue_id]
    new_hook = org._stores["hooks"][new_hook_id]

    # The new hook's queues must reference the new (target) queue, not the source queue
    new_queue_url = new_queue["url"]
    source_queue_url = f"{org.base_url}/queues/500004"

    assert new_queue_url in new_hook["queues"]
    assert source_queue_url not in new_hook["queues"]


@pytest.mark.asyncio
async def test_deploy_cross_org_creates_hook_with_token_owner(tmp_path: Path, monkeypatch):
    """Cross-org deploy creates a hook in target org with the target's token_owner URL.

    Exercises the is_same_org=False branch — token_owner is set based on
    target client base_url, and hook creation paths are used.
    """
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    source_org = build_simple_org(org_id=111, name="source-org", base_url="https://src.rossum.app/api/v1")
    target_org = build_empty_target_org(org_id=222, name="target-org", base_url="https://tgt.rossum.app/api/v1")
    # Pre-register a token-owning user in target
    target_user = [u for u in target_org._stores["users"].values()][0]

    await _write_cross_org_project_config(tmp_path, source_org, target_org)
    await _write_source_tree(tmp_path, source_org)
    await _write_hooks(tmp_path, source_org)

    # Also write target org file (required by orchestrator)
    await (tmp_path / "target" / "primary").mkdir(parents=True, exist_ok=True)
    await write_object_to_json(
        tmp_path / "target" / "organization.json",
        deepcopy(target_org._stores["organizations"][target_org.org_id]),
    )

    deploy_file_data = {
        settings.DEPLOY_KEY_SOURCE_DIR: "source/primary",
        settings.DEPLOY_KEY_TARGET_DIR: "target/primary",
        settings.DEPLOY_KEY_SOURCE_URL: source_org.base_url,
        settings.DEPLOY_KEY_TARGET_URL: target_org.base_url,
        settings.DEPLOY_KEY_TOKEN_OWNER: target_user["id"],
        settings.DEPLOY_KEY_DEPLOYED_ORG_ID: None,
        "patch_target_org": False,
        settings.DEPLOY_KEY_WORKSPACES: [],
        settings.DEPLOY_KEY_QUEUES: [],
        settings.DEPLOY_KEY_HOOKS: [
            {"id": 500003, "name": "MyHook", "targets": [{"id": None}]}
        ],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/cross_org.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "cross_org.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    source_client = VirtualRossumClient(source_org)
    target_client = VirtualRossumClient(target_org)

    target_hooks_before = set(target_org._stores["hooks"].keys())

    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=source_client,
        target_client=target_client,
        auto_apply_plan=True,
        prefer="",
    )

    target_hooks_after = set(target_org._stores["hooks"].keys())
    new_hook_ids = target_hooks_after - target_hooks_before
    assert len(new_hook_ids) == 1

    new_hook = target_org._stores["hooks"][new_hook_ids.pop()]
    assert new_hook["name"] == "MyHook"
    # Token owner URL must point at the TARGET org base_url
    assert new_hook["token_owner"] == f"{target_org.base_url}/users/{target_user['id']}"
    # And source org is unchanged
    assert 500003 in source_org._stores["hooks"]


@pytest.mark.asyncio
async def test_deploy_queue_with_schema_creates_both(tmp_path: Path, monkeypatch):
    """Deploy a new queue → its schema is also created in the same org and correctly linked."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    org = build_simple_org()
    # Pre-create a target workspace so the queue has somewhere to land
    target_ws = org.add_workspace(name="Target WS", id_=700001)

    await _write_project_config(tmp_path, org)
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
                "targets": [{"id": target_ws["id"]}],
            }
        ],
        settings.DEPLOY_KEY_QUEUES: [
            {
                "id": 500004,
                "name": "Q1",
                "ignore_deploy_warnings": True,
                "base_path": "source/primary/workspaces/WS1_[500001]",
                "targets": [{"id": None}],
                "schema": {"id": 500002, "targets": [{"id": None}]},
            }
        ],
        settings.DEPLOY_KEY_HOOKS: [],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/state.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "with_queue.yaml"
    import pathlib
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(deploy_file_data, sort_keys=False))

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    queues_before = set(org._stores["queues"].keys())
    schemas_before = set(org._stores["schemas"].keys())

    client = VirtualRossumClient(org)
    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=client,
        target_client=client,
        auto_apply_plan=True,
        prefer="",
    )

    queues_after = set(org._stores["queues"].keys())
    schemas_after = set(org._stores["schemas"].keys())

    new_queue_ids = queues_after - queues_before
    new_schema_ids = schemas_after - schemas_before

    assert len(new_queue_ids) == 1
    assert len(new_schema_ids) == 1

    new_queue = org._stores["queues"][new_queue_ids.pop()]
    new_schema = org._stores["schemas"][new_schema_ids.pop()]

    # New queue should reference the new schema (not the source schema)
    assert new_queue["schema"] == new_schema["url"]
    # And should reference the TARGET workspace
    assert new_queue["workspace"] == target_ws["url"]
