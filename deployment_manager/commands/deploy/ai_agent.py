from __future__ import annotations

from pathlib import Path

import click

from deployment_manager.ai_agent.assistant import AgentOptions, run_agent_follow, run_agent_once
from deployment_manager.ai_agent.runtime import start_ai_agent, stop_ai_agent


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
