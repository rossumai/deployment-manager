from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from deployment_manager.ai_agent.config import AgentConfig, load_agent_config
from deployment_manager.ai_agent.llm.factory import create_llm_client
from deployment_manager.ai_agent.logs.sources import CommunicationLog, LogSource
from deployment_manager.ai_agent.plugins.base import CommandAgentPlugin
from deployment_manager.ai_agent.plugins.deploy import DeployAgentPlugin
from deployment_manager.ai_agent.skills.loader import SkillLoader
from deployment_manager.utils.consts import display_info, display_warning


@dataclass(frozen=True)
class AgentOptions:
    config_path: Path
    model: str | None = None


class AgentRunner:
    def __init__(
        self,
        config: AgentConfig,
        plugin: CommandAgentPlugin | None = None,
    ):
        self._config = config
        self._plugin = plugin or DeployAgentPlugin()
        self._llm = create_llm_client(config)
        self._skill_loader = SkillLoader(config)

    @classmethod
    def from_options(cls, options: AgentOptions, plugin: CommandAgentPlugin | None = None) -> AgentRunner:
        config = load_agent_config(options.config_path)
        return cls(config=config, plugin=plugin)

    def _load_instructions(self) -> str:
        return self._skill_loader.load_instructions()

    def _load_skills(self) -> str:
        return self._skill_loader.load_skills_text()

    async def _invoke_llm(self, prompt: str) -> str:
        return await self._llm.run(prompt)

    def once(self, log_path: Path | None = None) -> str:
        resolved_path = LogSource.resolve_log_path(self._config, log_path=log_path)
        if resolved_path is None:
            return "No log path available."

        log_source = LogSource(resolved_path, self._config.tail_lines)
        log_excerpt = log_source.read_tail()
        if not log_excerpt:
            return "No log data available yet."

        summary_json = self._plugin.build_summary(
            log_excerpt, is_jsonl=log_source.is_jsonl, log_path=resolved_path,
        )
        instructions = self._load_instructions()
        skills_text = self._load_skills()
        prompt = self._plugin.build_prompt(
            config=self._config,
            instructions=instructions,
            skills_text=skills_text,
            summary_json=summary_json,
        )

        import asyncio
        return asyncio.run(self._invoke_llm(prompt))

    def follow(self, log_path: Path | None = None) -> None:
        resolved_path = LogSource.resolve_log_path(self._config, log_path=log_path)
        if resolved_path is None:
            display_warning("No log path available for AI agent.")
            return

        base_skill_count = self._skill_loader.count_base_skills()
        extra_skill_count = self._skill_loader.count_extra_skills()
        display_info("AI agent active. Watching logs for prompts and changes.")
        display_info(f"Loaded {base_skill_count} base skill(s), {extra_skill_count} custom skill(s).")

        log_source = LogSource(resolved_path, self._config.tail_lines)
        comm_log = CommunicationLog(resolved_path)
        last_summary = ""
        offset = log_source.current_size()
        buffered_lines: list[str] = []
        last_prompt_present = False
        prompt_consumed = False
        prompt_markers = self._plugin.prompt_markers(self._config)
        instructions = self._load_instructions()
        skills_text = self._load_skills()

        import asyncio

        while True:
            if not log_source.exists():
                time.sleep(self._config.interval_seconds)
                continue

            current_size = log_source.current_size()
            if current_size < offset:
                offset = 0
                buffered_lines = []
            new_text, offset = log_source.read_since_offset(offset)
            if not new_text:
                time.sleep(self._config.interval_seconds)
                continue
            new_lines = new_text.splitlines()
            buffered_lines.extend(new_lines)
            if len(buffered_lines) > self._config.tail_lines:
                buffered_lines = buffered_lines[-self._config.tail_lines:]
            log_excerpt = "\n".join(buffered_lines).strip()
            if not log_excerpt:
                time.sleep(self._config.interval_seconds)
                continue

            prompt_present = DeployAgentPlugin._detect_prompt(log_excerpt, prompt_markers) if prompt_markers else False
            if not prompt_present:
                time.sleep(self._config.interval_seconds)
                continue

            if prompt_present and not last_prompt_present:
                display_info("User input detected. Summarizing context with AI agent.")

            summary_json = self._plugin.build_summary(
                log_excerpt, is_jsonl=log_source.is_jsonl, log_path=resolved_path,
            )

            if prompt_present and not prompt_consumed and self._config.fast_diff_summary:
                prompt = self._plugin.build_prompt(
                    config=self._config,
                    instructions=instructions,
                    skills_text=skills_text,
                    summary_json=summary_json,
                    log_excerpt=log_excerpt,
                )
                comm_log.append(prompt, "", pending=True)
                output = asyncio.run(self._invoke_llm(prompt))
                comm_log.append(prompt, output)
                if output:
                    print("\n--- DIFF SUMMARY ---\n" + output + "\n")
                    last_prompt_present = prompt_present
                    prompt_consumed = True
                    time.sleep(self._config.interval_seconds)
                    continue

            prompt = self._plugin.build_prompt(
                config=self._config,
                instructions=instructions,
                skills_text=skills_text,
                summary_json=summary_json,
            )
            comm_log.append(prompt, "", pending=True)
            output = asyncio.run(self._invoke_llm(prompt))
            comm_log.append(prompt, output)
            if output and output != last_summary:
                print("\n--- AI AGENT ---\n" + output + "\n")
                last_summary = output

            last_prompt_present = prompt_present
            if not prompt_present:
                prompt_consumed = False

            time.sleep(self._config.interval_seconds)
