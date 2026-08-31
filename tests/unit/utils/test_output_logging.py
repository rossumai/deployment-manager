import re
from datetime import datetime

import pytest

from deployment_manager.utils.output_logging import (
    ANSI_ESCAPE_RE,
    AUTO_LOG_FILE,
    TeeStream,
    hoist_log_file_option,
    resolve_log_file_path,
)

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
        # untouched when the option is absent
        (["pull", "--force"], ["pull", "--force"]),
    ],
)
def test_hoist_log_file_option(args, expected):
    assert hoist_log_file_option(args, COMMANDS) == expected


def test_hoist_does_not_mutate_input():
    args = ["pull", "--log-file", "out.log"]
    hoist_log_file_option(args, COMMANDS)
    assert args == ["pull", "--log-file", "out.log"]


def test_resolve_log_file_path_keeps_explicit_path(tmp_path):
    explicit = tmp_path / "given.log"
    assert resolve_log_file_path(explicit) == explicit


def test_resolve_log_file_path_generates_timestamped_name():
    resolved = resolve_log_file_path(AUTO_LOG_FILE)
    assert re.fullmatch(r"output-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.log", resolved.name)
    # the timestamp is generated per call, not baked in at import time
    assert resolved.name.startswith(f"output-{datetime.now().strftime('%Y-%m-%d')}")


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
