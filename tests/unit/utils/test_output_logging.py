import re
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from deployment_manager.utils.output_logging import (
    ANSI_ESCAPE_RE,
    AUTO_LOG_FILE,
    TeeStream,
    ensure_log_dir,
    hoist_log_file_option,
    prune_log_files,
    resolve_log_file_path,
)
from deployment_manager.utils.consts import settings

COMMANDS = frozenset({"pull", "push", "deploy"})


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        # already in front, explicit value
        (["--log-file", "out.log", "pull"], ["--log-file=out.log", "pull"]),
        # after the subcommand, which click alone cannot parse
        (["pull", "--log-file", "out.log"], ["--log-file=out.log", "pull"]),
        # equals form is passed through untouched
        (["pull", "--log-file=out.log"], ["--log-file=out.log", "pull"]),
        # no value at all -> normalised to the auto sentinel
        (["pull", "--log-file"], [f"--log-file={AUTO_LOG_FILE}", "pull"]),
        # a bare option followed by a command name must not eat the command
        (["--log-file", "pull"], [f"--log-file={AUTO_LOG_FILE}", "pull"]),
        # a following option is not a value either
        (["pull", "--log-file", "--force"], [f"--log-file={AUTO_LOG_FILE}", "pull", "--force"]),
        # nested subcommands and their arguments keep their order
        (
            ["deploy", "run", "file.yaml", "--log-file", "out.log"],
            ["--log-file=out.log", "deploy", "run", "file.yaml"],
        ),
        # the opt-out flag is hoisted as well
        (["pull", "--no-log-file", "--force"], ["--no-log-file", "pull", "--force"]),
        # untouched when the option is absent
        (["pull", "--force"], ["pull", "--force"]),
    ],
)
def test_hoist_log_file_option(args, expected):
    assert hoist_log_file_option(args, COMMANDS) == expected


@pytest.mark.parametrize(
    ("args", "env", "expected_calls"),
    [
        (["hook", "--help"], {}, 1),
        (["hook", "--help", "--no-log-file"], {}, 0),
        (["hook", "--help"], {"PRD_NO_LOG_FILE": "1"}, 0),
    ],
)
def test_logging_is_on_by_default_and_can_be_suppressed(args, env, expected_calls):
    from deployment_manager.main import main

    with patch("deployment_manager.main.enable_output_logging") as enable, patch(
        "deployment_manager.main.resolve_log_file_path"
    ):
        result = CliRunner().invoke(main, args, env=env)
    assert result.exit_code == 0
    assert enable.call_count == expected_calls


def test_hoist_does_not_mutate_input():
    args = ["pull", "--log-file", "out.log"]
    hoist_log_file_option(args, COMMANDS)
    assert args == ["pull", "--log-file", "out.log"]


def test_resolve_log_file_path_keeps_explicit_path(tmp_path):
    explicit = tmp_path / "given.log"
    assert resolve_log_file_path(explicit) == explicit


def test_resolve_log_file_path_generates_timestamped_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    resolved = resolve_log_file_path(AUTO_LOG_FILE)
    assert resolved.parent.name == settings.DEFAULT_LOG_FILES_PARENT
    assert re.fullmatch(r"output-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.log", resolved.name)
    # the timestamp is generated per call, not baked in at import time
    assert resolved.name.startswith(f"output-{datetime.now().strftime('%Y-%m-%d')}")


def test_resolve_log_file_path_recycles_old_auto_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_dir = Path(tmp_path) / settings.DEFAULT_LOG_FILES_PARENT
    log_dir.mkdir()
    for day in range(1, settings.MAX_LOG_FILES + 6):
        (log_dir / f"output-2020-01-{day:02d}_00-00-00.log").touch()
    resolve_log_file_path(AUTO_LOG_FILE)
    remaining = sorted(p.name for p in log_dir.iterdir())
    # one slot is left for the new file, the oldest ones are gone
    assert len(remaining) == settings.MAX_LOG_FILES - 1
    assert remaining[0] == "output-2020-01-07_00-00-00.log"


def test_prune_log_files_ignores_other_files_and_missing_dir(tmp_path):
    tmp_path = Path(tmp_path)  # conftest hands out an async anyio Path
    prune_log_files(tmp_path / "missing", keep=1)
    (tmp_path / "custom.log").touch()
    (tmp_path / "output-2020-01-01_00-00-00.log").touch()
    (tmp_path / "output-2020-01-02_00-00-00.log").touch()
    prune_log_files(tmp_path, keep=1)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["custom.log", "output-2020-01-02_00-00-00.log"]


def test_ensure_log_dir_ignores_a_new_dir_and_leaves_an_existing_one_alone(tmp_path):
    tmp_path = Path(tmp_path)  # conftest hands out an async anyio Path
    new_dir = tmp_path / "nested" / "logs"
    ensure_log_dir(new_dir)
    assert (new_dir / ".gitignore").read_text() == "*\n"

    existing_dir = tmp_path / "existing"
    existing_dir.mkdir()
    ensure_log_dir(existing_dir)
    assert not (existing_dir / ".gitignore").exists()


class FakeStream:
    def __init__(self, tty: bool = True):
        self.written = ""
        self.tty = tty

    def write(self, data):
        self.written += data
        return len(data)

    def flush(self): ...

    def isatty(self):
        return self.tty

    def fileno(self):
        return 1


def test_tee_stream_strips_ansi_from_the_log_copy_only():
    terminal, log = FakeStream(), FakeStream()
    TeeStream(terminal, log).write("\x1b[1;32mgreen\x1b[0m\n")
    assert terminal.written == "\x1b[1;32mgreen\x1b[0m\n"
    assert log.written == "green\n"


def test_tee_stream_keeps_bare_newlines_but_drops_cursor_noise():
    terminal, log = FakeStream(), FakeStream()
    tee = TeeStream(terminal, log)
    tee.write("line")
    tee.write("\n")  # print() emits the newline as its own write
    tee.write("\r\x1b[2K")  # spinner repaint
    assert log.written == "line\n"


def test_tee_stream_looks_like_a_terminal_to_rich():
    terminal, log = FakeStream(tty=True), FakeStream()
    tee = TeeStream(terminal, log)
    assert tee.isatty() is True
    assert tee.fileno() == 1
    assert tee.writable() is True


def test_ansi_escape_re_matches_common_sequences():
    assert ANSI_ESCAPE_RE.sub("", "\x1b[1;31mx\x1b[0m\x1b[2K") == "x"
