import subprocess

from anyio import Path

from project_rossum_deploy.utils.consts import GIT_CHARACTERS


def get_changed_file_paths(
    destination: str, indexed_only=False
) -> list[tuple[str, str]]:
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
        op, path = tuple(change.split(" ", maxsplit=1))

        path = Path(path.strip().strip('"'))
        changes.append((op, path))
    return changes
