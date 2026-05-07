import json
import os
import subprocess
from pathlib import Path

import pytest

from deployment_manager.common.git import (
    get_changed_file_paths,
    load_deleted_object_from_git,
)
from deployment_manager.utils.consts import GIT_CHARACTERS


# The root conftest overrides `tmp_path` to return `anyio.Path` (async I/O).
# These tests use synchronous pathlib, so restore the plain Path here.
@pytest.fixture()
def tmp_path(tmp_path):
    return Path(str(tmp_path))


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(tmp_path), check=True, capture_output=True)


class TestLoadDeletedObjectFromGit:
    def test_returns_committed_content(self, tmp_path):
        """When the file was committed and then deleted, returns the parsed JSON from HEAD."""
        _init_repo(tmp_path)
        file_path = tmp_path / "schema.json"
        obj = {"id": 42, "url": "https://x/api/v1/schemas/42", "name": "S"}
        file_path.write_text(json.dumps(obj))
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), check=True, capture_output=True)
        file_path.unlink()  # delete locally

        result = load_deleted_object_from_git(tmp_path, file_path)
        assert result == obj

    def test_prefers_staged_over_committed(self, tmp_path):
        """When a newer version is staged, return that (covers `git add`-then-`git rm` flow)."""
        _init_repo(tmp_path)
        file_path = tmp_path / "schema.json"
        file_path.write_text(json.dumps({"id": 1, "name": "old"}))
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), check=True, capture_output=True)

        # Stage an updated version, then remove the file.
        file_path.write_text(json.dumps({"id": 99, "name": "new"}))
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
        file_path.unlink()

        result = load_deleted_object_from_git(tmp_path, file_path)
        assert result == {"id": 99, "name": "new"}

    def test_returns_none_for_unknown_file(self, tmp_path):
        """A path that was never in git: returns None."""
        _init_repo(tmp_path)
        fake = tmp_path / "never_existed.json"
        assert load_deleted_object_from_git(tmp_path, fake) is None

    def test_returns_none_for_malformed_json(self, tmp_path):
        """Best-effort: non-JSON content returns None."""
        _init_repo(tmp_path)
        file_path = tmp_path / "broken.json"
        file_path.write_text("not json{{{")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), check=True, capture_output=True)
        file_path.unlink()
        assert load_deleted_object_from_git(tmp_path, file_path) is None

    def test_falls_back_to_head_after_git_rm(self, tmp_path):
        """`git rm` removes the index entry, so `:{path}` returns non-zero;
        the helper must fall back to HEAD to recover the content."""
        _init_repo(tmp_path)
        file_path = tmp_path / "schema.json"
        obj = {"id": 7, "url": "https://x/api/v1/schemas/7", "name": "S"}
        file_path.write_text(json.dumps(obj))
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), check=True, capture_output=True)

        # `git rm` removes both the index entry and the working-tree file.
        subprocess.run(["git", "rm", str(file_path)], cwd=str(tmp_path), check=True, capture_output=True)

        result = load_deleted_object_from_git(tmp_path, file_path)
        assert result == obj


def test_get_changed_file_paths_handles_RM_rename_with_modify(tmp_path):
    """`git mv` followed by editing the new file produces an `RM` line in
    `git status -s`. The parser must still split that into (D old, ?? new),
    not collapse it into a single un-handled op."""
    _init_repo(tmp_path)
    f = tmp_path / "hooks" / "Foo_[1].json"
    f.parent.mkdir(parents=True)
    f.write_text('{"id": 1, "name": "Foo"}')
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), check=True, capture_output=True)

    # git mv + content edit => `RM` op in git status.
    subprocess.run(
        ["git", "mv", "hooks/Foo_[1].json", "hooks/Bar_[1].json"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )
    (tmp_path / "hooks" / "Bar_[1].json").write_text('{"id": 1, "name": "Bar"}')

    prev_cwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        changes = get_changed_file_paths(".")
    finally:
        os.chdir(prev_cwd)

    ops = [(op, str(p)) for op, p in changes]
    assert (GIT_CHARACTERS.DELETED, "hooks/Foo_[1].json") in ops, ops
    assert (GIT_CHARACTERS.CREATED, "hooks/Bar_[1].json") in ops, ops
