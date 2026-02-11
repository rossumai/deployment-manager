from __future__ import annotations

from dataclasses import dataclass
import json
import re
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

def _find_latest_log_file(log_dir: Path) -> Path | None:
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
    preferred = latest_run / "user.log"
    if preferred.exists():
        return preferred
    log_files = list(latest_run.glob("*.log"))
    if log_files:
        return max(log_files, key=lambda path: path.stat().st_mtime)
    return None

_PLAN_LINE_RE = re.compile(
    r"PLAN:\s+(?P<action>UPDATE|CREATE|DELETE)\s+(?P<type>[a-zA-Z_]+)\s+\"(?P<source_name>.+)\s+\((?P<source_id>\d+)\)\"\s+->\s+\"(?P<target_name>.+)\s+\((?P<target_id>[^\)]+)\)\""
)
_NEW_COPY_TYPE_RE = re.compile(r"/api/v1/(?P<type>[a-z_]+)/<NEW COPY>", re.IGNORECASE)

def _strip_log_artifacts(line: str) -> str:
    if "│" in line:
        parts = line.split("│")
        if len(parts) >= 2:
            line = "│".join(parts[1:-1])
    line = line.replace("\x1b", "")
    return line.strip()

def _build_summary_json(log_excerpt: str) -> str:
    plan_counts: dict[str, dict[str, int]] = {}
    new_copy_counts: dict[str, int] = {}
    new_copy_total = 0
    mappings: list[dict[str, object]] = []
    object_changes: dict[str, dict[str, object]] = {}
    diff_counts: dict[str, int] = {"additions": 0, "deletions": 0}
    diff_occurrences: dict[str, int] = {}
    current_key: str | None = None

    for raw_line in log_excerpt.splitlines():
        line = _strip_log_artifacts(raw_line)
        if not line:
            continue

        if "<NEW COPY>" in line:
            new_copy_total += 1
            type_match = _NEW_COPY_TYPE_RE.search(line)
            if type_match:
                copy_type = type_match.group("type").lower()
            else:
                copy_type = "unknown"
            new_copy_counts[copy_type] = new_copy_counts.get(copy_type, 0) + 1

        plan_match = _PLAN_LINE_RE.search(line)
        if plan_match:
            action = plan_match.group("action").lower()
            obj_type = plan_match.group("type").lower()
            target_id_raw = plan_match.group("target_id")
            new_copy = "<NEW COPY>" in target_id_raw
            target_id_match = re.search(r"\d+", target_id_raw)
            target_id = int(target_id_match.group(0)) if target_id_match else None
            plan_counts.setdefault(obj_type, {})
            plan_counts[obj_type][action] = plan_counts[obj_type].get(action, 0) + 1
            if new_copy:
                new_copy_counts[obj_type] = new_copy_counts.get(obj_type, 0) + 1
                new_copy_total += 1
            source_id = int(plan_match.group("source_id"))
            mappings.append(
                {
                    "action": action,
                    "type": obj_type,
                    "source_id": source_id,
                    "target_id": target_id,
                    "target_id_raw": target_id_raw,
                    "new_copy": new_copy,
                    "source_name": plan_match.group("source_name"),
                    "target_name": plan_match.group("target_name"),
                }
            )
            current_key = f"{obj_type}:{source_id}:{target_id_raw}"
            object_changes.setdefault(
                current_key,
                {
                    "action": action,
                    "type": obj_type,
                    "source_id": source_id,
                    "target_id": target_id,
                    "target_id_raw": target_id_raw,
                    "new_copy": new_copy,
                    "diff_lines": {},
                },
            )
            continue

        stripped = line.lstrip()
        if stripped.startswith("+") and not stripped.startswith("+++"):
            diff_counts["additions"] += 1
            diff_occurrences[stripped] = diff_occurrences.get(stripped, 0) + 1
            if current_key:
                diff_map = object_changes[current_key]["diff_lines"]
                diff_map[stripped] = diff_map.get(stripped, 0) + 1
        elif stripped.startswith("-") and not stripped.startswith("---"):
            diff_counts["deletions"] += 1
            diff_occurrences[stripped] = diff_occurrences.get(stripped, 0) + 1
            if current_key:
                diff_map = object_changes[current_key]["diff_lines"]
                diff_map[stripped] = diff_map.get(stripped, 0) + 1

    repeated_changes = [
        {"line": line, "count": count}
        for line, count in sorted(diff_occurrences.items(), key=lambda item: item[1], reverse=True)
    ]

    total_objects = len(object_changes)
    common_changes = []
    if total_objects:
        for line, count in diff_occurrences.items():
            if count == total_objects:
                common_changes.append({"line": line, "count": count})

    object_change_list = []
    for key, obj in object_changes.items():
        diff_lines = obj["diff_lines"]
        repeated = [
            {"line": line, "count": count}
            for line, count in sorted(diff_lines.items(), key=lambda item: item[1], reverse=True)
        ]
        obj_copy = {k: v for k, v in obj.items() if k != "diff_lines"}
        obj_copy["repeated_changes"] = repeated
        object_change_list.append(obj_copy)

    summary = {
        "plan": {
            "counts": plan_counts,
            "new_copy_counts": new_copy_counts,
            "new_copy_total": new_copy_total,
            "mappings": mappings,
        },
        "diff": {
            "counts": diff_counts,
            "repeated_changes": repeated_changes,
            "common_changes": common_changes,
            "object_changes": object_change_list,
        },
    }
    return json.dumps(summary, ensure_ascii=True)

def _build_prompt(config: AgentConfig, log_excerpt: str, summary_json: str | None = None) -> str:
    agent_instructions = _read_agent_instructions(config)
    skills_text = _read_skills(config)
    base_prompt = config.prompt_prefix
    if agent_instructions:
        base_prompt = f"{base_prompt}\n\nAgent instructions:\n{agent_instructions}"
    if skills_text:
        base_prompt = f"{base_prompt}\n\nSkills:\n{skills_text}"
    summary_block = ""
    if summary_json:
        summary_block = f"\n\nStructured summary JSON:\n{summary_json}"
    diff_instructions = (
        "You must count additions and deletions from diff-like lines. "
        "Count lines whose first non-border character is '+' as additions and '-' as deletions, "
        "ignoring '+++' and '---' headers. "
        "Reply only with: Additions: <n> Deletions: <n>."
    )
    prompt = f"{base_prompt}\n\n{diff_instructions}{summary_block}"
    if log_excerpt:
        prompt = f"{prompt}\n\nLog excerpt:\n{log_excerpt}\n"
    return prompt

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
        latest_log = _find_latest_log_file(config.log_path)
        if latest_log:
            return latest_log
    return None

def _resolve_comm_log_path(log_path: Path) -> Path:
    return log_path.with_name("prd2_ai_communication.log")

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

    summary_json = _build_summary_json(log_excerpt)
    prompt = _build_prompt(config, "", summary_json=summary_json)
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

        summary_json = _build_summary_json(log_excerpt)
        if prompt_present and not prompt_consumed and config.fast_diff_summary:
            prompt = _build_prompt(config, "", summary_json=summary_json)
            _append_ai_comm(comm_log_path, prompt, "", pending=True)
            output = _run_llm(prompt, config.model_id)
            _append_ai_comm(comm_log_path, prompt, output)
            if output:
                print("\n--- DIFF SUMMARY ---\n" + output + "\n")
                last_prompt_present = prompt_present
                prompt_consumed = True
                time.sleep(config.interval_seconds)
                continue

        prompt = _build_prompt(config, "", summary_json=summary_json)
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
