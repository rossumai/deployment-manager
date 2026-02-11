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
    skill_paths = [config.skills_path, *config.extra_skills_paths]
    skill_files: list[Path] = []
    for skill_path in skill_paths:
        if not skill_path.exists():
            continue
        skill_files.extend(sorted(skill_path.glob("*.md")))
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

def _count_skills(skill_path: Path) -> int:
    if not skill_path.exists():
        return 0
    return len([path for path in skill_path.glob("*.md") if path.is_file()])

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
    preferred_raw = latest_run / "user_raw.jsonl"
    if preferred_raw.exists():
        return preferred_raw
    preferred_raw = latest_run / "prd2_user_raw.jsonl"
    if preferred_raw.exists():
        return preferred_raw
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
_ID_SUFFIX_RE = re.compile(r"\[(\d+)\]")
_CONFLICT_FILE_RE = re.compile(r"Conflict between source and remote target detected for:\s*(?P<path>.+)")
_PROMPT_QUESTION_RE = re.compile(r"^(?:\?|PROMPT)\s+(?P<question>.+)")
_REBASE_PROMPT_RE = re.compile(r"Rebase it into source\?", re.IGNORECASE)
_REBASE_DECISION_RE = re.compile(
    r"Rebase it into source\?\s*\([^)]+\)\s*(?P<answer>yy|nn|y|n)\b",
    re.IGNORECASE,
)
_DIFF_HIGHLIGHT_TOKENS = (
    "trigger_condition",
    "engine",
    "score_threshold",
    "queue_ids",
    "hooks",
    "rir_field_names",
    "schema",
    "inbox",
)
_SUSPICIOUS_DIFF_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("empty_len", re.compile(r"\blen\(\)")),
    ("empty_sum", re.compile(r"\bsum\(\)")),
)
_OBJECT_TYPE_ALIASES = {
    "workspace": "workspaces",
    "workspaces": "workspaces",
    "queue": "queues",
    "queues": "queues",
    "schema": "schemas",
    "schemas": "schemas",
    "inbox": "inboxes",
    "inboxes": "inboxes",
    "hook": "hooks",
    "hooks": "hooks",
    "rule": "rules",
    "rules": "rules",
    "engine": "engines",
    "engines": "engines",
    "label": "labels",
    "labels": "labels",
    "email_template": "email_templates",
    "email_templates": "email_templates",
}
_MAX_REPEATED_CHANGES = 20
_MAX_COMMON_CHANGES = 10
_MAX_OBJECT_CHANGES = 25
_MAX_LOG_ITEMS = 10

def _extract_ids_from_path(path: Path) -> list[int]:
    match = _ID_SUFFIX_RE.search(path.stem)
    if not match:
        return []
    return [int(match.group(1))]

def _scan_object_dir(base_dir: Path, patterns: list[str]) -> dict[str, object]:
    ids: list[int] = []
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(base_dir.glob(pattern))
    for path in {p for p in paths if p.is_file()}:
        ids.extend(_extract_ids_from_path(path))
    return {"count": len(ids), "ids": sorted(set(ids))}

def _scan_object_names(base_dir: Path, patterns: list[str], filter_ids: set[int] | None = None) -> dict[int, str]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(base_dir.glob(pattern))
    names: dict[int, str] = {}
    for path in {p for p in paths if p.is_file()}:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        obj_id = data.get("id")
        if obj_id is None:
            ids = _extract_ids_from_path(path)
            obj_id = ids[0] if ids else None
        if obj_id is None:
            continue
        try:
            obj_id_int = int(obj_id)
        except (TypeError, ValueError):
            continue
        if filter_ids is not None and obj_id_int not in filter_ids:
            continue
        name = data.get("name")
        if not name:
            continue
        names[obj_id_int] = str(name)
    return names

def _dedupe_preserve_order(items: list[object]) -> list[object]:
    seen = set()
    deduped = []
    for item in items:
        key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped

def _add_review_question(questions: list[str], seen: set[str], question: str) -> None:
    if question in seen:
        return
    questions.append(question)
    seen.add(question)

def _collect_diff_highlights(line: str, highlights: dict[str, dict[str, int]]) -> None:
    if not line:
        return
    action = None
    if line.startswith("+"):
        action = "additions"
        candidate = line[1:]
    elif line.startswith("-"):
        action = "deletions"
        candidate = line[1:]
    else:
        candidate = line
    lowered = candidate.lower()
    for token in _DIFF_HIGHLIGHT_TOKENS:
        if token in lowered:
            entry = highlights.setdefault(token, {"additions": 0, "deletions": 0})
            if action:
                entry[action] += 1

def _collect_suspicious_patterns(
    line: str,
    patterns: dict[str, dict[str, object]],
    review_questions: list[str],
    review_questions_seen: set[str],
) -> None:
    if not line:
        return
    for name, regex in _SUSPICIOUS_DIFF_PATTERNS:
        if not regex.search(line):
            continue
        entry = patterns.setdefault(name, {"count": 0, "sample": line.strip()})
        entry["count"] = int(entry["count"]) + 1
        if name in {"empty_len", "empty_sum"}:
            _add_review_question(
                review_questions,
                review_questions_seen,
                "Review trigger conditions for empty len()/sum() expressions.",
            )

def _load_deploy_yaml(deploy_file: Path) -> dict:
    try:
        import yaml
    except ImportError:
        return {}
    try:
        return yaml.safe_load(deploy_file.read_text()) or {}
    except Exception:
        return {}

def _resolve_project_root(deploy_file: Path, source_dir: str | None) -> Path:
    if not source_dir:
        return deploy_file.parent
    candidate = deploy_file.parent / source_dir
    if candidate.exists():
        return deploy_file.parent
    if deploy_file.parent.parent:
        candidate = deploy_file.parent.parent / source_dir
        if candidate.exists():
            return deploy_file.parent.parent
    return deploy_file.parent

def _collect_project_context(deploy_file: Path, deploy_data: dict) -> dict[str, object]:
    source_dir = deploy_data.get("source_dir")
    target_dir = deploy_data.get("target_dir")
    project_root = _resolve_project_root(deploy_file, source_dir)
    source_base = project_root / source_dir if source_dir else None
    target_base = project_root / target_dir if target_dir else None
    object_dirs = {
        "workspaces": {
            "patterns": ["workspaces/*.json"],
            "deploy_key": "workspaces",
        },
        "queues": {
            "patterns": ["**/queues/*.json"],
            "deploy_key": "queues",
        },
        "schemas": {
            "patterns": ["**/schemas/*.json"],
            "deploy_key": "schemas",
        },
        "inboxes": {
            "patterns": ["**/inboxes/*.json"],
            "deploy_key": "inboxes",
        },
        "hooks": {
            "patterns": ["hooks/*.json", "**/hooks/*.json"],
            "deploy_key": "hooks",
        },
        "rules": {
            "patterns": ["rules/*.json", "**/rules/*.json"],
            "deploy_key": "rules",
        },
        "engines": {
            "patterns": ["engines/*.json", "**/engines/*.json"],
            "deploy_key": "engines",
        },
        "labels": {
            "patterns": ["labels/*.json", "**/labels/*.json"],
            "deploy_key": "labels",
        },
        "email_templates": {
            "patterns": ["email_templates/*.json", "**/email_templates/*.json"],
            "deploy_key": "email_templates",
        },
    }
    source_counts = {}
    target_counts = {}
    source_names: dict[str, dict[int, str]] = {}
    target_names: dict[str, dict[int, str]] = {}
    if source_base:
        for key, spec in object_dirs.items():
            source_counts[key] = _scan_object_dir(source_base, spec["patterns"])
    if target_base:
        for key, spec in object_dirs.items():
            target_counts[key] = _scan_object_dir(target_base, spec["patterns"])

    deploy_counts: dict[str, list[int]] = {}
    deploy_target_ids: dict[str, set[int]] = {key: set() for key in object_dirs}
    for key, spec in object_dirs.items():
        items = deploy_data.get(spec["deploy_key"]) or []
        ids: list[int] = []
        for item in items:
            if isinstance(item, dict) and item.get("id") is not None:
                ids.append(int(item["id"]))
            if not isinstance(item, dict):
                continue
            for target in item.get("targets") or []:
                if isinstance(target, dict) and target.get("id") is not None:
                    deploy_target_ids[key].add(int(target["id"]))
        deploy_counts[key] = sorted(set(ids))

    queue_items = deploy_data.get("queues") or []
    for item in queue_items:
        if not isinstance(item, dict):
            continue
        schema = item.get("schema")
        if isinstance(schema, dict) and schema.get("id") is not None:
            deploy_counts.setdefault("schemas", [])
            deploy_counts["schemas"] = sorted(set(deploy_counts["schemas"] + [int(schema["id"]) ]))
            for target in schema.get("targets") or []:
                if isinstance(target, dict) and target.get("id") is not None:
                    deploy_target_ids["schemas"].add(int(target["id"]))
        inbox = item.get("inbox")
        if isinstance(inbox, dict) and inbox.get("id") is not None:
            deploy_counts.setdefault("inboxes", [])
            deploy_counts["inboxes"] = sorted(set(deploy_counts["inboxes"] + [int(inbox["id"]) ]))
            for target in inbox.get("targets") or []:
                if isinstance(target, dict) and target.get("id") is not None:
                    deploy_target_ids["inboxes"].add(int(target["id"]))

    for key, spec in object_dirs.items():
        source_filter_ids = set(deploy_counts.get(key, []))
        target_filter_ids = deploy_target_ids.get(key, set())
        if source_base:
            source_names[key] = _scan_object_names(source_base, spec["patterns"], source_filter_ids or None)
        if target_base:
            target_names[key] = _scan_object_names(target_base, spec["patterns"], target_filter_ids or None)

    missing_in_deploy = {}
    for key, info in source_counts.items():
        source_ids = set(info.get("ids", []))
        deploy_ids = set(deploy_counts.get(key, []))
        missing = sorted(source_ids - deploy_ids)
        if missing:
            missing_in_deploy[key] = {
                "count": len(missing),
                "sample_ids": missing[:10],
            }

    deploy_summary = deploy_data.get("deploy_summary") or {}
    multi_target_sources = []
    override_targets_missing_ids = []
    for section, items in deploy_summary.items():
        if not isinstance(items, list):
            continue
        for item in items:
            targets = item.get("targets") or []
            if len(targets) > 1:
                multi_target_sources.append(
                    {
                        "section": section,
                        "source_id": item.get("id"),
                        "name": item.get("name"),
                        "targets": targets,
                    }
                )
            target_overrides = item.get("target_overrides") or []
            if target_overrides and any(target_id in (None, "") for target_id in targets):
                override_targets_missing_ids.append(
                    {
                        "section": section,
                        "source_id": item.get("id"),
                        "name": item.get("name"),
                        "override_count": len(target_overrides),
                        "targets": targets,
                    }
                )
            for key in ("schema", "inbox"):
                nested = item.get(key)
                if not isinstance(nested, dict):
                    continue
                nested_targets = nested.get("targets") or []
                if len(nested_targets) > 1:
                    multi_target_sources.append(
                        {
                            "section": f"{section}.{key}",
                            "source_id": nested.get("id"),
                            "name": item.get("name"),
                            "targets": nested_targets,
                        }
                    )

    return {
        "deploy_file": str(deploy_file),
        "source_dir": source_dir,
        "target_dir": target_dir,
        "project_root": str(project_root),
        "source_counts": source_counts,
        "target_counts": target_counts,
        "deploy_ids": {key: len(ids) for key, ids in deploy_counts.items()},
        "source_name_index": source_names,
        "target_name_index": target_names,
        "missing_in_deploy": missing_in_deploy,
        "multi_target_sources": multi_target_sources,
        "override_targets_missing_ids": override_targets_missing_ids,
    }

def _normalize_object_type(obj_type: str) -> str | None:
    return _OBJECT_TYPE_ALIASES.get(obj_type.lower())

def _collect_id_discrepancies(
    mappings: list[dict[str, object]],
    project: dict[str, object],
) -> list[dict[str, object]]:
    source_index = project.get("source_name_index") or {}
    target_index = project.get("target_name_index") or {}
    source_name_lookup = {
        obj_type: {name: obj_id for obj_id, name in names.items()}
        for obj_type, names in source_index.items()
    }
    discrepancies: list[dict[str, object]] = []
    for mapping in mappings:
        obj_type = _normalize_object_type(str(mapping.get("type") or ""))
        if not obj_type:
            continue
        source_id = mapping.get("source_id")
        target_id = mapping.get("target_id")
        if not isinstance(source_id, int) or not isinstance(target_id, int):
            continue
        source_name = (source_index.get(obj_type) or {}).get(source_id)
        target_name = (target_index.get(obj_type) or {}).get(target_id)
        if source_name and target_name and source_name != target_name:
            collision_id = source_name_lookup.get(obj_type, {}).get(target_name)
            if collision_id is None or collision_id == source_id:
                continue
            discrepancies.append(
                {
                    "type": obj_type,
                    "source_id": source_id,
                    "target_id": target_id,
                    "source_name": source_name,
                    "target_name": target_name,
                    "reason": "name_collision",
                    "collision_source_id": collision_id,
                }
            )
        elif source_name and target_name is None:
            discrepancies.append(
                {
                    "type": obj_type,
                    "source_id": source_id,
                    "target_id": target_id,
                    "source_name": source_name,
                    "target_name": None,
                    "reason": "missing_target",
                }
            )
        elif target_name and source_name is None:
            discrepancies.append(
                {
                    "type": obj_type,
                    "source_id": source_id,
                    "target_id": target_id,
                    "source_name": None,
                    "target_name": target_name,
                    "reason": "missing_source",
                }
            )
    return discrepancies

def _strip_log_artifacts(line: str) -> str:
    if "│" in line:
        parts = line.split("│")
        if len(parts) >= 2:
            line = "│".join(parts[1:-1])
    line = line.replace("\x1b", "")
    return line.strip()

def _load_latest_jsonl_event(log_path: Path, event_name: str) -> dict[str, object] | None:
    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("event") == event_name:
            return payload.get("data", {})
    return None

def _scan_jsonl_log(log_path: Path) -> dict[str, list[object]]:
    conflict_files: list[str] = []
    conflicts: list[str] = []
    warning_messages: list[str] = []
    prompt_questions: list[str] = []
    rebase_prompts: list[str] = []
    rebase_decisions: list[dict[str, str]] = []
    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return {
            "conflict_files": conflict_files,
            "conflicts": conflicts,
            "warning_messages": warning_messages,
            "prompt_questions": prompt_questions,
            "rebase_prompts": rebase_prompts,
            "rebase_decisions": rebase_decisions,
        }
    for raw_line in lines:
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        line = str(payload.get("text") or "").strip()
        if not line:
            continue
        prompt_match = _PROMPT_QUESTION_RE.match(line)
        if prompt_match:
            prompt_questions.append(prompt_match.group("question"))
        if _REBASE_PROMPT_RE.search(line):
            rebase_prompts.append(line)
        rebase_match = _REBASE_DECISION_RE.search(line)
        if rebase_match:
            rebase_decisions.append(
                {
                    "answer": rebase_match.group("answer").lower(),
                    "raw": line,
                }
            )
        conflict_match = _CONFLICT_FILE_RE.search(line)
        if conflict_match:
            conflict_files.append(conflict_match.group("path"))
        if line.startswith("Conflict between "):
            conflicts.append(line)
        elif line.startswith("Conflicts detected:"):
            conflicts.append(line)
        elif "has 'generic_engine' defined" in line:
            warning_messages.append(line)
    return {
        "conflict_files": conflict_files,
        "conflicts": conflicts,
        "warning_messages": warning_messages,
        "prompt_questions": prompt_questions,
        "rebase_prompts": rebase_prompts,
        "rebase_decisions": rebase_decisions,
    }

def _build_summary_json(log_excerpt: str, is_jsonl: bool = False, log_path: Path | None = None) -> str:
    plan_counts: dict[str, dict[str, int]] = {}
    new_copy_counts: dict[str, int] = {}
    new_copy_total = 0
    mappings: list[dict[str, object]] = []
    object_changes: dict[str, dict[str, object]] = {}
    context: dict[str, object] = {}
    warnings: dict[str, list[str]] = {"conflicts": [], "warnings": []}
    diff_counts: dict[str, int] = {"additions": 0, "deletions": 0}
    diff_occurrences: dict[str, int] = {}
    diff_highlights: dict[str, dict[str, int]] = {}
    diff_suspicious: dict[str, dict[str, object]] = {}
    conflict_files: list[str] = []
    warning_messages: list[str] = []
    prompt_questions: list[str] = []
    rebase_prompts: list[str] = []
    rebase_decisions: list[dict[str, str]] = []
    review_questions: list[str] = []
    review_questions_seen: set[str] = set()
    current_key: str | None = None

    for raw_line in log_excerpt.splitlines():
        if is_jsonl:
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if payload.get("event") == "deploy_context":
                context.update(payload.get("data", {}))
                continue
            if payload.get("event") == "deploy_file":
                context.update(payload.get("data", {}))
                continue
            if payload.get("event") == "plan_object":
                data = payload.get("data", {})
                obj_type = str(data.get("type") or "").lower()
                action = str(data.get("action") or "").lower()
                source_id = data.get("source_id")
                target_id = data.get("target_id")
                target_id_raw = str(data.get("target_id")) if data.get("target_id") is not None else ""
                diff_text = data.get("diff") or ""
                plan_counts.setdefault(obj_type, {})
                if action:
                    plan_counts[obj_type][action] = plan_counts[obj_type].get(action, 0) + 1
                mappings.append(
                    {
                        "action": action,
                        "type": obj_type,
                        "source_id": source_id,
                        "target_id": target_id,
                        "target_id_raw": target_id_raw,
                        "new_copy": "<NEW COPY>" in target_id_raw,
                        "source_name": data.get("source_name"),
                        "target_name": data.get("target_name"),
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
                        "new_copy": "<NEW COPY>" in target_id_raw,
                        "diff_lines": {},
                    },
                )
                if "<NEW COPY>" in target_id_raw:
                    new_copy_total += 1
                    new_copy_counts[obj_type] = new_copy_counts.get(obj_type, 0) + 1
                for diff_line in str(diff_text).splitlines():
                    stripped = diff_line.lstrip()
                    if stripped.startswith("+") and not stripped.startswith("+++"):
                        diff_counts["additions"] += 1
                        diff_occurrences[stripped] = diff_occurrences.get(stripped, 0) + 1
                        _collect_diff_highlights(stripped, diff_highlights)
                        _collect_suspicious_patterns(
                            stripped,
                            diff_suspicious,
                            review_questions,
                            review_questions_seen,
                        )
                        diff_map = object_changes[current_key]["diff_lines"]
                        diff_map[stripped] = diff_map.get(stripped, 0) + 1
                    elif stripped.startswith("-") and not stripped.startswith("---"):
                        diff_counts["deletions"] += 1
                        diff_occurrences[stripped] = diff_occurrences.get(stripped, 0) + 1
                        _collect_diff_highlights(stripped, diff_highlights)
                        _collect_suspicious_patterns(
                            stripped,
                            diff_suspicious,
                            review_questions,
                            review_questions_seen,
                        )
                        diff_map = object_changes[current_key]["diff_lines"]
                        diff_map[stripped] = diff_map.get(stripped, 0) + 1
                continue
            line = payload.get("text", "")
        else:
            line = _strip_log_artifacts(raw_line)
        if not line:
            continue

        prompt_match = _PROMPT_QUESTION_RE.match(line)
        if prompt_match:
            prompt_questions.append(prompt_match.group("question"))
        if _REBASE_PROMPT_RE.search(line):
            rebase_prompts.append(line)
        rebase_match = _REBASE_DECISION_RE.search(line)
        if rebase_match:
            rebase_decisions.append(
                {
                    "answer": rebase_match.group("answer").lower(),
                    "raw": line,
                }
            )

        conflict_match = _CONFLICT_FILE_RE.search(line)
        if conflict_match:
            conflict_files.append(conflict_match.group("path"))
            _add_review_question(
                review_questions,
                review_questions_seen,
                "Resolve conflicts listed in the log before applying the plan.",
            )

        if line.startswith("Conflict between "):
            warnings["conflicts"].append(line)
        elif line.startswith("Conflicts detected:"):
            warnings["conflicts"].append(line)
        elif "has 'generic_engine' defined" in line:
            warnings["warnings"].append(line)
            warning_messages.append(line)
            _add_review_question(
                review_questions,
                review_questions_seen,
                "Ensure any referenced generic engines exist and are assigned in the target.",
            )

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
            _collect_diff_highlights(stripped, diff_highlights)
            _collect_suspicious_patterns(
                stripped,
                diff_suspicious,
                review_questions,
                review_questions_seen,
            )
            if current_key:
                diff_map = object_changes[current_key]["diff_lines"]
                diff_map[stripped] = diff_map.get(stripped, 0) + 1
        elif stripped.startswith("-") and not stripped.startswith("---"):
            diff_counts["deletions"] += 1
            diff_occurrences[stripped] = diff_occurrences.get(stripped, 0) + 1
            _collect_diff_highlights(stripped, diff_highlights)
            _collect_suspicious_patterns(
                stripped,
                diff_suspicious,
                review_questions,
                review_questions_seen,
            )
            if current_key:
                diff_map = object_changes[current_key]["diff_lines"]
                diff_map[stripped] = diff_map.get(stripped, 0) + 1

    repeated_changes = [
        {"line": line, "count": count}
        for line, count in sorted(diff_occurrences.items(), key=lambda item: item[1], reverse=True)
    ]
    repeated_changes = repeated_changes[:_MAX_REPEATED_CHANGES]

    total_objects = len(object_changes)
    common_changes = []
    if total_objects:
        for line, count in diff_occurrences.items():
            if count == total_objects:
                common_changes.append({"line": line, "count": count})
    common_changes = common_changes[:_MAX_COMMON_CHANGES]

    object_change_list = []
    for key, obj in object_changes.items():
        diff_lines = obj["diff_lines"]
        repeated = [
            {"line": line, "count": count}
            for line, count in sorted(diff_lines.items(), key=lambda item: item[1], reverse=True)
        ]
        repeated = repeated[:_MAX_REPEATED_CHANGES]
        obj_copy = {k: v for k, v in obj.items() if k != "diff_lines"}
        obj_copy["repeated_changes"] = repeated
        object_change_list.append(obj_copy)
    object_change_list = object_change_list[:_MAX_OBJECT_CHANGES]

    summary = {
        "context": context,
        "warnings": warnings,
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
            "highlights": diff_highlights,
            "suspicious_patterns": diff_suspicious,
        },
        "log": {
            "conflict_files": conflict_files,
            "warning_messages": warning_messages,
            "prompt_questions": prompt_questions,
            "rebase_prompts": rebase_prompts,
            "rebase_decisions": rebase_decisions,
            "review_questions": review_questions,
        },
    }
    if log_path is not None:
        context_path = log_path.parent / "deploy_context.json"
        if context_path.exists():
            try:
                context = json.loads(context_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                context = context
        if is_jsonl and not context:
            context = _load_latest_jsonl_event(log_path, "deploy_context") or {}
        summary["context"] = context

        if is_jsonl and log_path.exists():
            jsonl_summary = _scan_jsonl_log(log_path)
            for item in jsonl_summary["conflict_files"]:
                if item not in conflict_files:
                    conflict_files.append(item)
            for item in jsonl_summary["conflicts"]:
                if item not in warnings["conflicts"]:
                    warnings["conflicts"].append(item)
            for item in jsonl_summary["warning_messages"]:
                if item not in warning_messages:
                    warning_messages.append(item)
                if item not in warnings["warnings"]:
                    warnings["warnings"].append(item)
                    _add_review_question(
                        review_questions,
                        review_questions_seen,
                        "Ensure any referenced generic engines exist and are assigned in the target.",
                    )
            for item in jsonl_summary["prompt_questions"]:
                if item not in prompt_questions:
                    prompt_questions.append(item)
            for item in jsonl_summary["rebase_prompts"]:
                if item not in rebase_prompts:
                    rebase_prompts.append(item)
            for item in jsonl_summary["rebase_decisions"]:
                if item not in rebase_decisions:
                    rebase_decisions.append(item)
            if jsonl_summary["conflict_files"] or jsonl_summary["conflicts"]:
                _add_review_question(
                    review_questions,
                    review_questions_seen,
                    "Resolve conflicts listed in the log before applying the plan.",
                )
            if jsonl_summary["rebase_decisions"]:
                if any(decision.get("answer") in {"y", "yy"} for decision in jsonl_summary["rebase_decisions"]):
                    _add_review_question(
                        review_questions,
                        review_questions_seen,
                        "Rebase accepted for target-only changes; confirm they are intended.",
                    )
                if any(decision.get("answer") in {"n", "nn"} for decision in jsonl_summary["rebase_decisions"]):
                    _add_review_question(
                        review_questions,
                        review_questions_seen,
                        "Rebase rejected for target-only changes; validate target differences remain acceptable.",
                    )
            elif jsonl_summary["rebase_prompts"]:
                _add_review_question(
                    review_questions,
                    review_questions_seen,
                    "Confirm target-only changes before accepting rebase prompts.",
                )
            summary["warnings"] = warnings
            summary["log"] = {
                "conflict_files": conflict_files[:_MAX_LOG_ITEMS],
                "warning_messages": warning_messages[:_MAX_LOG_ITEMS],
                "prompt_questions": prompt_questions[:_MAX_LOG_ITEMS],
                "rebase_prompts": rebase_prompts[:_MAX_LOG_ITEMS],
                "rebase_decisions": rebase_decisions[:_MAX_LOG_ITEMS],
                "review_questions": review_questions[:_MAX_LOG_ITEMS],
            }

    deploy_file = summary["context"].get("deploy_file")
    if deploy_file:
        deploy_path = Path(str(deploy_file))
        deploy_data = _load_deploy_yaml(deploy_path)
        project = _collect_project_context(deploy_path, deploy_data)
        summary["project"] = project
        summary["mapping"] = {
            "id_discrepancies": _collect_id_discrepancies(mappings, project)[:_MAX_LOG_ITEMS],
        }
    summary["plan"]["mappings"] = _dedupe_preserve_order(summary["plan"]["mappings"])[:_MAX_OBJECT_CHANGES]
    summary["log"]["conflict_files"] = _dedupe_preserve_order(summary["log"]["conflict_files"])
    summary["log"]["warning_messages"] = _dedupe_preserve_order(summary["log"]["warning_messages"])
    summary["log"]["prompt_questions"] = _dedupe_preserve_order(summary["log"]["prompt_questions"])
    summary["log"]["rebase_prompts"] = _dedupe_preserve_order(summary["log"]["rebase_prompts"])
    summary["log"]["rebase_decisions"] = _dedupe_preserve_order(summary["log"]["rebase_decisions"])
    summary["log"]["review_questions"] = _dedupe_preserve_order(summary["log"]["review_questions"])
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
        if log_path.is_file() and log_path.suffix == ".log":
            raw_user = log_path.with_name("user_raw.jsonl")
            if raw_user.exists():
                return raw_user
            raw_user = log_path.with_name("prd2_user_raw.jsonl")
            if raw_user.exists():
                return raw_user
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

def _build_prompt_for_summary(config: AgentConfig, summary_json: str) -> str:
    agent_instructions = _read_agent_instructions(config)
    skills_text = _read_skills(config)
    base_prompt = config.prompt_prefix
    if agent_instructions:
        base_prompt = f"{base_prompt}\n\nAgent instructions:\n{agent_instructions}"
    if skills_text:
        base_prompt = f"{base_prompt}\n\nSkills:\n{skills_text}"
    summary_block = f"\n\nStructured summary JSON:\n{summary_json}"
    return f"{base_prompt}{summary_block}"

def run_agent_once(options: AgentOptions, log_path: Path | None = None) -> str:
    config = load_agent_config(options.config_path)
    log_path = _resolve_log_path(config, log_path=log_path)
    if log_path is None:
        return "No log path available."

    log_excerpt = _read_tail_lines(log_path, config.tail_lines)
    if not log_excerpt:
        return "No log data available yet."

    summary_json = _build_summary_json(
        log_excerpt,
        is_jsonl=log_path.suffix == ".jsonl",
        log_path=log_path,
    )
    prompt = _build_prompt_for_summary(config, summary_json)
    return _run_gemini(config.command, prompt)

def run_agent_follow(options: AgentOptions, log_path: Path | None = None) -> None:
    config = load_agent_config(options.config_path)
    log_path = _resolve_log_path(config, log_path=log_path)
    if log_path is None:
        display_warning("No log path available for AI agent.")
        return

    base_skill_count = _count_skills(config.skills_path)
    extra_skill_count = sum(_count_skills(path) for path in config.extra_skills_paths)
    display_info("AI agent active. Watching logs for prompts and changes.")
    display_info(f"Loaded {base_skill_count} base skill(s), {extra_skill_count} custom skill(s).")

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

        summary_json = _build_summary_json(
            log_excerpt,
            is_jsonl=log_path.suffix == ".jsonl",
            log_path=log_path,
        )
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

        prompt = _build_prompt_for_summary(config, summary_json)
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
