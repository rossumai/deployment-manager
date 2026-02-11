from __future__ import annotations

from pathlib import Path
import threading

import click

from deployment_manager.ai_agent.assistant import AgentOptions, run_agent_follow
from deployment_manager.ai_agent.config import load_agent_config
from deployment_manager.ai_agent.tmux import ensure_tmux_split, stop_tmux_pane
from deployment_manager.utils.consts import display_error

def resolve_ai_agent_settings(ctx: click.Context | None) -> tuple[bool, Path]:
    if not ctx or not ctx.obj:
        return False, Path("ai_agent.yaml")
    enabled = bool(ctx.obj.get("ai_agent"))
    config_path = ctx.obj.get("ai_config") or Path("ai_agent.yaml")
    return enabled, Path(config_path)

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

async def start_ai_agent_from_context(
    ctx: click.Context | None, log_path: Path | None
) -> tuple[str, bool] | None:
    enabled, config_path = resolve_ai_agent_settings(ctx)
    if not enabled or log_path is None:
        return None
    return await start_ai_agent(config_path=config_path, log_path=log_path)
