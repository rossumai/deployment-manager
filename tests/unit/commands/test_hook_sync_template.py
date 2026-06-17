"""Tests for commands/hook/sync/template.py — `prd2 hook sync template/add`."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anyio import Path
from ruamel.yaml import YAML

from deployment_manager.commands.hook.sync.template import create_or_append_sync_template


def _q_mock(answer):
    async def _ask():
        return answer

    m = MagicMock()
    m.ask_async = _ask
    return m


@pytest.mark.asyncio
class TestCreateOrAppendSyncTemplate:
    async def test_creates_template_with_one_hook(self, tmp_path, monkeypatch):
        # cd into tmp_path so the saved file lands in a clean directory
        monkeypatch.chdir(tmp_path)

        local_py = tmp_path / "hooks" / "ext.py"
        await local_py.parent.mkdir(parents=True)
        await local_py.write_text("# hook code\n")

        text_answers = iter([str(local_py), "https://github.com/u/r/blob/main/x.py"])
        confirm_answers = iter([False])  # don't add another hook

        def text_factory(*a, **kw):
            return _q_mock(next(text_answers))

        def confirm_factory(*a, **kw):
            return _q_mock(next(confirm_answers))

        out_path = tmp_path / "out.yaml"
        with patch(
            "deployment_manager.commands.hook.sync.template.questionary.text",
            side_effect=text_factory,
        ), patch(
            "deployment_manager.commands.hook.sync.template.questionary.confirm",
            side_effect=confirm_factory,
        ), patch(
            "deployment_manager.commands.hook.sync.template.get_filepath_from_user",
            new=AsyncMock(return_value=out_path),
        ):
            await create_or_append_sync_template()

        assert await out_path.exists()
        data = YAML().load(await out_path.read_text())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["local_path"] == str(local_py)
        assert data[0]["remote_path"] == "https://github.com/u/r/blob/main/x.py"

    async def test_creates_template_with_multiple_hooks(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        a_py = tmp_path / "a.py"
        b_py = tmp_path / "b.py"
        await a_py.write_text("a")
        await b_py.write_text("b")

        text_answers = iter(
            [
                str(a_py),
                "https://github.com/u/r/blob/main/a.py",
                str(b_py),
                "https://github.com/u/r/blob/main/b.py",
            ]
        )
        # First confirm "add another?" → True; second → False (stop)
        confirm_answers = iter([True, False])

        out_path = tmp_path / "out.yaml"
        with patch(
            "deployment_manager.commands.hook.sync.template.questionary.text",
            side_effect=lambda *a, **kw: _q_mock(next(text_answers)),
        ), patch(
            "deployment_manager.commands.hook.sync.template.questionary.confirm",
            side_effect=lambda *a, **kw: _q_mock(next(confirm_answers)),
        ), patch(
            "deployment_manager.commands.hook.sync.template.get_filepath_from_user",
            new=AsyncMock(return_value=out_path),
        ):
            await create_or_append_sync_template()

        data = YAML().load(await out_path.read_text())
        assert len(data) == 2
        assert {entry["local_path"] for entry in data} == {str(a_py), str(b_py)}

    async def test_appends_to_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        existing_anyio = tmp_path / "existing.yaml"
        # Use plain stdlib pathlib for the YAML round-trip (ruamel needs sync file handles)
        from pathlib import Path as StdPath

        existing_std = StdPath(str(existing_anyio))
        with existing_std.open("w") as f:
            YAML().dump(
                [{"local_path": "first.py", "remote_path": "https://github.com/u/r/blob/main/first.py"}],
                f,
            )

        new_py = tmp_path / "new.py"
        await new_py.write_text("# new\n")

        text_answers = iter([str(new_py), "https://github.com/u/r/blob/main/new.py"])
        confirm_answers = iter([False])

        with patch(
            "deployment_manager.commands.hook.sync.template.questionary.text",
            side_effect=lambda *a, **kw: _q_mock(next(text_answers)),
        ), patch(
            "deployment_manager.commands.hook.sync.template.questionary.confirm",
            side_effect=lambda *a, **kw: _q_mock(next(confirm_answers)),
        ), patch(
            "deployment_manager.commands.hook.sync.template.get_filepath_from_user",
            new=AsyncMock(return_value=Path(existing_anyio)),
        ):
            await create_or_append_sync_template(old_hooks_file=Path(existing_anyio))

        with existing_std.open("r") as f:
            data = YAML().load(f)
        assert len(data) == 2
        assert data[0]["local_path"] == "first.py"
        assert data[1]["local_path"] == str(new_py)
