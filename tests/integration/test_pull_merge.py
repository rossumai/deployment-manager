"""Pull merges remote changes into locally modified files (3-way merge via git)."""

import copy
import json
import shutil
import subprocess
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import yaml
from anyio import Path
from rossum_api.domain_logic.resources import Resource

from deployment_manager.commands.download.directory import DownloadOrganizationDirectory
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.commands.download.helpers import replace_code_paths
from deployment_manager.commands.download.merge import _extract_code, _mark_conflict_in_git_index, is_unmerged
from deployment_manager.commands.upload.directory import UploadOrganizationDirectory
from deployment_manager.commands.upload.upload import upload_destinations
from deployment_manager.common.git import get_changed_file_paths
from deployment_manager.common.read_write import write_non_versioned_attribute
from deployment_manager.utils.consts import settings
from tests.integration.virtual_api import VirtualRossumClient, build_simple_org

HOOK_JSON = Path("source") / "primary" / "hooks" / "MyHook_[500003].json"
HOOK_PY = HOOK_JSON.with_suffix(".py")
QUEUE_DIR = Path("source") / "primary" / "workspaces" / "WS1_[500001]" / "queues" / "Q1_[500004]"
QUEUE_JSON = QUEUE_DIR / "queue.json"
SCHEMA_JSON = QUEUE_DIR / "schema.json"
FORMULA_PY = QUEUE_DIR / settings.FORMULA_DIR_NAME / "total.py"
REMOTE_MODIFIED_AT = "2099-01-01T00:00:00.000000Z"
LOCAL_FORMULA = "a = 10\nb = 2\nreturn a + b\n"
OLD_PROMPT = "Should the remote version overwrite the local one?"

pytestmark = pytest.mark.asyncio


def _git(cwd, *args) -> str:
    return subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True).stdout


@contextmanager
def _use_client(client):
    """Pull and push use the virtual client (instead of the credentials from the project)."""

    async def initialize(directory):
        directory.project_path = directory.project_path or Path(".")
        directory.client = client
        if isinstance(directory, DownloadOrganizationDirectory):
            changed_files = get_changed_file_paths(directory.org_path)
            directory.changed_files = replace_code_paths([path for _, path in changed_files])

    with (
        patch.object(DownloadOrganizationDirectory, "initialize", initialize),
        patch.object(UploadOrganizationDirectory, "initialize", initialize),
    ):
        yield


async def _pull(client, destination=Path("source") / "primary", **kwargs):
    with _use_client(client):
        await download_destinations(destinations=(destination,), project_path=Path("."), **kwargs)


async def _pull_and_commit(tmp_path, client):
    await _pull(client)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "pull")


async def _pull_answering(client, answer: str | None, module: str = "merge", **kwargs) -> MagicMock:
    """Pulls in a TTY with `answer` to the prompt of `module`, or in a non-TTY shell if `answer` is None."""
    prompt = MagicMock()
    prompt.ask_async = AsyncMock(return_value=answer)
    with (
        patch("sys.stdin.isatty", return_value=answer is not None),
        patch(f"deployment_manager.commands.download.{module}.questionary.text", return_value=prompt) as text_prompt,
    ):
        await _pull(client, **kwargs)
    return text_prompt


def _change_remote_hook(org, **changes):
    org._stores["hooks"][500003].update(modified_at=REMOTE_MODIFIED_AT, **changes)


def _change_remote_schema(org, edit):
    remote_schema = org._stores["schemas"][500002]
    edit(remote_schema)
    remote_schema["modified_at"] = REMOTE_MODIFIED_AT


async def _drop_base(tmp_path):
    shutil.rmtree(tmp_path / settings.PULL_BASE_DIRNAME, ignore_errors=True)


async def _edit_json(path: Path, edit):
    data = json.loads(await path.read_text())
    edit(data)
    await path.write_text(json.dumps(data, indent=2))


async def _read_json(path: Path) -> dict:
    return json.loads(await path.read_text())


async def _local_modified_at(path: Path) -> str:
    node = json.loads(await (Path("source") / "primary" / settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME).read_text())
    for part in path.parts[2:]:
        node = node[part]
    return node["modified_at"]


def _unmerged_paths(tmp_path) -> str:
    return _git(tmp_path, "ls-files", "-u")


def _stages(tmp_path, path) -> set[str]:
    return {line.split()[2] for line in _unmerged_paths(tmp_path).splitlines() if str(path) in line}


def _two_section_schema_content():
    def field(field_id, **extra):
        return {"category": "datapoint", "id": field_id, "label": field_id, "type": "string", **extra}

    return [
        {"category": "section", "id": "first", "label": "First", "children": [field("invoice_id"), field("order_id")]},
        {
            "category": "section",
            "id": "second",
            "label": "Second",
            "children": [field("vendor_name"), field("total", formula="a = 1\nb = 2\nreturn a + b\n")],
        },
    ]


def _set_label(schema: dict, field_id: str, label: str):
    for section in schema["content"]:
        for child in section["children"]:
            if child["id"] == field_id:
                child["label"] = label


def _remove_total_formula_field(schema: dict):
    schema["content"][1]["children"] = [c for c in schema["content"][1]["children"] if c["id"] != "total"]


@pytest_asyncio.fixture
async def project(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    org = build_simple_org()
    org._stores["schemas"][500002]["content"] = _two_section_schema_content()
    source = {"org_id": org.org_id, "api_base": org.base_url, "subdirectories": {"primary": {"regex": ""}}}
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump({"directories": {"source": source}}))
    await (tmp_path / "source" / "primary").mkdir(parents=True, exist_ok=True)
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    client = VirtualRossumClient(org)
    await _pull_and_commit(tmp_path, client)
    return tmp_path, org, client


@pytest.mark.parametrize(
    "local_edit, answer",
    [({"active": False}, "y"), ({"active": False}, None), ({"guide": "remote guide"}, "y")],
    ids=["accepted", "non-tty", "same-change"],
)
async def test_disjoint_edits_are_merged(project, local_edit, answer):
    """Local and remote change different hook fields -> both edits are kept (a clean merge needs no TTY).

    The same change on both sides has nothing to merge -> no prompt, only the timestamp is updated.
    """
    tmp_path, org, client = project
    await _edit_json(HOOK_JSON, lambda h: h.update(local_edit))
    local_before = await HOOK_JSON.read_text()
    _change_remote_hook(org, guide="remote guide")
    same_change = local_edit == {"guide": "remote guide"}

    text_prompt = await _pull_answering(client, answer)

    assert text_prompt.return_value.ask_async.await_count == (answer is not None and not same_change)
    assert await _read_json(HOOK_JSON) == {**json.loads(local_before), "guide": "remote guide"}
    if same_change:
        assert await HOOK_JSON.read_text() == local_before
    assert await _local_modified_at(HOOK_JSON) == REMOTE_MODIFIED_AT
    assert not _unmerged_paths(tmp_path)


@pytest.mark.parametrize(
    "local_edit, answer", [({"active": False}, "n"), ({"guide": "local guide"}, None)], ids=["declined", "non-tty"]
)
async def test_local_file_is_kept(project, local_edit, answer):
    """A declined merge, or a conflict in a non-TTY shell -> the local file and its timestamp stay unchanged."""
    tmp_path, org, client = project
    await _edit_json(HOOK_JSON, lambda h: h.update(local_edit))
    local_before = await HOOK_JSON.read_text()
    modified_at_before = await _local_modified_at(HOOK_JSON)
    _change_remote_hook(org, guide="remote guide")

    await _pull_answering(client, answer)

    assert await HOOK_JSON.read_text() == local_before
    assert await _local_modified_at(HOOK_JSON) == modified_at_before
    assert not _unmerged_paths(tmp_path)


async def test_same_field_edit_creates_git_conflict(project):
    """Both sides change the same field -> conflict markers and a real git conflict."""
    tmp_path, org, client = project
    await _edit_json(HOOK_JSON, lambda h: h.update(guide="local guide"))
    _change_remote_hook(org, guide="remote guide")

    with patch("deployment_manager.commands.download.directory.display_error") as display_error:
        await _pull_answering(client, "y")

    display_error.assert_not_called()
    text = await HOOK_JSON.read_text()
    assert "<<<<<<<" in text and "local guide" in text and "remote guide" in text
    assert _stages(tmp_path, HOOK_JSON) == {"1", "2", "3"}
    assert await _local_modified_at(HOOK_JSON) == REMOTE_MODIFIED_AT
    # The editor flow works: take the remote side and mark it resolved
    _git(tmp_path, "checkout", "--theirs", str(HOOK_JSON))
    assert (await _read_json(HOOK_JSON))["guide"] == "remote guide"


@pytest.mark.parametrize(
    "header, local_header, remote_return",
    [
        ("import json", "import json  # local", "return {'remote': 1}"),
        # Non-ASCII code is merged as UTF-8, whatever the locale encoding is
        ("# Příjemce", "# Příjemce – místní", "return {'název': 'ř'}"),
    ],
    ids=["ascii", "non-ascii"],
)
async def test_hook_code_edits_in_different_lines_are_merged(project, header, local_header, remote_return):
    """Local edits the .py file, remote edits another line of the code."""
    tmp_path, org, client = project
    remote_hook = org._stores["hooks"][500003]
    remote_hook["config"]["code"] = f"{header}\n\n\ndef rossum_hook_request_handler(payload):\n    return {{}}\n"
    remote_hook["modified_at"] = "2098-01-01T00:00:00.000000Z"
    await _pull_and_commit(tmp_path, client)

    await HOOK_PY.write_text((await HOOK_PY.read_text()).replace(header, local_header))
    remote_hook["config"]["code"] = remote_hook["config"]["code"].replace("return {}", remote_return)
    _change_remote_hook(org)

    await _pull_answering(client, "y")

    code = await HOOK_PY.read_text()
    assert local_header in code
    assert remote_return in code
    assert (await _read_json(HOOK_JSON))["config"]["code"] == code
    assert not _unmerged_paths(tmp_path)


async def test_schema_edits_are_merged_and_the_local_formula_is_kept(project):
    """Local and remote change labels of different datapoints, the local formula .py edit is kept."""
    tmp_path, org, client = project
    await FORMULA_PY.write_text(LOCAL_FORMULA)
    await _edit_json(SCHEMA_JSON, lambda s: _set_label(s, "invoice_id", "Invoice ID LOCAL"))
    _change_remote_schema(org, lambda s: _set_label(s, "vendor_name", "Vendor REMOTE"))

    await _pull_answering(client, "y")

    assert await FORMULA_PY.read_text() == LOCAL_FORMULA
    fields = {c["id"]: c for s in (await _read_json(SCHEMA_JSON))["content"] for c in s["children"]}
    assert fields["invoice_id"]["label"] == "Invoice ID LOCAL"
    assert fields["vendor_name"]["label"] == "Vendor REMOTE"
    assert fields["total"]["formula"] == LOCAL_FORMULA
    assert not _unmerged_paths(tmp_path)


async def _make_base_outdated(tmp_path):
    """The local file was written by something else than pull (old prd2, git checkout)."""
    await write_non_versioned_attribute(HOOK_JSON, {"modified_at": "2050-01-01T00:00:00.000000Z"}, "modified_at")


@pytest.mark.parametrize("break_base, answer", [(_drop_base, "y"), (_make_base_outdated, "n")], ids=["no", "outdated"])
async def test_without_usable_base_the_old_overwrite_prompt_is_used(project, break_base, answer):
    tmp_path, org, client = project
    await break_base(tmp_path)
    await _edit_json(HOOK_JSON, lambda h: h.update(active=False))
    _change_remote_hook(org, guide="remote guide")

    text_prompt = await _pull_answering(client, answer, module="helpers")

    assert [call.kwargs["message"] for call in text_prompt.call_args_list] == [OLD_PROMPT]
    hook = await _read_json(HOOK_JSON)
    assert hook["active"] is (answer == "y")
    if answer == "y":
        assert hook["guide"] == "remote guide"
    else:
        # A declined overwrite keeps the base of the local version
        base = json.loads(await (tmp_path / settings.PULL_BASE_DIRNAME / HOOK_JSON).read_text())
        assert base["modified_at"] != REMOTE_MODIFIED_AT


async def test_remote_only_change_overwrites_without_prompt(project):
    tmp_path, org, client = project
    _change_remote_hook(org, guide="remote guide")

    text_prompt = await _pull_answering(client, "n", module="helpers")

    text_prompt.assert_not_called()
    assert (await _read_json(HOOK_JSON))["guide"] == "remote guide"


async def _create_guide_conflict(org, client):
    await _edit_json(HOOK_JSON, lambda h: h.update(guide="local guide"))
    _change_remote_hook(org, guide="remote guide")
    await _pull_answering(client, "y")


async def _create_code_conflict(org, client):
    """Conflict only in the .py file: the hook JSON stays valid and keeps the local code."""
    await HOOK_PY.write_text((await HOOK_PY.read_text()).replace("return {}", "return {'local': 1}"))
    remote_config = org._stores["hooks"][500003]["config"]
    remote_config["code"] = remote_config["code"].replace("return {}", "return {'remote': 1}")
    _change_remote_hook(org)
    await _pull_answering(client, "y")
    assert "<<<<<<<" in await HOOK_PY.read_text()
    assert "<<<<<<<" not in await HOOK_JSON.read_text()


@pytest.mark.parametrize("create_conflict", [_create_code_conflict, _create_guide_conflict])
async def test_push_refuses_unresolved_conflicts(project, capsys, create_conflict):
    """A file with unresolved conflicts must never be pushed, and the user is told why."""
    tmp_path, org, client = project
    await create_conflict(org, client)
    remote_hook_before = copy.deepcopy(org._stores["hooks"][500003])

    with _use_client(client):
        await upload_destinations(destinations=(Path("source") / "primary",), project_path=Path("."))

    assert org._stores["hooks"][500003] == remote_hook_before
    assert "Resolve the merge" in capsys.readouterr().out


@pytest.mark.parametrize(
    "create_conflict, download_all",
    [(_create_code_conflict, False), (_create_code_conflict, True), (_create_guide_conflict, False)],
)
async def test_pull_skips_files_with_unresolved_conflicts(project, create_conflict, download_all):
    """The next pull (also `pull --all`) does not touch a conflicted file.

    The id of a file with conflict markers comes from the git index, so a 2nd subdir regex does not take the object.
    """
    tmp_path, org, client = project
    await create_conflict(org, client)
    conflicted_json, conflicted_code = await HOOK_JSON.read_text(), await HOOK_PY.read_text()
    config = yaml.safe_load(await (tmp_path / settings.CONFIG_FILENAME).read_text())
    config["directories"]["source"]["subdirectories"]["secondary"] = {"regex": "MyHook"}
    await (tmp_path / settings.CONFIG_FILENAME).write_text(yaml.safe_dump(config))
    await (tmp_path / "source" / "secondary").mkdir(parents=True, exist_ok=True)
    org._stores["hooks"][500003].update(guide="newer remote guide", modified_at="2099-02-01T00:00:00.000000Z")

    await _pull_answering(client, None, destination=Path("source"), download_all=download_all)

    assert await HOOK_JSON.read_text() == conflicted_json
    assert await HOOK_PY.read_text() == conflicted_code
    assert not await (Path("source") / "secondary" / "hooks" / HOOK_JSON.name).exists()
    assert _unmerged_paths(tmp_path)


async def _pull_commit_after_conflict(org, client):
    await _create_guide_conflict(org, client)
    await _pull(client, commit=True, commit_message="pull")


async def _push_commit_with_conflicting_auto_pull(org, client):
    async def pull_with_conflict(**kwargs):
        await _create_guide_conflict(org, client)

    with (
        _use_client(client),
        patch("deployment_manager.commands.upload.upload.download_destinations", pull_with_conflict),
    ):
        await upload_destinations(
            destinations=(Path("source") / "primary",), project_path=Path("."), commit=True, commit_message="push"
        )


@pytest.mark.parametrize("command", [_pull_commit_after_conflict, _push_commit_with_conflicting_auto_pull])
async def test_commit_is_skipped_with_unresolved_conflicts(project, command):
    """`pull -c` and `push -c` (its auto-pull can create conflicts) would `git add` the conflict markers."""
    tmp_path, org, client = project
    commits_before = _git(tmp_path, "rev-list", "--count", "HEAD")

    await command(org, client)

    assert _git(tmp_path, "rev-list", "--count", "HEAD") == commits_before
    assert _unmerged_paths(tmp_path)


async def test_unchanged_file_gets_a_base_when_the_api_returns_a_new_key(project):
    """The remote returns a new key with the same modified_at -> the local file is the base, merges still work."""
    tmp_path, org, client = project
    await _drop_base(tmp_path)
    remote_queue = org._stores["queues"][500004]
    remote_queue["enabled"] = True
    await _pull(client)
    assert await (tmp_path / settings.PULL_BASE_DIRNAME / QUEUE_JSON).exists()

    await _edit_json(QUEUE_JSON, lambda q: q.update(name="Q1 LOCAL"))
    remote_queue.update(session_timeout="02:00:00", modified_at=REMOTE_MODIFIED_AT)
    await _pull_answering(client, "y")

    queue = await _read_json(QUEUE_JSON)
    assert queue["name"] == "Q1 LOCAL"
    assert queue["session_timeout"] == "02:00:00"
    assert queue["enabled"] is True


@pytest.mark.parametrize(
    "formula_edited, answer",
    [(True, "y"), (True, None), (False, "y")],
    ids=["edited-tty", "edited-non-tty", "unchanged"],
)
async def test_remote_removal_of_a_formula(project, formula_edited, answer):
    """Remote deletes a formula field. A locally edited .py is a modify/delete conflict (local kept in non-TTY).

    An unchanged .py is deleted.
    """
    tmp_path, org, client = project
    if formula_edited:
        await FORMULA_PY.write_text(LOCAL_FORMULA)
    else:
        await _edit_json(SCHEMA_JSON, lambda s: _set_label(s, "invoice_id", "Invoice ID LOCAL"))
    schema_before = await SCHEMA_JSON.read_text()
    _change_remote_schema(org, _remove_total_formula_field)

    await _pull_answering(client, answer)

    if not formula_edited:
        assert not await FORMULA_PY.exists()
        assert not _unmerged_paths(tmp_path)
        return
    assert await FORMULA_PY.read_text() == LOCAL_FORMULA
    if answer:
        assert _stages(tmp_path, FORMULA_PY) == {"1", "2"}
    else:
        assert await SCHEMA_JSON.read_text() == schema_before
        assert not _unmerged_paths(tmp_path)


async def test_pull_all_updates_the_base_for_later_merges(project):
    """`pull --all` overwrites the files, so it also stores their new base: the next pull merges."""
    tmp_path, org, client = project
    org._stores["hooks"][500003].update(guide="remote guide", modified_at="2098-01-01T00:00:00.000000Z")
    await _pull(client, download_all=True)

    await _edit_json(HOOK_JSON, lambda h: h.update(active=False))
    _change_remote_hook(org, description="remote description")
    await _pull_answering(client, None)

    hook = await _read_json(HOOK_JSON)
    assert hook["active"] is False
    assert hook["guide"] == "remote guide"
    assert hook["description"] == "remote description"


async def test_empty_formulas_are_not_merged_as_code():
    """Like the saver, the merge has no formula files for empty formulas, so they stay in the schema JSON."""
    schema = {"content": _two_section_schema_content()}
    schema["content"][0]["children"][1]["formula"] = ""

    codes = _extract_code(schema, Resource.Schema)

    assert list(codes) == ["total"]
    assert schema["content"][0]["children"][1]["formula"] == ""


async def test_organization_json_uses_the_overwrite_prompt(project):
    """organization.json keeps modified_at in its JSON, a merge would keep the old one and make the base outdated."""
    tmp_path, org, client = project
    org_json = Path("source") / "organization.json"
    remote_org = org._stores["organizations"][org.org_id]
    remote_org["modified_at"] = "2098-01-01T00:00:00.000000Z"
    await _pull_and_commit(tmp_path, client)
    await _edit_json(org_json, lambda o: o.update(name="local name"))
    remote_org.update(metadata={"remote": 1}, modified_at=REMOTE_MODIFIED_AT)

    text_prompt = await _pull_answering(client, "y", destination=Path("source"), module="helpers")

    assert [call.kwargs["message"] for call in text_prompt.call_args_list] == [OLD_PROMPT]
    assert (await _read_json(org_json))["metadata"] == {"remote": 1}


async def test_object_without_modified_at_is_merged(project):
    """The base stores a missing modified_at as null, the local file has an empty one."""
    tmp_path, org, client = project
    org._stores["hooks"][500003].pop("modified_at")
    await (Path("source") / "primary" / settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME).unlink()
    await _pull(client)
    _git(tmp_path, "commit", "-q", "-a", "--allow-empty", "-m", "pull")
    await _edit_json(HOOK_JSON, lambda h: h.update(active=False))
    _change_remote_hook(org, guide="remote guide")

    text_prompt = await _pull_answering(client, "y")

    text_prompt.return_value.ask_async.assert_awaited_once()
    hook = await _read_json(HOOK_JSON)
    assert hook["active"] is False
    assert hook["guide"] == "remote guide"


async def test_runtime_change_merges_the_local_code(project):
    """Remote changes the runtime (python to nodejs) -> the local .py edits are merged into the new .js file."""
    tmp_path, org, client = project
    await HOOK_PY.write_text((await HOOK_PY.read_text()).replace("return {}", "return {'local': 1}"))
    remote_config = org._stores["hooks"][500003]["config"]
    remote_config.update(runtime="nodejs22.x", code="// remote\n" + remote_config["code"])
    _change_remote_hook(org)

    await _pull_answering(client, "y")

    code = await HOOK_PY.with_suffix(".js").read_text()
    assert "// remote" in code
    assert "return {'local': 1}" in code
    assert (await _read_json(HOOK_JSON))["config"]["code"] == code
    assert not _unmerged_paths(tmp_path)


async def test_unmerged_check_does_not_glob_the_file_name(project):
    """The [id] in file names is a glob character class: MyHook_[500003].json would match MyHook_5.json."""
    tmp_path, org, client = project
    other_path = HOOK_JSON.parent / "MyHook_5.json"
    await other_path.write_text("conflict")
    _mark_conflict_in_git_index(other_path, "base", "local", "remote")

    assert is_unmerged(other_path)
    assert not is_unmerged(HOOK_JSON)
