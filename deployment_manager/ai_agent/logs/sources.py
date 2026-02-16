from __future__ import annotations

from pathlib import Path

from deployment_manager.ai_agent.config import AgentConfig
from deployment_manager.utils.logging import get_log_path


class LogSource:
    def __init__(self, path: Path, tail_lines: int = 200):
        self._path = path
        self._tail_lines = tail_lines

    @property
    def path(self) -> Path:
        return self._path

    @property
    def suffix(self) -> str:
        return self._path.suffix

    @property
    def is_jsonl(self) -> bool:
        return self._path.suffix == ".jsonl"

    def exists(self) -> bool:
        return self._path.exists()

    def current_size(self) -> int:
        return self._path.stat().st_size if self._path.exists() else 0

    def read_tail(self) -> str:
        try:
            lines = self._path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except FileNotFoundError:
            return ""
        return "\n".join(lines[-self._tail_lines:])

    def read_since_offset(self, offset: int) -> tuple[str, int]:
        try:
            with self._path.open("rb") as handle:
                handle.seek(offset)
                data = handle.read()
                if not data:
                    return "", offset
                text = data.decode("utf-8", errors="ignore")
                return text, offset + len(data)
        except FileNotFoundError:
            return "", offset

    @staticmethod
    def find_latest_log_file(log_dir: Path) -> Path | None:
        if not log_dir.exists():
            return None
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            return max(log_files, key=lambda path: path.stat().st_mtime)
        run_dirs = [path for path in log_dir.iterdir() if path.is_dir()]
        if not run_dirs:
            return None
        run_dirs.sort(key=lambda path: path.name)
        latest_run = run_dirs[-1]
        preferred_raw = latest_run / "user_raw.jsonl"
        if preferred_raw.exists():
            return preferred_raw
        preferred_raw = latest_run / "prd2_user_raw.jsonl"
        if preferred_raw.exists():
            return preferred_raw
        preferred = latest_run / "user.log"
        if preferred.exists():
            return preferred
        log_files = list(latest_run.glob("*.log"))
        if log_files:
            return max(log_files, key=lambda path: path.stat().st_mtime)
        return None

    @staticmethod
    def resolve_log_path(config: AgentConfig, log_path: Path | None = None) -> Path | None:
        if log_path is not None:
            if log_path.is_file() and log_path.suffix == ".log":
                raw_user = log_path.with_name("user_raw.jsonl")
                if raw_user.exists():
                    return raw_user
                raw_user = log_path.with_name("prd2_user_raw.jsonl")
                if raw_user.exists():
                    return raw_user
            return log_path
        active_log = get_log_path()
        if active_log is not None:
            return active_log
        if config.log_path.exists() and config.log_path.is_file():
            return config.log_path
        if config.log_path.exists() and config.log_path.is_dir():
            latest_log = LogSource.find_latest_log_file(config.log_path)
            if latest_log:
                return latest_log
        return None


class CommunicationLog:
    def __init__(self, log_path: Path):
        self._path = log_path.with_name("prd2_ai_communication.log")

    @property
    def path(self) -> Path:
        return self._path

    def append(self, prompt: str, response: str, pending: bool = False) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write("\n=== Gemini Request ===\n")
            handle.write(prompt)
            handle.write("\n=== Gemini Response ===\n")
            if pending:
                handle.write("<pending>\n")
            else:
                handle.write(response)
            handle.write("\n=== End ===\n")
