import subprocess

from anyio import Path


def get_changed_file_paths(destination: str) -> list[tuple[str, str]]:
    git_destination_diff = subprocess.run(
        ["git", "status", destination, "-s"],
        capture_output=True,
        text=True,
    )
    changes_raw = git_destination_diff.stdout.split("\n")
    changes = []
    for change in changes_raw:
        change = change.strip()
        if not change:
            continue
        op, path = tuple(change.split(" ", maxsplit=1))
        path = Path(path.strip().strip('"'))
        changes.append((op, path))
    return changes
