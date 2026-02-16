from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from deployment_manager.ai_agent.config import AgentConfig


class CommandAgentPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def prompt_markers(self, config: AgentConfig) -> list[str]:
        ...

    @abstractmethod
    def build_summary(self, log_excerpt: str, is_jsonl: bool = False, log_path: Path | None = None) -> str:
        ...

    @abstractmethod
    def build_prompt(
        self,
        config: AgentConfig,
        instructions: str,
        skills_text: str,
        summary_json: str,
        log_excerpt: str = "",
    ) -> str:
        ...
