import logging
import re
import sys
from typing import Any
from datetime import datetime
from pathlib import Path

from rich import reconfigure
from rich.logging import RichHandler

_LOG_HANDLE = None
_LAST_SECTION = None
_PROMPT_ACTIVE = 0
_ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_SECTION_OUTPUT = "PRD OUTPUT"
_SECTION_INPUT = "USER INPUT"


def _strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", text)


def _format_log_separator(title: str) -> str:
    return f"\n--- {title} ---\n"


def _write_log_section(title: str) -> None:
    global _LAST_SECTION
    if _LAST_SECTION == title:
        return
    if _LOG_HANDLE:
        _LOG_HANDLE.write(_format_log_separator(title))
    _LAST_SECTION = title


def _format_prompt_entry(message: str | None, answer: Any) -> str:
    if message:
        return f"PROMPT {message} -> {answer!r}\n"
    return f"PROMPT -> {answer!r}\n"


def _format_prompt_question(message: str | None) -> str:
    if message:
        return f"PROMPT {message}\n"
    return "PROMPT\n"


def _format_prompt_choices(choices: list | None) -> str:
    if not choices:
        return ""
    lines = ["CHOICES:"]
    for choice in choices:
        label = None
        if hasattr(choice, "title"):
            label = getattr(choice, "title", None)
        elif isinstance(choice, tuple) and choice:
            label = choice[0]
        if label is None:
            label = choice
        lines.append(f"- {label}")
    return "\n".join(lines) + "\n"


def _log_question_answer(question: object, answer: Any) -> None:
    message = getattr(question, "_prd2_question", None)
    _write_log_section(_SECTION_INPUT)
    if _LOG_HANDLE:
        _LOG_HANDLE.write(_format_prompt_entry(message, answer))
    _write_log_section(_SECTION_OUTPUT)


def _wrap_questionary_prompt(prompt_fn, prompt_name: str):
    if getattr(prompt_fn, "_prd2_wrapped", False):
        return prompt_fn

    def wrapper(message: str, *args, **kwargs):
        choices = None
        if prompt_name in {"select", "checkbox"}:
            if len(args) > 1:
                choices = args[1]
            else:
                choices = kwargs.get("choices")
        question = prompt_fn(message, *args, **kwargs)
        setattr(question, "_prd2_question", message)
        _write_log_section(_SECTION_OUTPUT)
        if _LOG_HANDLE:
            _LOG_HANDLE.write(_format_prompt_question(message))
            if choices is not None:
                _LOG_HANDLE.write(_format_prompt_choices(list(choices)))
        return question

    wrapper._prd2_wrapped = True
    return wrapper


def _enable_questionary_input_logging() -> None:
    try:
        import questionary
        from questionary.question import Question
    except Exception:
        return

    for name in ("text", "confirm", "select", "checkbox", "password"):
        prompt_fn = getattr(questionary, name, None)
        if prompt_fn:
            setattr(questionary, name, _wrap_questionary_prompt(prompt_fn, name))

    if not getattr(Question.unsafe_ask, "_prd2_wrapped", False):
        original_unsafe_ask = Question.unsafe_ask

        def unsafe_ask(self, *args, **kwargs):
            global _PROMPT_ACTIVE
            _PROMPT_ACTIVE += 1
            try:
                answer = original_unsafe_ask(self, *args, **kwargs)
            finally:
                _PROMPT_ACTIVE -= 1
            _log_question_answer(self, answer)
            return answer

        unsafe_ask._prd2_wrapped = True
        Question.unsafe_ask = unsafe_ask

    if not getattr(Question.unsafe_ask_async, "_prd2_wrapped", False):
        original_unsafe_ask_async = Question.unsafe_ask_async

        async def unsafe_ask_async(self, *args, **kwargs):
            global _PROMPT_ACTIVE
            _PROMPT_ACTIVE += 1
            try:
                answer = await original_unsafe_ask_async(self, *args, **kwargs)
            finally:
                _PROMPT_ACTIVE -= 1
            _log_question_answer(self, answer)
            return answer

        unsafe_ask_async._prd2_wrapped = True
        Question.unsafe_ask_async = unsafe_ask_async

def _resolve_log_path(log_path: str | Path | None, default_path: Path) -> Path:
    if log_path is None:
        return default_path
    if isinstance(log_path, Path):
        return log_path
    return Path(log_path)



class TeeIO:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            if stream is _LOG_HANDLE:
                if _PROMPT_ACTIVE <= 0:
                    stream.write(_strip_ansi(data))
            else:
                stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()

    def isatty(self) -> bool:
        return any(getattr(stream, "isatty", lambda: False)() for stream in self._streams)

    def fileno(self) -> int:
        for stream in self._streams:
            if getattr(stream, "fileno", None):
                return stream.fileno()
        raise OSError("No file descriptor available for TeeIO.")

    def writable(self) -> bool:
        return True

    @property
    def encoding(self) -> str:
        for stream in self._streams:
            if getattr(stream, "encoding", None):
                return stream.encoding
        return "utf-8"

    @property
    def errors(self) -> str | None:
        for stream in self._streams:
            if getattr(stream, "errors", None):
                return stream.errors
        return None

    def readable(self) -> bool:
        return False

    def seekable(self) -> bool:
        return False

    def close(self) -> None:
        for stream in self._streams:
            if getattr(stream, "close", None):
                stream.close()


def configure_logging(log_path: str | Path | None = None) -> None:
    global _LOG_HANDLE

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_log_path = Path("logs") / f"prd2_{timestamp}.log"
    log_file = _resolve_log_path(log_path, default_log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    _LOG_HANDLE = open(log_file, "w", encoding="utf-8", buffering=1)
    _LOG_HANDLE.write(f"--- Run started {datetime.now().isoformat(timespec='seconds')} ---\n")
    _write_log_section(_SECTION_OUTPUT)

    sys.stdout = TeeIO(sys.__stdout__, _LOG_HANDLE)
    sys.stderr = TeeIO(sys.__stderr__, _LOG_HANDLE)

    reconfigure(file=sys.stdout)

    _enable_questionary_input_logging()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
        force=True,
    )
    logging.getLogger("httpx").setLevel(logging.ERROR)
