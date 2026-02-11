from __future__ import annotations

from pathlib import Path
import threading

import click

from deployment_manager.ai_agent.assistant import AgentOptions, run_agent_follow, run_agent_once
from deployment_manager.ai_agent.config import load_agent_config
from deployment_manager.ai_agent.tmux import ensure_tmux_split, stop_tmux_pane
from deployment_manager.utils.consts import display_error

@click.group(name="ai")
def ai_group():
    """AI agent helpers for PRD2."""

@ai_group.command(name="follow")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=Path("ai_agent.yaml"))
@click.option("--log-path", "log_path", type=click.Path(path_type=Path), default=None)
def ai_follow(config_path: Path, log_path: Path | None):
    options = AgentOptions(config_path=config_path)
    run_agent_follow(options, log_path=log_path)

@ai_group.command(name="once")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=Path("ai_agent.yaml"))
@click.option("--log-path", "log_path", type=click.Path(path_type=Path), default=None)
def ai_once(config_path: Path, log_path: Path | None):
    options = AgentOptions(config_path=config_path)
    output = run_agent_once(options, log_path=log_path)
    print(output)

async def start_ai_agent(config_path: Path, log_path: Path) -> tuple[str, bool] | None:
    try:
        config = load_agent_config(config_path)
    except Exception as exc:
        display_error(str(exc), exc)
        return None

    tmux_info = ensure_tmux_split(config, log_path=log_path, config_path=config_path)
    if tmux_info:
        return tmux_info

    thread = threading.Thread(
        target=run_agent_follow,
        kwargs={"options": AgentOptions(config_path=config_path), "log_path": log_path},
        daemon=True,
    )
    thread.start()
    return None

async def stop_ai_agent(tmux_info: tuple[str, bool] | None) -> None:
    if not tmux_info:
        return
    pane_id, created = tmux_info
    stop_tmux_pane(pane_id, created)
