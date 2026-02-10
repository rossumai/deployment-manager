from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time

import asyncio

from deployment_manager.ai_agent.config import AgentConfig, load_agent_config
from deployment_manager.commands.document.llm_helper import LLMHelper
from deployment_manager.utils.consts import display_info, display_warning
from deployment_manager.utils.logging import get_log_path

@dataclass(frozen=True)
class AgentOptions:
    config_path: Path
    model: str | None = None

def _read_tail_lines(path: Path, count: int) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except FileNotFoundError:
        return ""
    return "\n".join(lines[-count:])

def _read_since_offset(path: Path, offset: int) -> tuple[str, int]:
    try:
        with path.open("rb") as handle:
            handle.seek(offset)
            data = handle.read()
            if not data:
                return "", offset
            text = data.decode("utf-8", errors="ignore")
            return text, offset + len(data)
    except FileNotFoundError:
        return "", offset

def _detect_prompt(log_excerpt: str, prompt_markers: list[str]) -> bool:
    return any(marker in log_excerpt for marker in prompt_markers)

def _read_agent_instructions(config: AgentConfig) -> str:
    if not config.agent_path:
        return ""
    try:
        return config.agent_path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return ""

def _read_skills(config: AgentConfig) -> str:
    if not config.skills_path.exists():
        return ""
    skill_files = sorted(config.skills_path.glob("*.md"))
    if not skill_files:
        return ""
    content = []
    for skill_file in skill_files:
        try:
            skill_text = skill_file.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if skill_text:
            content.append(f"\n# Skill: {skill_file.name}\n{skill_text}")
    return "\n".join(content).strip()

def _build_prompt(config: AgentConfig, log_excerpt: str) -> str:
    agent_instructions = _read_agent_instructions(config)
    skills_text = _read_skills(config)
    base_prompt = config.prompt_prefix
    if agent_instructions:
        base_prompt = f"{base_prompt}\n\nAgent instructions:\n{agent_instructions}"
    if skills_text:
        base_prompt = f"{base_prompt}\n\nSkills:\n{skills_text}"
    diff_instructions = (
        "You must count additions and deletions from diff-like lines. "
        "Count lines whose first non-border character is '+' as additions and '-' as deletions, "
        "ignoring '+++' and '---' headers. "
        "Reply only with: Additions: <n> Deletions: <n>."
    )
    return f"{base_prompt}\n\n{diff_instructions}\n\nLog excerpt:\n{log_excerpt}\n"

def _run_gemini(command: str, prompt: str, use_stdin: bool) -> str:
    if "\x00" in prompt:
        prompt = prompt.replace("\x00", "")
    try:
        if use_stdin:
            result = subprocess.run(
                [command, "-p", "-"],
                input=prompt,
                check=False,
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                [command, "-p", prompt],
                check=False,
                capture_output=True,
                text=True,
            )
    except FileNotFoundError:
        return f"Gemini command not found: {command}"

    output = (result.stdout or "").strip()
    if not output:
        output = (result.stderr or "").strip()
    return output

def _run_llm(prompt: str, model_id: str) -> str:
    helper = LLMHelper(model_id=model_id)
    if not helper.validate_credentials():
        return "Missing or invalid AWS credentials for Bedrock."
    response = asyncio.run(helper.run(prompt))
    if response and response.text:
        return response.text
    return ""

def _resolve_log_path(config: AgentConfig, log_path: Path | None = None) -> Path | None:
    if log_path is not None:
        return log_path
    active_log = get_log_path()
    if active_log is not None:
        return active_log
    if config.log_path.exists() and config.log_path.is_file():
        return config.log_path
    if config.log_path.exists() and config.log_path.is_dir():
        log_files = sorted(config.log_path.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
        if log_files:
            return log_files[0]
    return None

def _resolve_comm_log_path(log_path: Path) -> Path:
    name = log_path.name
    if name.startswith("prd2_user_"):
        name = name.replace("prd2_user_", "prd2_ai_comm_", 1)
    elif name.startswith("prd2_assistant_"):
        name = name.replace("prd2_assistant_", "prd2_ai_comm_", 1)
    else:
        name = f"prd2_ai_comm_{name}"
    return log_path.with_name(name)

def _append_ai_comm(comm_path: Path, prompt: str, response: str, pending: bool = False) -> None:
    comm_path.parent.mkdir(parents=True, exist_ok=True)
    with comm_path.open("a", encoding="utf-8") as handle:
        handle.write("\n=== Gemini Request ===\n")
        handle.write(prompt)
        handle.write("\n=== Gemini Response ===\n")
        if pending:
            handle.write("<pending>\n")
        else:
            handle.write(response)
        handle.write("\n=== End ===\n")

def run_agent_once(options: AgentOptions, log_path: Path | None = None) -> str:
    config = load_agent_config(options.config_path)
    log_path = _resolve_log_path(config, log_path=log_path)
    if log_path is None:
        return "No log path available."

    log_excerpt = _read_tail_lines(log_path, config.tail_lines)
    if not log_excerpt:
        return "No log data available yet."

    prompt = _build_prompt(config, log_excerpt)
    return _run_gemini(config.command, prompt)

def run_agent_follow(options: AgentOptions, log_path: Path | None = None) -> None:
    config = load_agent_config(options.config_path)
    log_path = _resolve_log_path(config, log_path=log_path)
    if log_path is None:
        display_warning("No log path available for AI agent.")
        return

    display_info("AI agent active. Watching logs for prompts and changes.")

    last_summary = ""
    offset = log_path.stat().st_size if log_path.exists() else 0
    buffered_lines: list[str] = []
    comm_log_path = _resolve_comm_log_path(log_path)
    last_prompt_present = False
    prompt_consumed = False
    while True:
        if not log_path.exists():
            time.sleep(config.interval_seconds)
            continue

        current_size = log_path.stat().st_size
        if current_size < offset:
            offset = 0
            buffered_lines = []
        new_text, offset = _read_since_offset(log_path, offset)
        if not new_text:
            time.sleep(config.interval_seconds)
            continue
        new_lines = new_text.splitlines()
        buffered_lines.extend(new_lines)
        if len(buffered_lines) > config.tail_lines:
            buffered_lines = buffered_lines[-config.tail_lines :]
        log_excerpt = "\n".join(buffered_lines).strip()
        if not log_excerpt:
            time.sleep(config.interval_seconds)
            continue

        prompt_markers = config.prompt_markers or []
        prompt_present = _detect_prompt(log_excerpt, prompt_markers) if prompt_markers else False
        if not prompt_present:
            time.sleep(config.interval_seconds)
            continue

        if prompt_present and not last_prompt_present:
            display_info("User input detected. Summarizing context with AI agent.")

        if prompt_present and not prompt_consumed and config.fast_diff_summary:
            prompt = _build_prompt(config, log_excerpt)
            _append_ai_comm(comm_log_path, prompt, "", pending=True)
            output = _run_llm(prompt, config.model_id)
            _append_ai_comm(comm_log_path, prompt, output)
            if output:
                print("\n--- DIFF SUMMARY ---\n" + output + "\n")
                last_prompt_present = prompt_present
                prompt_consumed = True
                time.sleep(config.interval_seconds)
                continue

        prompt = _build_prompt(config, log_excerpt)
        _append_ai_comm(comm_log_path, prompt, "", pending=True)
        output = _run_llm(prompt, config.model_id)
        _append_ai_comm(comm_log_path, prompt, output)
        if output and output != last_summary:
            print("\n--- AI AGENT ---\n" + output + "\n")
            last_summary = output

        last_prompt_present = prompt_present
        if not prompt_present:
            prompt_consumed = False

        time.sleep(config.interval_seconds)
