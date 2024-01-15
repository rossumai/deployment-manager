import asyncio
import copy
from functools import wraps
import dataclasses
import json
from typing import Any
from anyio import Path

import yaml


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def templatize_name_id(name, id):
    return f"{name}_[{id}]"


# ID_BRACKET_RE = re.compile(r"(\[\d+\])$")


def detemplatize_name_id(joint_name: str) -> tuple[str, int]:
    parts = joint_name.split("_")
    return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))


def extract_id_from_url(url: str) -> int:
    if not url:
        return None
    return int(url.split("/")[-1])


async def write_json(path: Path, object: dict):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        json.dump(object, wf, indent=2)


async def read_json(path: Path):
    return json.loads(await path.read_text())


async def write_yaml(path: Path, object: dict):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        yaml.dump(object, wf)


def read_yaml(path: Path):
    with open(path, "r") as rf:
        return yaml.safe_load(rf)


def adjust_keys(object: Any, uppercase_fields: list = [], lower: bool = True):
    if isinstance(object, dict):
        lowercased = {}
        for k, v in object.items():
            new_key = k
            if lower:
                new_key = k.lower()
            elif not lower and k in uppercase_fields:
                new_key = k.upper()
            lowercased[new_key] = adjust_keys(v, uppercase_fields, lower)
        return lowercased
    elif isinstance(object, list):
        lowercased = []
        for v in object:
            lowercased.append(adjust_keys(v, uppercase_fields, lower))
        return lowercased
    else:
        return object


async def retrieve_with_progress(retrieve, progress, task):
    result = await retrieve()
    progress.update(task, advance=1)
    return result


def create_empty_mapping():
    return {
        "organization": {
            "id": "",
            "name": "",
            "target": None,
            "workspaces": [],
            "hooks": [],
            "schemas": [],
        }
    }


def extract_sources_targets(
    mapping: dict, include_organization=True
) -> tuple[dict, dict]:
    if not mapping:
        mapping = create_empty_mapping()

    targets = {
        "workspaces": [],
        "queues": [],
        "inboxes": [],
        "schemas": [],
        "hooks": [],
    }
    sources = copy.deepcopy(targets)

    if include_organization:
        targets["organization"] = mapping["organization"]["target"]
        sources["organization"] = mapping["organization"]["id"]

    for ws in mapping["organization"]["workspaces"]:
        sources["workspaces"].append(ws["id"])
        if ws["target"]:
            targets["workspaces"].append(ws["target"])

        for q in ws["queues"]:
            sources["queues"].append(q["id"])
            if q["target"]:
                targets["queues"].append(q["target"])

            sources["inboxes"].append(q["inbox"]["id"])
            if q["inbox"] and q["inbox"]["target"]:
                targets["inboxes"].append(q["inbox"]["target"])

    for schema in mapping["organization"]["schemas"]:
        sources["schemas"].append(schema["id"])
        if schema["target"]:
            targets["schemas"].append(schema["target"])

    for hook in mapping["organization"]["hooks"]:
        sources["hooks"].append(hook["id"])
        if hook["target"]:
            targets["hooks"].append(hook["target"])

    return sources, targets


def extract_source_target_pairs(mapping: dict) -> dict:
    sources, targets = extract_sources_targets(mapping, include_organization=False)
    pairs = {}
    for object_type, sources in sources.items():
        pairs[object_type] = dict(zip(sources, targets[object_type]))
    return pairs
