"""End-to-end `deploy run --ld` (local deploy) against the in-memory virtual API.

These exercise the real `deploy_release_file` flow with `local_deploy=True`:
  - source object data is read solely from the local file tree
  - the source organization API is NEVER contacted (a tripwire source client
    records and rejects any call)
  - hook templates are matched against the TARGET org by id (no source lookup)
  - hook run_after references are remapped to the freshly-created target hooks

The credential/token short-circuit for --ld (skip_validation) is covered by the
unit tests in tests/unit/deploy/run/test_helpers.py; here we pass clients
explicitly and assert on the resulting target-org state.
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
from tests.integration.virtual_api import (
    VirtualRossumClient,
    VirtualRossumOrg,
    build_empty_target_org,
)


class _TripwireHttpClient:
    """Source ``_http_client`` whose only permitted use under --ld is reading ``base_url``.

    Every network method records the call and raises, so an accidental source-org
    call surfaces as a recorded call (asserted at the end of each test).
    """

    def __init__(self, base_url: str, calls: list):
        self._base_url = base_url
        self.calls = calls

    @property
    def base_url(self) -> str:
        return self._base_url

    async def fetch_one(self, *a, **k):
        self.calls.append("_http.fetch_one")
        raise AssertionError("source _http_client.fetch_one called under --ld")

    async def fetch_all(self, *a, **k):
        self.calls.append("_http.fetch_all")
        raise AssertionError("source _http_client.fetch_all called under --ld")
        yield  # noqa: makes this an async generator

    async def fetch_all_by_url(self, *a, **k):
        self.calls.append("_http.fetch_all_by_url")
        raise AssertionError("source _http_client.fetch_all_by_url called under --ld")
        yield  # noqa

    async def request_json(self, *a, **k):
        self.calls.append("_http.request_json")
        raise AssertionError("source _http_client.request_json called under --ld")

    async def create(self, *a, **k):
        self.calls.append("_http.create")
        raise AssertionError("source _http_client.create called under --ld")

    async def update(self, *a, **k):
        self.calls.append("_http.update")
        raise AssertionError("source _http_client.update called under --ld")


class _TripwireSourceClient(VirtualRossumClient):
    """A source client that fails the test if any source-org API call is made.

    Subclasses VirtualRossumClient so it still satisfies the orchestrator's
    ``isinstance(..., AsyncRossumAPIClient)`` validation.
    """

    def __init__(self, org: VirtualRossumOrg):
        super().__init__(org)
        self.calls: list = []
        self._http_client = _TripwireHttpClient(org.base_url, self.calls)

    async def retrieve_hook(self, *a, **k):
        self.calls.append("retrieve_hook")
        raise AssertionError("source.retrieve_hook called under --ld")

    async def request_json(self, *a, **k):
        self.calls.append("request_json")
        raise AssertionError("source.request_json called under --ld")

    async def retrieve_organization(self, *a, **k):
        self.calls.append("retrieve_organization")
        raise AssertionError("source.retrieve_organization called under --ld")

    async def list_organizations(self):
        self.calls.append("list_organizations")
        raise AssertionError("source.list_organizations called under --ld")
        yield  # noqa


def _patch_prompts(monkeypatch, auto_apply: bool = True):
    """Make all questionary prompts non-interactive (mirrors test_deploy.py)."""
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


async def _write_cross_org_project_config(
    project_root: Path, source_org: VirtualRossumOrg, target_org: VirtualRossumOrg
) -> None:
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


async def _write_org_file(project_root: Path, dir_name: str, org: VirtualRossumOrg) -> None:
    await (project_root / dir_name / "primary").mkdir(parents=True, exist_ok=True)
    await write_object_to_json(
        project_root / dir_name / "organization.json",
        deepcopy(org._stores["organizations"][org.org_id]),
    )


async def _write_hooks(project_root: Path, org: VirtualRossumOrg) -> None:
    for h in org._stores["hooks"].values():
        hook_file = project_root / "source" / "primary" / "hooks" / f"{h['name']}_[{h['id']}].json"
        await write_object_to_json(hook_file, deepcopy(h))
        code = h.get("config", {}).get("code")
        if code and h.get("extension_source") != "rossum_store":
            suffix = ".py" if "python" in h.get("config", {}).get("runtime", "") else ".js"
            await hook_file.with_suffix(suffix).write_text(code)


def _write_deploy_file(deploy_file_path: Path, data: dict) -> None:
    pathlib.Path(deploy_file_path.parent).mkdir(parents=True, exist_ok=True)
    pathlib.Path(deploy_file_path).write_text(yaml.safe_dump(data, sort_keys=False))


@pytest.mark.asyncio
async def test_local_deploy_creates_hooks_without_any_source_call(tmp_path: Path, monkeypatch):
    """A cross-org --ld deploy of two hooks (one with a hook_template, one with a
    run_after dependency) creates both in the target org, matches the template by id
    against the target, remaps run_after to the new target hook — and never calls the
    source organization API."""
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    # --- Source org exists only as local files; target org is empty ---
    source_org = VirtualRossumOrg(org_id=111, name="source-org", base_url="https://src.rossum.app/api/v1")
    source_org.add_user(username="src-user")
    # HookA references a hook_template (id 55). HookB runs after HookA.
    source_org.add_hook(
        name="HookA",
        id_=500003,
        hook_type="function",
        hook_template=f"{source_org.base_url}/hook_templates/55",
    )
    source_org.add_hook(name="HookB", id_=500005, hook_type="function", run_after=[500003])

    target_org = build_empty_target_org(org_id=222, name="target-org", base_url="https://tgt.rossum.app/api/v1")
    target_user = next(iter(target_org._stores["users"].values()))
    # The target org has the SAME template id 55 (store templates are global across orgs).
    # Mirror the real list endpoint, which returns name + url but NOT a top-level "id" —
    # the id must be derived from the url for the --ld match to succeed.
    target_org._stores["hook_templates"][55] = {
        "name": "Master Data Hub",
        "url": f"{target_org.base_url}/hook_templates/55",
    }

    await _write_cross_org_project_config(tmp_path, source_org, target_org)
    await _write_org_file(tmp_path, "source", source_org)
    await _write_org_file(tmp_path, "target", target_org)
    await _write_hooks(tmp_path, source_org)

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
            {"id": 500003, "name": "HookA", "targets": [{"id": None}]},
            {"id": 500005, "name": "HookB", "targets": [{"id": None}]},
        ],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/local.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "local.yaml"
    _write_deploy_file(deploy_file_path, deploy_file_data)

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    source_client = _TripwireSourceClient(source_org)
    target_client = VirtualRossumClient(target_org)

    target_hooks_before = set(target_org._stores["hooks"].keys())

    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=source_client,
        target_client=target_client,
        auto_apply_plan=True,
        prefer="",
        local_deploy=True,
    )

    # 1) The source organization API was never touched.
    assert source_client.calls == [], f"source org was contacted under --ld: {source_client.calls}"

    # 2) Two new hooks were created in the TARGET org.
    new_hook_ids = set(target_org._stores["hooks"].keys()) - target_hooks_before
    assert len(new_hook_ids) == 2
    new_hooks = {target_org._stores["hooks"][hid]["name"]: target_org._stores["hooks"][hid] for hid in new_hook_ids}
    assert set(new_hooks) == {"HookA", "HookB"}

    # 3) HookA still carries a hook_template reference to template id 55. Under --ld the
    #    template is matched against the TARGET org by id with no source lookup (the source
    #    tripwire above proves no `request_json` to the source org was made). The exact final
    #    URL host is governed by pre-existing create-vs-update mechanics and is not asserted.
    assert new_hooks["HookA"]["hook_template"].endswith("/hook_templates/55")

    # 4) HookB.run_after points at the newly-created TARGET HookA (remapped, not the source hook).
    target_hook_a_url = new_hooks["HookA"]["url"]
    assert new_hooks["HookB"]["run_after"] == [target_hook_a_url]
    assert f"{source_org.base_url}/hooks/500003" not in new_hooks["HookB"]["run_after"]

    # 5) The source org store is unchanged (read-only locally).
    assert set(source_org._stores["hooks"].keys()) == {500003, 500005}


@pytest.mark.asyncio
async def test_local_deploy_resolves_missing_run_after_predecessor_from_local_files(tmp_path: Path, monkeypatch):
    """A→B→C run_after chain where B is NOT part of the deploy.

    HookA.run_after = [B]; B is not deployed (not in the deploy file) but exists as a local
    file with B.run_after = [C]; C IS deployed. Under --ld the orchestrator must resolve the
    missing predecessor B by reading the LOCAL hook file (never calling source.retrieve_hook)
    and link HookA directly to the created target HookC.
    """
    monkeypatch.chdir(tmp_path)
    _patch_prompts(monkeypatch, auto_apply=True)

    source_org = VirtualRossumOrg(org_id=111, name="source-org", base_url="https://src.rossum.app/api/v1")
    source_org.add_user(username="src-user")
    source_org.add_hook(name="HookC", id_=500010, hook_type="function")
    source_org.add_hook(name="HookB", id_=500011, hook_type="function", run_after=[500010])  # NOT deployed
    source_org.add_hook(name="HookA", id_=500012, hook_type="function", run_after=[500011])

    target_org = build_empty_target_org(org_id=222, name="target-org", base_url="https://tgt.rossum.app/api/v1")
    target_user = next(iter(target_org._stores["users"].values()))

    await _write_cross_org_project_config(tmp_path, source_org, target_org)
    await _write_org_file(tmp_path, "source", source_org)
    await _write_org_file(tmp_path, "target", target_org)
    await _write_hooks(tmp_path, source_org)  # writes all three, including the non-deployed HookB

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
        # Only C and A are deployed; B is intentionally absent.
        settings.DEPLOY_KEY_HOOKS: [
            {"id": 500010, "name": "HookC", "targets": [{"id": None}]},
            {"id": 500012, "name": "HookA", "targets": [{"id": None}]},
        ],
        settings.DEPLOY_KEY_STATE_PATH: "deploy_states/local_chain.json",
        "unselected_hooks": [],
    }
    deploy_file_path = tmp_path / "deploy_files" / "local_chain.yaml"
    _write_deploy_file(deploy_file_path, deploy_file_data)

    async def _noop_download(*args, **kwargs):
        return

    monkeypatch.setattr(
        "deployment_manager.commands.deploy.subcommands.run.run.download_destinations",
        _noop_download,
    )

    source_client = _TripwireSourceClient(source_org)
    target_client = VirtualRossumClient(target_org)

    target_hooks_before = set(target_org._stores["hooks"].keys())

    await deploy_release_file(
        deploy_file_path=deploy_file_path,
        project_path=Path("."),
        source_client=source_client,
        target_client=target_client,
        auto_apply_plan=True,
        prefer="",
        local_deploy=True,
    )

    # No source-org call — in particular the missing predecessor was read from local files,
    # not via source.retrieve_hook (which is what the non-local path would have used).
    assert source_client.calls == [], f"source org was contacted under --ld: {source_client.calls}"

    new_hook_ids = set(target_org._stores["hooks"].keys()) - target_hooks_before
    new_hooks = {target_org._stores["hooks"][hid]["name"]: target_org._stores["hooks"][hid] for hid in new_hook_ids}
    # Only C and A were created (B was not part of the deploy).
    assert set(new_hooks) == {"HookC", "HookA"}

    # HookA is linked directly to the created target HookC (B collapsed out of the chain).
    assert new_hooks["HookA"]["run_after"] == [new_hooks["HookC"]["url"]]
