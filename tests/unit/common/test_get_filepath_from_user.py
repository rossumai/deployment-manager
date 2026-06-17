from unittest.mock import MagicMock, patch

import pytest

from deployment_manager.common.get_filepath_from_user import get_filepath_from_user


def _mock_questionary_text(answer: str):
    """Build a MagicMock shaped like questionary.text(...).ask_async()."""

    async def _fake_ask_async():
        return answer

    m = MagicMock()
    m.ask_async = _fake_ask_async
    return m


def _mock_questionary_confirm(answer: bool):
    async def _fake_ask_async():
        return answer

    m = MagicMock()
    m.ask_async = _fake_ask_async
    return m


@pytest.mark.asyncio
class TestGetFilepathFromUser:
    async def test_returns_filepath_when_new(self, tmp_path):
        with patch(
            "deployment_manager.common.get_filepath_from_user.questionary.text",
            return_value=_mock_questionary_text("new-file.yaml"),
        ):
            result = await get_filepath_from_user(tmp_path)
            # Convert to str for comparison since anyio.Path and pathlib.Path differ
            assert str(result).endswith("new-file.yaml")

    async def test_overwrite_confirmed(self, tmp_path):
        existing = tmp_path / "existing.yaml"
        await existing.write_text("x")

        with patch(
            "deployment_manager.common.get_filepath_from_user.questionary.text",
            return_value=_mock_questionary_text("existing.yaml"),
        ), patch(
            "deployment_manager.common.get_filepath_from_user.questionary.confirm",
            return_value=_mock_questionary_confirm(True),
        ):
            result = await get_filepath_from_user(tmp_path)
            assert str(result).endswith("existing.yaml")
