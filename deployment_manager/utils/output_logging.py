import logging
import re
import sys
from collections.abc import Container
from datetime import datetime
from pathlib import Path

import click
from rich import print as pprint

from deployment_manager.utils.consts import settings

# prd2 output leaves the process through two independent channels: rich
# (`rich.print` and ad-hoc `Console()` instances) writes to stdout, the stdlib
# root logger writes tracebacks to stderr. Both are captured here by swapping
# sys.stdout/sys.stderr for a tee, so no call site has to change.

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])")

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# Value the --log-file option takes when passed without one.
AUTO_LOG_FILE = "auto"
AUTO_LOG_FILE_TEMPLATE = "output-%Y-%m-%d_%H-%M-%S.log"
AUTO_LOG_FILE_GLOB = "output-*.log"
LOG_FILE_OPTION = "--log-file"
NO_LOG_FILE_OPTION = "--no-log-file"


class TeeStream:
    """Writes to the original stream and appends an ANSI-free copy to a file."""

    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file

    def write(self, data: str) -> int:
        written = self.stream.write(data)
        plain = ANSI_ESCAPE_RE.sub("", data)
        # Spinners and progress bars emit chunks that are pure cursor movement;
        # keeping them would fill the log with blank lines. Line breaks arrive as
        # a chunk of their own (print() writes text and "\n" separately), so
        # whitespace is only droppable when it carries no newline.
        if plain.strip() or "\n" in plain:
            try:
                self.log_file.write(plain)
            except ValueError:
                pass
        return written

    def flush(self):
        self.stream.flush()
        try:
            self.log_file.flush()
        except ValueError:
            pass

    # rich decides on colour and terminal width from these, and Prompt.ask
    # needs the stream to still look interactive.
    def isatty(self) -> bool:
        return self.stream.isatty()

    def fileno(self) -> int:
        return self.stream.fileno()

    def writable(self) -> bool:
        return True

    def __getattr__(self, name):
        return getattr(self.stream, name)


def enable_output_logging(log_file_path: Path) -> Path:
    log_file_path = Path(log_file_path).expanduser()
    ensure_log_dir(log_file_path.parent)

    # Line buffered so the log stays readable while a long command is running.
    log_file = log_file_path.open("a", encoding="utf-8", buffering=1)
    command = " ".join(sys.argv[1:])
    log_file.write(f"\n===== prd2 {command} @ {datetime.now().isoformat(timespec='seconds')} =====\n")

    sys.stdout = TeeStream(sys.stdout, log_file)
    sys.stderr = TeeStream(sys.stderr, log_file)

    # basicConfig() already ran at import time, so its handler still holds the
    # pre-swap stderr. Repointing it keeps a single writer on the log file.
    root_logger = logging.getLogger()
    stream_handlers = [
        handler
        for handler in root_logger.handlers
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
    ]
    if stream_handlers:
        for handler in stream_handlers:
            handler.setStream(sys.stderr)
    else:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(handler)

    pprint(f"[dim]Logging output to {log_file_path}[/dim]")

    return log_file_path


def ensure_log_dir(log_dir: Path):
    """Creates log_dir; a folder prd2 creates only for logs keeps itself out of git.

    This also covers projects initialized before .prd_logs/ was added to the default .gitignore.
    An already existing folder is left alone, since it may hold files the user versions.
    """
    if log_dir.exists():
        return
    log_dir.mkdir(parents=True)
    (log_dir / ".gitignore").write_text("*\n", encoding="utf-8")


def resolve_log_file_path(log_file: Path) -> Path:
    if str(log_file) == AUTO_LOG_FILE:
        log_dir = Path(settings.DEFAULT_LOG_FILES_PARENT)
        # Leave room for the file about to be created.
        prune_log_files(log_dir, settings.MAX_LOG_FILES - 1)
        return log_dir / datetime.now().strftime(AUTO_LOG_FILE_TEMPLATE)
    return log_file


def prune_log_files(log_dir: Path, keep: int):
    """Deletes all but the `keep` newest auto-named log files in log_dir."""
    # The timestamp in the name sorts chronologically; explicitly named logs are never touched.
    log_files = sorted(log_dir.glob(AUTO_LOG_FILE_GLOB))
    for old_file in log_files[: max(len(log_files) - keep, 0)]:
        old_file.unlink(missing_ok=True)


def hoist_log_file_option(args: list[str], command_names: Container[str] = frozenset()) -> list[str]:
    """Moves --log-file and --no-log-file to the front so they are accepted after the subcommand too.

    A click.Group stops parsing at the first non-option token and hands the rest
    to the subcommand, which does not define this option. Pulling it out of the
    raw arguments first keeps `prd2 pull --log-file x.log` working.

    The option takes an optional value, so a bare --log-file followed by a
    subcommand name would otherwise have that name parsed as its value; such an
    occurrence is normalised to the explicit --log-file=auto form instead.
    """
    hoisted, rest = [], []
    args = list(args)
    while args:
        arg = args.pop(0)
        if arg == LOG_FILE_OPTION:
            takes_value = args and not args[0].startswith("-") and args[0] not in command_names
            value = args.pop(0) if takes_value else AUTO_LOG_FILE
            hoisted.append(f"{LOG_FILE_OPTION}={value}")
        elif arg == NO_LOG_FILE_OPTION or arg.startswith(f"{LOG_FILE_OPTION}="):
            hoisted.append(arg)
        else:
            rest.append(arg)
    return hoisted + rest


class LogFileGroup(click.Group):
    def parse_args(self, ctx, args):
        return super().parse_args(ctx, hoist_log_file_option(args, self.commands))
