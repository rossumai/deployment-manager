"""3-way merge (`git merge-file`) of remote changes into locally modified files during pull."""

import copy
import difflib
import json
import os
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING

import questionary
from anyio import Path
from rich import print as pprint
from rich.panel import Panel
from rossum_api.domain_logic.resources import Resource

if TYPE_CHECKING:
    from deployment_manager.commands.download.directory import DownloadOrganizationDirectory

from deployment_manager.commands.deploy.subcommands.run.deploy_objects.deploy_differ import DeployObjectDiffer
from deployment_manager.common.read_write import (
    create_custom_hook_code_path,
    create_formula_directory_path,
    find_fields_in_schema,
    sort_object_list_attributes,
    write_non_versioned_attribute,
    write_str,
)
from deployment_manager.utils.consts import display_warning, settings

CODE_PLACEHOLDER = "<prd2-code:{key}>"
HOOK_CODE_KEY = "config.code"
MARKER_LABELS = ["LOCAL", "LAST PULL", "REMOTE"]


def to_file_object(object_: dict, object_type: Resource) -> dict:
    """The object as it is stored in its JSON file (without the non-pulled and non-versioned attributes)."""
    data = copy.deepcopy(object_)
    for key in settings.NON_PULLED_KEYS_PER_OBJECT.get(object_type, []):
        data.pop(key, None)
    for key in settings.NON_VERSIONED_ATTRIBUTES:
        data.pop(key, None)
    return sort_object_list_attributes(data, object_type)


def get_base_path(parent_dir_reference: "DownloadOrganizationDirectory", path: Path | None = None) -> Path | None:
    """The last pulled version of `path`, or the directory of all of them if `path` is None."""
    # Unit tests pass a None or MagicMock parent
    project_path = getattr(parent_dir_reference, "project_path", None)
    if isinstance(project_path, Path):
        base_dir = project_path / settings.PULL_BASE_DIRNAME
        return base_dir / path.relative_to(project_path) if path else base_dir


async def save_pull_base(
    parent_dir_reference: "DownloadOrganizationDirectory",
    path: Path,
    object_: dict,
    object_type: Resource,
    only_if_missing: bool = False,
):
    base_path = get_base_path(parent_dir_reference, path)
    if not base_path or (only_if_missing and await base_path.exists()):
        return

    gitignore_path = get_base_path(parent_dir_reference) / ".gitignore"
    await base_path.parent.mkdir(parents=True, exist_ok=True)
    if not await gitignore_path.exists():
        await gitignore_path.write_text("*\n", encoding="utf-8")
    # modified_at tells if the base is still the version that the local file was pulled from
    base = json.dumps(
        {"modified_at": object_.get("modified_at"), "object": to_file_object(object_, object_type)}, indent=2
    )
    if await base_path.exists() and await base_path.read_text(encoding="utf-8") == base:
        return
    await base_path.write_text(base, encoding="utf-8")


def _git(*args, cwd: Path, input: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), input=input, capture_output=True, encoding="utf-8")


def is_unmerged(path: Path) -> bool:
    """Whether the object file or its code files have unresolved merge conflicts."""
    names = [path.name, path.with_suffix(".py").name, path.with_suffix(".js").name]
    if path.name == "schema.json":
        names.append(settings.FORMULA_DIR_NAME)
    return bool(_git("--literal-pathspecs", "ls-files", "-u", "--", *names, cwd=path.parent).stdout.strip())


def read_local_version_of_unmerged(path: Path) -> dict | None:
    """The local version (git index stage 2) of a file with merge conflict markers."""
    result = _git("show", f":2:./{path.name}", cwd=path.parent)
    return json.loads(result.stdout) if result.returncode == 0 else None


def _merge_text(local: str, base: str, remote: str) -> tuple[str, bool]:
    """Returns the merged text and whether it has conflicts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        files = [os.path.join(tmp_dir, name) for name in ("local", "base", "remote")]
        for file_path, text in zip(files, [local, base, remote]):
            with open(file_path, "w", encoding="utf-8") as wf:
                wf.write(text)
        labels = [arg for label in MARKER_LABELS for arg in ("-L", label)]
        result = _git("merge-file", "-p", *labels, *files, cwd=Path(tmp_dir))

    # The exit code is the number of conflicts (capped at 127), it is negative on errors
    if result.returncode > 127:
        raise RuntimeError(f"git merge-file failed: {result.stderr}")
    return result.stdout, result.returncode > 0


def _mark_conflict_in_git_index(path: Path, base: str, local: str, remote: str | None):
    """Writes the versions as git index stages, so git shows a conflict (a None remote is "deleted by them")."""
    top_level = Path(_git("rev-parse", "--show-toplevel", cwd=path.parent).stdout.strip())
    relative_path = os.path.relpath(os.path.realpath(str(path)), os.path.realpath(str(top_level)))

    index_info = f"0 {'0' * 40}\t{relative_path}\n"
    for stage, text in enumerate([base, local, remote], start=1):
        if text is None:
            continue
        sha = _git("hash-object", "-w", "--stdin", cwd=top_level, input=text).stdout.strip()
        index_info += f"100644 {sha} {stage}\t{relative_path}\n"
    _git("update-index", "--index-info", cwd=top_level, input=index_info).check_returncode()


def _extract_code(object_: dict, object_type: Resource) -> dict[str, str]:
    """Replaces code (which has its own local file) with placeholders and returns the code per key."""
    codes = {}
    if object_type == Resource.Hook and isinstance(object_.get("config"), dict) and "code" in object_["config"]:
        codes[HOOK_CODE_KEY] = object_["config"]["code"]
        object_["config"]["code"] = CODE_PLACEHOLDER.format(key=HOOK_CODE_KEY)
    elif object_type == Resource.Schema:
        # Same as find_formula_fields_in_schema (which the saver uses), but with the nodes to mask
        for node in find_fields_in_schema(object_.get("content", [])):
            if not node.get("formula"):
                continue
            codes[node["id"]] = node["formula"]
            node["formula"] = CODE_PLACEHOLDER.format(key=node["id"])
    return codes


def _code_file_path(path: Path, key: str, object_: dict) -> Path | None:
    if key == HOOK_CODE_KEY:
        return create_custom_hook_code_path(path, object_)
    return create_formula_directory_path(path) / f"{key}.py"


def _show_diff(path: Path, before: str, after: str):
    diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm=""))
    if diff:
        pprint(Panel(DeployObjectDiffer.parse_diff(diff), title=str(path), title_align="left"))


async def _ask_to_apply(parent_dir_reference: "DownloadOrganizationDirectory") -> bool:
    if parent_dir_reference.merge_answer_for_all is not None:
        return parent_dir_reference.merge_answer_for_all

    prompt = questionary.text(message="Apply the merge to the local files?", instruction="(y/n/yy/nn)")
    user_answer = (await prompt.ask_async() or "").casefold()
    # Use the same answer for all other merges
    if user_answer in ("yy", "nn"):
        parent_dir_reference.merge_answer_for_all = user_answer == "yy"
    return user_answer in ("y", "yy")


async def merge_remote_into_local(
    path: Path,
    remote_object: dict,
    object_type: Resource,
    parent_dir_reference: "DownloadOrganizationDirectory",
    local_modified_at: str,
) -> bool:
    """Returns False when there is no base to merge against, the caller then uses the overwrite prompt."""
    # Files outside a subdirectory (organization.json) keep modified_at in the JSON, so a merge would keep the old one
    if len(path.parents) < 3:
        return False
    base_path = get_base_path(parent_dir_reference, path)
    if not base_path or not await base_path.exists():
        return False
    base_data = json.loads(await base_path.read_text(encoding="utf-8"))
    # The local file was written by something else than pull (e.g., a git checkout), the base does not match it
    if (base_data.get("modified_at") or "") != local_modified_at:
        display_warning(f"The last pulled version of [green]{path}[/green] is outdated, it cannot be merged.")
        return False

    local_text = await path.read_text()
    local, base = json.loads(local_text), base_data["object"]
    remote = to_file_object(remote_object, object_type)
    masked = [copy.deepcopy(data) for data in (local, base, remote)]
    local_codes, base_codes, remote_codes = (_extract_code(data, object_type) for data in masked)

    local_json = json.dumps(masked[0], indent=2)
    merged_masked_text, json_conflict = _merge_text(*(json.dumps(data, indent=2) + "\n" for data in masked))
    merged_masked_text = merged_masked_text.removesuffix("\n")
    merged_text = merged_masked_text
    changed = merged_masked_text != local_json
    conflicts = [(path, json.dumps(base, indent=2), local_text, json.dumps(remote, indent=2))] if json_conflict else []
    code_writes: dict[Path, str | None] = {}  # None deletes the code file
    code_previews = []

    for key in {*local_codes, *remote_codes}:
        # Code is merged in its own file. The local code file (and not the JSON) has the local version of the code.
        # A runtime change (e.g., python to nodejs) writes the merged code to the code file of the remote runtime.
        local_code_path = _code_file_path(path, key, local)
        code_path = _code_file_path(path, key, remote) or local_code_path
        if local_code_path and await local_code_path.exists():
            local_codes[key] = await local_code_path.read_text()
        local_code, base_code, remote_code = local_codes.get(key), base_codes.get(key, ""), remote_codes.get(key)
        code, code_conflict = local_code if remote_code is None else remote_code, False
        if local_code is not None and remote_code is not None:
            code, code_conflict = _merge_text(local_code, base_code, remote_code)
        placeholder = json.dumps(CODE_PLACEHOLDER.format(key=key))
        # A conflicted code file keeps the local code in the JSON, the code file has the conflict markers
        merged_text = merged_text.replace(placeholder, json.dumps(local_code if code_conflict else code))
        if not code_path:
            continue

        # Code that was removed from the object (e.g., a formula field was deleted) does not get a code file
        new_code = code if placeholder in merged_masked_text else None
        changed |= (new_code or "") != local_codes.get(key, "")
        code_previews.append((code_path, local_codes.get(key, ""), new_code or ""))
        # Remote removed code that was changed locally, the local code file is kept as a modify/delete conflict
        if new_code is None and remote_code is None and key in base_codes and local_code != base_code:
            conflicts.append((code_path, base_code, local_code, None))
            continue
        code_writes[code_path] = new_code
        if code_conflict:
            conflicts.append((code_path, base_code, local_code, remote_code))

    if conflicts or changed:
        display_warning(
            f"File [green]{path}[/green] has changed both locally and remotely. "
            f"Merging the remote changes into the local file{' has conflicts' if conflicts else ''}:"
        )
        _show_diff(path, local_json, merged_masked_text)
        for preview in code_previews:
            _show_diff(*preview)
        if not sys.stdin.isatty():
            # A clean merge cannot lose changes, but nobody is here to resolve conflicts
            if conflicts:
                display_warning(f"Non-interactive shell — keeping the local version of [green]{path}[/green].")
                return True
        elif not await _ask_to_apply(parent_dir_reference):
            return True

    with open(path, "w", encoding="utf-8") as wf:
        wf.write(merged_text)
    for code_path, code in code_writes.items():
        if code is not None:
            await write_str(code_path, code)
        elif await code_path.exists():
            await code_path.unlink()
    await write_non_versioned_attribute(path, remote_object, "modified_at")
    await save_pull_base(parent_dir_reference, path, remote_object, object_type)

    for conflict in conflicts:
        _mark_conflict_in_git_index(*conflict)
    if conflicts:
        display_warning(
            "Merge conflicts in:\n"
            + "\n".join(f"  [green]{conflict[0]}[/green]" for conflict in conflicts)
            + f"\nResolve them and run `git add` on the files before the next {settings.UPLOAD_COMMAND_NAME}."
        )
    return True
