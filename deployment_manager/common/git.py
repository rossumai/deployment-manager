import json
import pathlib
import subprocess

from anyio import Path

from deployment_manager.utils.consts import GIT_CHARACTERS


def get_changed_file_paths(destination: str, indexed_only=False) -> list[tuple[str, Path]]:
    # The -s flag is there to show a simplified list of changes
    # The -u flag is there to show each individual file (and not a subdir)
    # The change in git config is because of potential 'unusual' (non-ASCII) characters in paths
    subprocess.run(["git", "config", "core.quotePath", "false"])
    git_destination_diff = subprocess.run(
        ["git", "status", destination, "-s", "-u"],
        capture_output=True,
        text=True,
    )
    subprocess.run(["git", "config", "core.quotePath", "true"])

    changes_raw = git_destination_diff.stdout.split("\n")
    changes = []
    for change in changes_raw:
        if not change:
            continue

        if indexed_only:
            # "M" is staged modified, " M" is staged unmodified
            first_char, op_path = tuple(change.split(" ", maxsplit=1))
            if first_char != GIT_CHARACTERS.UPDATED:
                continue

        change = change.strip(" ")
        op, rest = tuple(change.split(" ", maxsplit=1))

        # `R old -> new` renames are surfaced as a (D old, ?? new) pair so the
        # rest of the pipeline only deals with two op codes. Git also emits
        # `RM` (renamed + modified in worktree) and `RD` (renamed + deleted in
        # worktree); treat the leading "R" the same way.
        if op.startswith("R") and " -> " in rest:
            old_str, new_str = rest.split(" -> ", maxsplit=1)
            old_path = Path(old_str.strip().strip('"'))
            new_path = Path(new_str.strip().strip('"'))
            if old_path.suffix in (".json", ".py", ".js"):
                changes.append((GIT_CHARACTERS.DELETED, old_path))
            if new_path.suffix in (".json", ".py", ".js"):
                changes.append((GIT_CHARACTERS.CREATED, new_path))
            continue

        path = Path(rest.strip().strip('"'))
        if path.suffix not in (".json", ".py", ".js"):
            continue

        changes.append((op, path))
    return changes


def load_deleted_object_from_git(project_path, file_path):
    """Best-effort recovery of a deleted JSON file's content from git.

    Tries the staged version first, then HEAD. Returns the parsed dict, or
    None if the file isn't in git, the git command fails, or the content
    isn't valid JSON.
    """
    proj_p = pathlib.Path(str(project_path))
    file_p = pathlib.Path(str(file_path))
    try:
        rel_path = str(file_p.relative_to(proj_p))
    except ValueError:
        rel_path = str(file_p)

    for git_ref in (f":{rel_path}", f"HEAD:{rel_path}"):
        try:
            result = subprocess.run(
                ["git", "show", git_ref],
                cwd=str(proj_p),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                continue
            return json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            continue
    return None
