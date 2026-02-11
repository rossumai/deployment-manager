from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from deployment_manager.ai_agent.config import AgentConfig
from deployment_manager.utils.consts import display_warning

_AI_PANE_MARK = "prd2_ai_agent"

def _run_tmux_command(args: list[str]) -> bool:
    try:
        subprocess.run(["tmux", *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True

def _run_tmux_command_capture(args: list[str]) -> str | None:
    try:
        result = subprocess.run(["tmux", *args], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    output = (result.stdout or "").strip()
    return output or None

def _is_inside_tmux() -> bool:
    return bool(os.environ.get("TMUX"))

def _find_marked_pane() -> str | None:
    panes_raw = _run_tmux_command_capture(["list-panes", "-F", "#{pane_id} #{pane_title}"])
    if not panes_raw:
        return None
    for line in panes_raw.splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        pane_id, title = parts
        if _AI_PANE_MARK in title:
            return pane_id
    return None

def _find_right_pane() -> str | None:
    panes_raw = _run_tmux_command_capture([
        "list-panes",
        "-F",
        "#{pane_id} #{pane_left} #{pane_width} #{pane_active}",
    ])
    if not panes_raw:
        return None
    panes = []
    for line in panes_raw.splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        pane_id, left, width, active = parts
        panes.append(
            {
                "pane_id": pane_id,
                "left": int(left),
                "width": int(width),
                "active": active == "1",
            }
        )
    if len(panes) < 2:
        return None
    panes.sort(key=lambda pane: pane["left"])
    for pane in reversed(panes):
        if not pane["active"]:
            return pane["pane_id"]
    return None

def ensure_tmux_split(agent_config: AgentConfig, log_path: Path, config_path: Path) -> tuple[str, bool] | None:
    if not agent_config.enable_tmux:
        return None
    if not _is_inside_tmux():
        display_warning("TMUX not detected. AI agent will run inline in the current terminal.")
        return None

    original_pane = _run_tmux_command_capture(["display-message", "-p", "#{pane_id}"])
    pane_id = _find_marked_pane() or _find_right_pane()
    created = False
    if pane_id is None:
        pane_id = _run_tmux_command_capture(["split-window", "-h", "-p", "40", "-P", "-F", "#{pane_id}"])
        created = True
    if not pane_id:
        display_warning("Failed to split tmux window for AI agent.")
        return None

    run_dir = log_path.parent
    agent_command = " ".join(
        [
            "PRD2_LOG_PREFIX=prd2_assistant",
            f"PRD2_LOG_PATH={shlex.quote(str(run_dir / 'assistant.log'))}",
            "prd2",
            "deploy",
            "ai",
            "follow",
            "--config",
            shlex.quote(str(config_path)),
            "--log-path",
            shlex.quote(str(log_path)),
        ]
    )
    send_ok = _run_tmux_command(["send-keys", "-t", pane_id, agent_command, "Enter"])
    if not send_ok:
        display_warning("Failed to start AI agent in tmux pane.")
        return None
    _run_tmux_command(["select-pane", "-t", pane_id, "-T", _AI_PANE_MARK])
    if original_pane:
        _run_tmux_command(["select-pane", "-t", original_pane])
    return pane_id, created

def stop_tmux_pane(pane_id: str, created: bool) -> None:
    if created:
        _run_tmux_command(["kill-pane", "-t", pane_id])
    else:
        _run_tmux_command(["send-keys", "-t", pane_id, "C-c"])
