import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest
from anyio import Path

from deployment_manager.commands.download.helpers import (
    delete_empty_folders,
    delete_empty_formula_dir,
    replace_code_paths,
    should_write_object,
)
from deployment_manager.utils.consts import settings


class TestReplaceCodePaths:
    def test_hook_py_replaced_with_json(self):
        paths = [Path("org/sub/hooks/h1.py")]
        assert replace_code_paths(paths) == [Path("org/sub/hooks/h1.json")]

    def test_hook_js_replaced_with_json(self):
        paths = [Path("org/sub/hooks/h1.js")]
        assert replace_code_paths(paths) == [Path("org/sub/hooks/h1.json")]

    def test_formula_py_replaced_with_schema(self):
        formula_dir = settings.FORMULA_DIR_NAME
        paths = [Path(f"org/sub/workspaces/ws_[1]/queues/q_[5]/{formula_dir}/field_a.py")]
        replaced = replace_code_paths(paths)
        assert replaced == [Path("org/sub/workspaces/ws_[1]/queues/q_[5]/schema.json")]

    def test_unrelated_files_untouched(self):
        paths = [Path("org/sub/workspaces/ws_[1]/workspace.json")]
        assert replace_code_paths(paths) == paths

    def test_multiple_mixed(self):
        formula_dir = settings.FORMULA_DIR_NAME
        paths = [
            Path("org/sub/hooks/h1.py"),
            Path("org/sub/workspaces/ws_[1]/workspace.json"),
            Path(f"org/sub/workspaces/ws_[1]/queues/q_[5]/{formula_dir}/f.py"),
        ]
        replaced = replace_code_paths(paths)
        assert replaced[0] == Path("org/sub/hooks/h1.json")
        assert replaced[1] == Path("org/sub/workspaces/ws_[1]/workspace.json")
        assert replaced[2] == Path("org/sub/workspaces/ws_[1]/queues/q_[5]/schema.json")


@pytest.mark.asyncio
class TestDeleteEmptyFolders:
    async def test_removes_single_empty_folder(self, tmp_path):
        empty_dir = tmp_path / "empty_dir"
        await empty_dir.mkdir()
        deleted = await delete_empty_folders(tmp_path)
        assert not await empty_dir.exists()
        assert any(str(d).endswith("empty_dir") for d in deleted)

    async def test_keeps_folders_with_files(self, tmp_path):
        non_empty = tmp_path / "not_empty"
        await non_empty.mkdir()
        await (non_empty / "f.txt").write_text("x")
        await delete_empty_folders(tmp_path)
        assert await non_empty.exists()

    async def test_removes_nested_empty(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        await nested.mkdir(parents=True)
        # A single pass walks rglob and deletes what it finds empty.
        # The innermost empty directory is always removed immediately.
        await delete_empty_folders(tmp_path)
        assert not await (tmp_path / "a" / "b" / "c").exists()


@pytest.mark.asyncio
class TestDeleteEmptyFormulaDir:
    async def test_removes_queue_with_only_formula_dir(self, tmp_path):
        formula_dir = settings.FORMULA_DIR_NAME
        queue_path = tmp_path / "ws_[1]" / "queues" / "q_[5]" / formula_dir
        await queue_path.mkdir(parents=True)
        # queue dir has only formula/
        await delete_empty_formula_dir(tmp_path)
        assert not await (tmp_path / "ws_[1]" / "queues" / "q_[5]").exists()

    async def test_does_not_remove_if_other_files(self, tmp_path):
        formula_dir = settings.FORMULA_DIR_NAME
        queue_dir = tmp_path / "ws_[1]" / "queues" / "q_[5]"
        await (queue_dir / formula_dir).mkdir(parents=True)
        await (queue_dir / "queue.json").write_text("{}")
        await delete_empty_formula_dir(tmp_path)
        assert await queue_dir.exists()
        assert await (queue_dir / "queue.json").exists()


@pytest.mark.asyncio
class TestShouldWriteObject:
    async def test_non_tty_defaults_to_overwrite(self, tmp_path):
        """Non-TTY context: skip the questionary prompt, default to True (overwrite)."""
        sync_root = pathlib.Path(str(tmp_path))
        file_path_str = str(sync_root / "obj.json")
        with open(file_path_str, "w") as f:
            json.dump(
                {"url": "https://x/api/v1/queues/1", "modified_at": "2026-01-01"},
                f,
            )

        file_path = Path(file_path_str)
        remote = {"url": "https://x/api/v1/queues/1", "modified_at": "2026-02-02"}
        parent_dir = MagicMock()
        parent_dir.ignore_changed_file_warnings = False

        with patch("sys.stdin.isatty", return_value=False):
            result = await should_write_object(
                path=file_path,
                remote_object=remote,
                changed_files=[file_path],
                parent_dir_reference=parent_dir,
            )
        assert result is True

    async def test_non_tty_does_not_call_questionary(self, tmp_path):
        """In non-TTY, questionary.text must NOT be invoked (it would crash)."""
        sync_root = pathlib.Path(str(tmp_path))
        file_path_str = str(sync_root / "obj.json")
        with open(file_path_str, "w") as f:
            json.dump(
                {"url": "https://x/api/v1/queues/1", "modified_at": "2026-01-01"},
                f,
            )
        file_path = Path(file_path_str)
        remote = {"url": "https://x/api/v1/queues/1", "modified_at": "2026-02-02"}
        parent_dir = MagicMock()
        parent_dir.ignore_changed_file_warnings = False

        with patch("sys.stdin.isatty", return_value=False), patch(
            "deployment_manager.commands.download.helpers.questionary.text"
        ) as mock_q:
            await should_write_object(
                path=file_path,
                remote_object=remote,
                changed_files=[file_path],
                parent_dir_reference=parent_dir,
            )
        mock_q.assert_not_called()

    async def test_queue_hooks_reordered_only_is_not_treated_as_change(self, tmp_path):
        sync_root = pathlib.Path(str(tmp_path))
        file_path_str = str(sync_root / "queue.json")
        local_queue = {
            "url": "https://x/api/v1/queues/1",
            "modified_at": "2026-01-01",
            "hooks": [
                "https://x/api/v1/hooks/9",
                "https://x/api/v1/hooks/2",
            ],
        }
        with open(file_path_str, "w") as f:
            json.dump(local_queue, f)

        file_path = Path(file_path_str)
        remote = {
            "url": "https://x/api/v1/queues/1",
            "modified_at": "2026-01-01",
            "hooks": [
                "https://x/api/v1/hooks/2",
                "https://x/api/v1/hooks/9",
            ],
        }
        parent_dir = MagicMock()
        parent_dir.ignore_changed_file_warnings = False

        result = await should_write_object(
            path=file_path,
            remote_object=remote,
            changed_files=[],
            parent_dir_reference=parent_dir,
        )
        assert not result

    async def test_schema_queues_reordered_only_is_not_treated_as_change(self, tmp_path):
        sync_root = pathlib.Path(str(tmp_path))
        file_path_str = str(sync_root / "schema.json")
        local_schema = {
            "url": "https://x/api/v1/schemas/1",
            "modified_at": "2026-01-01",
            "queues": [
                "https://x/api/v1/queues/9",
                "https://x/api/v1/queues/2",
            ],
        }
        with open(file_path_str, "w") as f:
            json.dump(local_schema, f)

        file_path = Path(file_path_str)
        remote = {
            "url": "https://x/api/v1/schemas/1",
            "modified_at": "2026-01-01",
            "queues": [
                "https://x/api/v1/queues/2",
                "https://x/api/v1/queues/9",
            ],
        }
        parent_dir = MagicMock()
        parent_dir.ignore_changed_file_warnings = False

        result = await should_write_object(
            path=file_path,
            remote_object=remote,
            changed_files=[],
            parent_dir_reference=parent_dir,
        )
        assert not result
