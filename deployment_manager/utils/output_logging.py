import logging
import re
import sys
from datetime import datetime
from pathlib import Path

# prd2 output leaves the process through two independent channels: rich
# (`rich.print` and ad-hoc `Console()` instances) writes to stdout, the stdlib
# root logger writes tracebacks to stderr. Both are captured here by swapping
# sys.stdout/sys.stderr for a tee, so no call site has to change.

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])")

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


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
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

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

    return log_file_path
