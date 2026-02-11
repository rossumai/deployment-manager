from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from deployment_manager.utils.consts import display_warning

DEFAULT_AGENT_BASE = Path(__file__).resolve().parent / "assets"

@dataclass(frozen=True)
class AgentConfig:
    provider: str
    command: str
    prompt_prefix: str
    model_id: str
    agent_path: Path | None
    skills_path: Path
    log_path: Path
    asset_root: Path | None
    tail_lines: int = 200
    interval_seconds: float = 1.0
    enable_tmux: bool = True
    prompt_markers: list[str] | None = None
    fast_diff_summary: bool = True
    use_stdin: bool = True

def _coerce_path(value: Any, default: Path, base_dir: Path) -> Path:
    if not value:
        return default
    if isinstance(value, Path):
        return value if value.is_absolute() else base_dir / value
    path_value = Path(str(value))
    return path_value if path_value.is_absolute() else base_dir / path_value

def _normalize_path(path_value: Any) -> Path:
    if isinstance(path_value, Path):
        return path_value
    return Path(str(path_value))

def _find_upwards(start_path: Path, filename: str) -> Path | None:
    current = start_path
    while True:
        candidate = current / filename
        if candidate.exists():
            return candidate
        if current.parent == current:
            return None
        current = current.parent

def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True

def load_agent_config(config_path: Path) -> AgentConfig:
    config_path = _normalize_path(config_path)
    if not config_path.exists():
        if not config_path.is_absolute():
            default_config = DEFAULT_AGENT_BASE / config_path.name
            if default_config.exists():
                config_path = default_config
            package_root = Path(__file__).resolve().parents[2]
            if not config_path.exists():
                resolved = _find_upwards(package_root, config_path.name)
                if resolved:
                    config_path = resolved
            if not config_path.exists():
                resolved = _find_upwards(Path.cwd(), config_path.name)
                if resolved:
                    config_path = resolved
        if not config_path.exists():
            raise FileNotFoundError(f"AI agent config not found: {config_path}")

    data = yaml.safe_load(config_path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError("AI agent config must be a YAML mapping.")

    provider = str(data.get("provider") or "gemini")
    command = str(data.get("command") or "gemini")
    model_id = str(data.get("model_id") or "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    prompt_prefix = str(
        data.get("prompt_prefix")
        or "You are assisting with a PRD2 deployment. Summarize important events and prompt the user with next steps."
    )

    base_dir = config_path.parent
    asset_root = data.get("asset_root")
    asset_root = _coerce_path(asset_root, DEFAULT_AGENT_BASE, base_dir) if asset_root else DEFAULT_AGENT_BASE

    agent_path = data.get("agent_path")
    agent_path = _coerce_path(agent_path, base_dir / "agent.md", base_dir) if agent_path else None
    if agent_path and not agent_path.exists():
        agent_path = None
    skills_path = _coerce_path(data.get("skills_path"), base_dir / "skills", base_dir)
    log_path_value = data.get("log_path")
    if log_path_value is None and _is_within(config_path, DEFAULT_AGENT_BASE):
        log_path = Path.cwd() / "logs"
    else:
        log_path = _coerce_path(log_path_value, base_dir / "logs", base_dir)

    if agent_path is None:
        default_agent = asset_root / "agent.md"
        if default_agent.exists():
            agent_path = default_agent
    if not skills_path.exists():
        default_skills = asset_root / "skills"
        if default_skills.exists():
            skills_path = default_skills

    tail_lines = int(data.get("tail_lines") or 200)
    interval_seconds = float(data.get("interval_seconds") or 1.0)
    enable_tmux = bool(data.get("enable_tmux", True))
    prompt_markers = data.get("prompt_markers")
    if prompt_markers is None:
        prompt_markers = ["Do you wish to apply the plan?"]
    elif not isinstance(prompt_markers, list):
        prompt_markers = [str(prompt_markers)]
    prompt_markers = [str(marker) for marker in prompt_markers if marker]
    fast_diff_summary = bool(data.get("fast_diff_summary", True))
    use_stdin = bool(data.get("use_stdin", True))

    if not skills_path.exists():
        display_warning(f"AI agent skills path does not exist: {skills_path}")

    return AgentConfig(
        provider=provider,
        command=command,
        prompt_prefix=prompt_prefix,
        model_id=model_id,
        agent_path=agent_path,
        skills_path=skills_path,
        log_path=log_path,
        asset_root=asset_root,
        tail_lines=tail_lines,
        interval_seconds=interval_seconds,
        enable_tmux=enable_tmux,
        prompt_markers=prompt_markers,
        fast_diff_summary=fast_diff_summary,
        use_stdin=use_stdin,
    )
