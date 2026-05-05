"""Tests for git.py - mocks subprocess.run to emulate `git status` output."""

from unittest.mock import MagicMock, patch

from deployment_manager.common.git import get_changed_file_paths
from deployment_manager.utils.consts import GIT_CHARACTERS


def _mock_git_status(output: str):
    """Return a side_effect for subprocess.run that returns the given output once."""

    call_count = [0]

    def side_effect(*args, **kwargs):
        result = MagicMock()
        # The first and third subprocess.run calls are `git config core.quotePath`
        # The second one is `git status`
        call_count[0] += 1
        if call_count[0] == 2:
            result.stdout = output
        else:
            result.stdout = ""
        return result

    return side_effect


class TestGetChangedFilePaths:
    def test_empty_output(self):
        with patch("subprocess.run", side_effect=_mock_git_status("")):
            assert get_changed_file_paths(".") == []

    def test_parses_modified_file(self):
        with patch("subprocess.run", side_effect=_mock_git_status(" M org/sub/workspaces/ws.json\n")):
            result = get_changed_file_paths(".")
            assert len(result) == 1
            op, path = result[0]
            assert op == GIT_CHARACTERS.UPDATED
            assert str(path).endswith("ws.json")

    def test_parses_untracked_file(self):
        with patch("subprocess.run", side_effect=_mock_git_status("?? org/sub/hooks/h.json\n")):
            result = get_changed_file_paths(".")
            assert result[0][0] == GIT_CHARACTERS.CREATED

    def test_ignores_non_json_py_js(self):
        output = " M org/README.md\n M config.yaml\n M hook.py\n"
        with patch("subprocess.run", side_effect=_mock_git_status(output)):
            result = get_changed_file_paths(".")
            # README.md and config.yaml filtered out; only hook.py remains
            assert len(result) == 1
            assert str(result[0][1]) == "hook.py"

    def test_indexed_only_filters_non_staged(self):
        """Indexed_only keeps only staged `M` entries."""
        # " M" (space then M) = unstaged modified
        # "M " (M then space) = staged modified
        # Note: the production code splits on space, so opcode "M" means staged
        output = "M  staged.json\n M unstaged.json\n"
        with patch("subprocess.run", side_effect=_mock_git_status(output)):
            result = get_changed_file_paths(".", indexed_only=True)
            # Only the staged one remains
            assert len(result) == 1
            assert str(result[0][1]) == "staged.json"

    def test_quoted_paths_are_unquoted(self):
        output = ' M "path with spaces.json"\n'
        with patch("subprocess.run", side_effect=_mock_git_status(output)):
            result = get_changed_file_paths(".")
            assert len(result) == 1
            assert str(result[0][1]) == "path with spaces.json"
