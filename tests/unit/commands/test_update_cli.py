"""End-to-end tests for the `prd2 update` command.

We mock out:
- GitHub HTTP API (get_latest_version / get_specific_version)
- questionary.confirm (user prompts)
- subprocess.run (the actual pip install)
- importlib.metadata.version (the currently installed version)
"""

from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from deployment_manager.commands.update import update_application


def _mock_questionary_answer(answer: bool):
    """Return a MagicMock shaped like questionary.confirm(...).ask_async()."""

    async def _fake_ask_async():
        return answer

    m = MagicMock()
    m.ask_async = _fake_ask_async
    return m


class TestUpdateApplication:
    def test_latest_happy_path_installs(self):
        """current < selected, subprocess runs, display_info shown."""
        runner = CliRunner()

        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "2.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="1.0.0"),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            # The wheel URL must be the last argument
            call_args = mock_run.call_args[0][0]
            assert call_args[-1] == "https://whl"
            assert "pip" in call_args

    def test_specific_version_installs(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_specific_version", new=AsyncMock(return_value="https://whl2")),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="1.0.0"),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, ["v3.1.4"])
            assert result.exit_code == 0
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0][-1] == "https://whl2"

    def test_specific_version_not_found_aborts(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_specific_version", new=AsyncMock(return_value=None)),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, ["v9.9.9"])
            assert result.exit_code == 0
            mock_run.assert_not_called()

    def test_latest_when_no_url_errors_gracefully(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=(None, None))),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            mock_run.assert_not_called()

    def test_local_dev_version_prompts_and_declines(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "2.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="0.0.0"),
            patch("deployment_manager.commands.update.questionary.confirm", return_value=_mock_questionary_answer(False)),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            # User declined, so subprocess is NOT called
            mock_run.assert_not_called()

    def test_local_dev_version_prompts_and_accepts(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "2.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="0.0.0"),
            patch("deployment_manager.commands.update.questionary.confirm", return_value=_mock_questionary_answer(True)),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_reinstall_same_version_confirmed(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "1.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="1.0.0"),
            patch("deployment_manager.commands.update.questionary.confirm", return_value=_mock_questionary_answer(True)),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_reinstall_same_version_declined(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "1.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="1.0.0"),
            patch("deployment_manager.commands.update.questionary.confirm", return_value=_mock_questionary_answer(False)),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            mock_run.assert_not_called()

    def test_downgrade_prompt_accepted(self):
        """Installed version is newer than latest — prompt, then install."""
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "1.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="2.5.0"),
            patch("deployment_manager.commands.update.questionary.confirm", return_value=_mock_questionary_answer(True)),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_downgrade_prompt_declined(self):
        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "1.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="2.5.0"),
            patch("deployment_manager.commands.update.questionary.confirm", return_value=_mock_questionary_answer(False)),
            patch("deployment_manager.commands.update.subprocess.run") as mock_run,
        ):
            result = runner.invoke(update_application, [])
            assert result.exit_code == 0
            mock_run.assert_not_called()

    def test_subprocess_failure_does_not_raise(self):
        """If the pip install fails, the command handles it and does not crash."""
        import subprocess as subprocess_mod

        runner = CliRunner()
        with (
            patch("deployment_manager.commands.update.get_latest_version", new=AsyncMock(return_value=("https://whl", "2.0.0"))),
            patch("deployment_manager.commands.update.importlib.metadata.version", return_value="1.0.0"),
            patch(
                "deployment_manager.commands.update.subprocess.run",
                side_effect=subprocess_mod.CalledProcessError(1, "pip"),
            ),
        ):
            result = runner.invoke(update_application, [])
            # Command should complete (exit 0) even though pip failed.
            assert result.exit_code == 0
