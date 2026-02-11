import json
from pathlib import Path

import questionary
from anyio import Path as AsyncPath

from deployment_manager.ai_agent.config import load_agent_config
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.document.llm_helper import LLMHelper
from deployment_manager.utils.consts import display_error, display_info, settings

_MISSING_TARGET_KEYS = {
    settings.DEPLOY_KEY_WORKSPACES,
    settings.DEPLOY_KEY_QUEUES,
    settings.DEPLOY_KEY_HOOKS,
    settings.DEPLOY_KEY_RULES,
    settings.DEPLOY_KEY_ENGINES,
    settings.DEPLOY_KEY_LABELS,
    settings.DEPLOY_KEY_EMAIL_TEMPLATES,
}

def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, json.JSONDecodeError):
        return {}

def _scan_target_inventory(target_base: Path) -> dict[str, list[dict[str, object]]]:
    inventory: dict[str, list[dict[str, object]]] = {
        "workspaces": [],
        "queues": [],
        "schemas": [],
        "inboxes": [],
        "hooks": [],
        "rules": [],
        "engines": [],
        "labels": [],
        "email_templates": [],
    }

    workspaces_dir = target_base / "workspaces"
    if workspaces_dir.exists():
        for ws_dir in workspaces_dir.iterdir():
            if not ws_dir.is_dir():
                continue
            ws_json = ws_dir / "workspace.json"
            data = _read_json(ws_json) if ws_json.exists() else {}
            if data.get("id"):
                inventory["workspaces"].append({"id": data.get("id"), "name": data.get("name")})
            queues_dir = ws_dir / "queues"
            if not queues_dir.exists():
                continue
            for queue_dir in queues_dir.iterdir():
                if not queue_dir.is_dir():
                    continue
                queue_json = queue_dir / "queue.json"
                queue_data = _read_json(queue_json) if queue_json.exists() else {}
                if queue_data.get("id"):
                    inventory["queues"].append(
                        {
                            "id": queue_data.get("id"),
                            "name": queue_data.get("name"),
                            "workspace_id": data.get("id"),
                            "workspace_name": data.get("name"),
                        }
                    )
                schema_json = queue_dir / "schema.json"
                schema_data = _read_json(schema_json) if schema_json.exists() else {}
                if schema_data.get("id"):
                    inventory["schemas"].append(
                        {
                            "id": schema_data.get("id"),
                            "name": schema_data.get("name"),
                            "queue_id": queue_data.get("id"),
                        }
                    )
                inbox_json = queue_dir / "inbox.json"
                inbox_data = _read_json(inbox_json) if inbox_json.exists() else {}
                if inbox_data.get("id"):
                    inventory["inboxes"].append(
                        {
                            "id": inbox_data.get("id"),
                            "name": inbox_data.get("name"),
                            "queue_id": queue_data.get("id"),
                        }
                    )

                for template_path in (queue_dir / "email_templates").glob("*.json"):
                    template_data = _read_json(template_path)
                    if template_data.get("id"):
                        inventory["email_templates"].append(
                            {"id": template_data.get("id"), "name": template_data.get("name")}
                        )

    hooks_dir = target_base / "hooks"
    if hooks_dir.exists():
        for hook_path in hooks_dir.glob("*.json"):
            data = _read_json(hook_path)
            if data.get("id"):
                inventory["hooks"].append({"id": data.get("id"), "name": data.get("name")})

    for rule_path in target_base.rglob("rules/*.json"):
        data = _read_json(rule_path)
        if data.get("id"):
            inventory["rules"].append({"id": data.get("id"), "name": data.get("name")})

    for engine_path in target_base.rglob("engines/*.json"):
        data = _read_json(engine_path)
        if data.get("id"):
            inventory["engines"].append({"id": data.get("id"), "name": data.get("name")})

    for label_path in target_base.rglob("labels/*.json"):
        data = _read_json(label_path)
        if data.get("id"):
            inventory["labels"].append({"id": data.get("id"), "name": data.get("name")})

    return inventory

def _collect_missing_targets(deploy_data: dict) -> tuple[list[dict[str, object]], dict[tuple[str, int], list[dict]]]:
    missing: list[dict[str, object]] = []
    target_index: dict[tuple[str, int], list[dict]] = {}

    def register_missing(obj_type: str, source_id: int, source_name: str | None, target: dict, extra: dict | None):
        entry = {
            "type": obj_type,
            "source_id": source_id,
            "source_name": source_name,
        }
        if extra:
            entry.update(extra)
        missing.append(entry)
        target_index.setdefault((obj_type, source_id), []).append(target)

    for key in _MISSING_TARGET_KEYS:
        for item in deploy_data.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            source_id = item.get("id")
            if source_id is None:
                continue
            targets = item.get("targets") or []
            for target in targets:
                if not isinstance(target, dict):
                    continue
                if target.get("id"):
                    continue
                register_missing(key, int(source_id), item.get("name"), target, None)

    for queue in deploy_data.get(settings.DEPLOY_KEY_QUEUES, []) or []:
        if not isinstance(queue, dict):
            continue
        queue_name = queue.get("name")
        for nested_key, target_key in (("schema", "schemas"), ("inbox", "inboxes")):
            nested = queue.get(nested_key)
            if not isinstance(nested, dict):
                continue
            source_id = nested.get("id")
            if source_id is None:
                continue
            for target in nested.get("targets") or []:
                if not isinstance(target, dict):
                    continue
                if target.get("id"):
                    continue
                register_missing(
                    target_key,
                    int(source_id),
                    queue_name,
                    target,
                    {"queue_name": queue_name, "queue_id": queue.get("id")},
                )

    return missing, target_index

def _read_skill_prompt(project_root: Path) -> str:
    config_path = project_root / "ai_agent.yaml"
    try:
        config = load_agent_config(config_path)
    except Exception:
        return ""
    skill_paths = [*config.extra_skills_paths, config.skills_path]
    for skill_path in skill_paths:
        if not skill_path.exists():
            continue
        skill_file = skill_path / "deploy-template-assistant.md"
        if not skill_file.exists():
            continue
        try:
            skill_text = skill_file.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if skill_text:
            return f"\n# Skill: {skill_file.name}\n{skill_text}"
    return ""

def _extract_json_payload(text: str) -> dict:
    if not text:
        raise ValueError("Empty LLM response")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        candidate = cleaned[brace_start : brace_end + 1]
        return json.loads(candidate)
    raise ValueError("LLM response did not contain valid JSON")

def _build_prompt(skill_prompt: str, missing_targets: list[dict[str, object]], inventory: dict[str, list[dict]]):
    return (
        f"{skill_prompt}\n\n"
        "Task: Fill missing target IDs in the deploy template using only the local target inventory. "
        "Do not create new objects and do not change non-empty target IDs. "
        "Return JSON only, with a single key 'mappings' containing entries with "
        "type, source_id, and target_id. Omit items you cannot confidently match. "
        "Ignore any other formatting instructions above and respond with JSON only.\n\n"
        f"Missing targets:\n{json.dumps(missing_targets, ensure_ascii=True, indent=2)}\n\n"
        f"Target inventory:\n{json.dumps(inventory, ensure_ascii=True, indent=2)}\n"
    )

async def enhance_deploy_template(
    deploy_file_path: AsyncPath,
    project_path: AsyncPath | None = None,
    model_id: str | None = None,
):
    if not project_path:
        project_path = AsyncPath("./")
    deploy_text = await deploy_file_path.read_text()
    yaml = DeployYaml(file=deploy_text)
    deploy_data = yaml.data or {}

    target_dir = deploy_data.get(settings.DEPLOY_KEY_TARGET_DIR)
    if not target_dir:
        display_error("Target dir is missing in the deploy file.")
        return

    target_base = Path(str(project_path)) / str(target_dir)
    if not target_base.exists():
        display_error(f'Target dir "{target_base}" not found.')
        return

    missing_targets, target_index = _collect_missing_targets(deploy_data)
    if not missing_targets:
        display_info("No missing target IDs found in deploy file.")
        return

    inventory = _scan_target_inventory(target_base)
    skill_prompt = _read_skill_prompt(Path(str(project_path)))
    if not skill_prompt:
        display_error("No deploy template assistant skill found.")
        return
    prompt = _build_prompt(skill_prompt, missing_targets, inventory)

    helper = LLMHelper(model_id=model_id)
    if not helper.validate_credentials():
        return
    response = await helper.run(prompt)
    if not response or not response.text:
        display_error("LLM did not return any response.")
        return

    try:
        payload = _extract_json_payload(response.text)
    except Exception as exc:
        display_error(f"Failed to parse LLM response as JSON: {exc}")
        return

    mappings = payload.get("mappings") or []
    if not isinstance(mappings, list):
        display_error("LLM response must include a list under 'mappings'.")
        return

    applied = []
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        obj_type = mapping.get("type")
        source_id = mapping.get("source_id")
        target_id = mapping.get("target_id")
        if obj_type is None or source_id is None or target_id in (None, ""):
            continue
        try:
            key = (str(obj_type), int(source_id))
            target_id_int = int(target_id)
        except (TypeError, ValueError):
            continue
        targets = target_index.get(key) or []
        for target in targets:
            if target.get("id"):
                continue
            target["id"] = target_id_int
        if targets:
            applied.append({"type": obj_type, "source_id": source_id, "target_id": target_id_int})

    if not applied:
        display_info("No target IDs were filled from the LLM response.")
        return

    display_info(f"Proposed {len(applied)} target ID updates.")
    for entry in applied[:10]:
        display_info(
            f"{entry['type']} source {entry['source_id']} -> target {entry['target_id']}"
        )

    if not await questionary.confirm("Apply these changes to the deploy file?", default=False).ask_async():
        display_info("Aborted. No changes were saved.")
        return

    await yaml.save_to_file(deploy_file_path)
    display_info(f"Deploy template updated: {deploy_file_path}")
