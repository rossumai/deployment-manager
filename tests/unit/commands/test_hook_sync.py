"""Tests for commands/hook/sync/sync.py — `prd2 hook sync run`."""

from unittest.mock import MagicMock, patch

import pytest
import yaml

from deployment_manager.commands.hook.sync.sync import sync_hook


def _q_mock(answer):
    async def _ask():
        return answer

    m = MagicMock()
    m.ask_async = _ask
    return m


async def _write_sync_yaml(sync_file, entries):
    await sync_file.write_text(yaml.safe_dump(entries))


@pytest.mark.asyncio
class TestSyncHook:
    async def test_returns_early_when_sync_file_missing(self, tmp_path):
        # The function should not raise when the sync file does not exist
        await sync_hook(sync_file=tmp_path / "missing.yaml")

    async def test_skips_when_local_path_is_not_py(self, tmp_path):
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [{"local_path": "hooks/extension.txt", "remote_path": "https://github.com/u/r/blob/main/x.py"}],
        )
        # No git fetch is attempted because we bail out before that
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
        ) as fetch:
            await sync_hook(sync_file=sync_file)
        fetch.assert_not_called()

    async def test_skips_when_remote_path_not_py(self, tmp_path):
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [{"local_path": "hooks/x.py", "remote_path": "https://github.com/u/r/blob/main/x.txt"}],
        )
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
        ) as fetch:
            await sync_hook(sync_file=sync_file)
        fetch.assert_not_called()

    async def test_aborts_when_remote_fetch_returns_none(self, tmp_path):
        local = tmp_path / "x.py"
        await local.write_text("print('hello')\n")
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [
                {
                    "local_path": str(local),
                    "remote_path": "https://github.com/u/r/blob/main/x.py",
                }
            ],
        )
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
            return_value=None,
        ):
            await sync_hook(sync_file=sync_file)
        # Local file unchanged
        assert await local.read_text() == "print('hello')\n"

    async def test_aborts_when_local_path_does_not_exist(self, tmp_path):
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [
                {
                    "local_path": str(tmp_path / "missing_local.py"),
                    "remote_path": "https://github.com/u/r/blob/main/x.py",
                }
            ],
        )
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
            return_value=b"print('remote')\n",
        ):
            await sync_hook(sync_file=sync_file)
        assert not await (tmp_path / "missing_local.py").exists()

    async def test_skips_when_no_diff(self, tmp_path):
        local = tmp_path / "x.py"
        await local.write_text("print('hello')\n")
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [
                {
                    "local_path": str(local),
                    "remote_path": "https://github.com/u/r/blob/main/x.py",
                }
            ],
        )
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
            return_value=b"print('hello')\n",
        ), patch(
            "deployment_manager.commands.hook.sync.sync.questionary.confirm",
        ) as confirm:
            await sync_hook(sync_file=sync_file)
        # No prompt is shown when there's nothing to sync
        confirm.assert_not_called()

    async def test_overwrites_local_when_user_confirms(self, tmp_path):
        local = tmp_path / "x.py"
        await local.write_text("local_content\n")
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [
                {
                    "local_path": str(local),
                    "remote_path": "https://github.com/u/r/blob/main/x.py",
                }
            ],
        )
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
            return_value=b"remote_content\n",
        ), patch(
            "deployment_manager.commands.hook.sync.sync.questionary.confirm",
            return_value=_q_mock(True),
        ):
            await sync_hook(sync_file=sync_file)
        assert await local.read_text() == "remote_content\n"

    async def test_keeps_local_when_user_declines(self, tmp_path):
        local = tmp_path / "x.py"
        await local.write_text("local_content\n")
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [
                {
                    "local_path": str(local),
                    "remote_path": "https://github.com/u/r/blob/main/x.py",
                }
            ],
        )
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
            return_value=b"remote_content\n",
        ), patch(
            "deployment_manager.commands.hook.sync.sync.questionary.confirm",
            return_value=_q_mock(False),
        ):
            await sync_hook(sync_file=sync_file)
        assert await local.read_text() == "local_content\n"

    async def test_relative_remote_path_uses_gitlab_default(self, tmp_path):
        local = tmp_path / "x.py"
        await local.write_text("local\n")
        sync_file = tmp_path / "sync.yaml"
        await _write_sync_yaml(
            sync_file,
            [
                {
                    "local_path": str(local),
                    # No hostname → falls back to GITLAB_SERVERLESS_FUNCTIONS_URL prefix
                    "remote_path": "generic/stable/x.py",
                }
            ],
        )
        with patch(
            "deployment_manager.commands.hook.sync.sync.get_git_file_content_from_url_ssh",
            return_value=b"local\n",
        ) as fetch:
            await sync_hook(sync_file=sync_file)
        # The fetcher is called with a URL that includes the gitlab prefix
        called_url = fetch.call_args.args[0]
        assert called_url.endswith("/generic/stable/x.py")
        assert "gitlab" in called_url
