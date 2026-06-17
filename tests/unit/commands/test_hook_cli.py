"""Smoke tests for commands/hook/hook.py — verifies Click wiring."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from deployment_manager.commands.hook.hook import hook


class TestHookCli:
    def test_help_lists_subcommands(self):
        runner = CliRunner()
        result = runner.invoke(hook, ["--help"])
        assert result.exit_code == 0
        assert "payload" in result.output
        assert "test" in result.output
        assert "sync" in result.output

    def test_sync_help_lists_subcommands(self):
        runner = CliRunner()
        result = runner.invoke(hook, ["sync", "--help"])
        assert result.exit_code == 0
        assert "template" in result.output
        assert "run" in result.output
        assert "add" in result.output

    def test_payload_calls_underlying_async(self, tmp_path):
        runner = CliRunner()
        # Click validates exists=True on the path; need a real file
        with runner.isolated_filesystem(temp_dir=str(tmp_path)) as cwd:
            from pathlib import Path as StdPath

            hook_path = StdPath(cwd) / "h.json"
            hook_path.write_text('{"id": 1, "name": "h", "events": []}')
            with patch(
                "deployment_manager.commands.hook.hook.generate_and_save_hook_payload",
                new=AsyncMock(),
            ) as fn:
                result = runner.invoke(hook, ["payload", str(hook_path)])
            assert result.exit_code == 0, result.output
            fn.assert_awaited_once()

    def test_test_calls_underlying_async(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=str(tmp_path)) as cwd:
            from pathlib import Path as StdPath

            hook_path = StdPath(cwd) / "h.json"
            hook_path.write_text('{"id": 1, "name": "h", "events": []}')
            with patch(
                "deployment_manager.commands.hook.hook.test_hook",
                new=AsyncMock(),
            ) as fn:
                result = runner.invoke(hook, ["test", str(hook_path)])
            assert result.exit_code == 0, result.output
            fn.assert_awaited_once()

    def test_sync_template_calls_underlying(self):
        runner = CliRunner()
        with patch(
            "deployment_manager.commands.hook.hook.create_or_append_sync_template",
            new=AsyncMock(),
        ) as fn:
            result = runner.invoke(hook, ["sync", "template"])
        assert result.exit_code == 0, result.output
        fn.assert_awaited_once()

    def test_sync_run_calls_underlying(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=str(tmp_path)) as cwd:
            from pathlib import Path as StdPath

            sync_file = StdPath(cwd) / "s.yaml"
            sync_file.write_text("[]")
            with patch(
                "deployment_manager.commands.hook.hook.sync_hook",
                new=AsyncMock(),
            ) as fn:
                result = runner.invoke(hook, ["sync", "run", str(sync_file)])
            assert result.exit_code == 0, result.output
            fn.assert_awaited_once()

    def test_sync_add_calls_underlying(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=str(tmp_path)) as cwd:
            from pathlib import Path as StdPath

            sync_file = StdPath(cwd) / "s.yaml"
            sync_file.write_text("[]")
            with patch(
                "deployment_manager.commands.hook.hook.create_or_append_sync_template",
                new=AsyncMock(),
            ) as fn:
                result = runner.invoke(hook, ["sync", "add", str(sync_file)])
            assert result.exit_code == 0, result.output
            fn.assert_awaited_once()
