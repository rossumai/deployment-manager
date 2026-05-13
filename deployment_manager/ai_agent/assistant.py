"""Backwards-compatible shim.

All logic has been moved to:
- deployment_manager.ai_agent.runner (AgentRunner, AgentOptions)
- deployment_manager.ai_agent.plugins.deploy (DeployAgentPlugin)
- deployment_manager.ai_agent.llm (LLM provider abstraction)
- deployment_manager.ai_agent.skills.loader (SkillLoader)
- deployment_manager.ai_agent.logs.sources (LogSource, CommunicationLog)

This module re-exports the public API so existing call sites continue to work.
"""
from __future__ import annotations

from pathlib import Path

from deployment_manager.ai_agent.runner import AgentOptions, AgentRunner

__all__ = ["AgentOptions", "run_agent_once", "run_agent_follow"]


def run_agent_once(options: AgentOptions, log_path: Path | None = None) -> str:
    runner = AgentRunner.from_options(options)
    return runner.once(log_path=log_path)


def run_agent_follow(options: AgentOptions, log_path: Path | None = None) -> None:
    runner = AgentRunner.from_options(options)
    runner.follow(log_path=log_path)
