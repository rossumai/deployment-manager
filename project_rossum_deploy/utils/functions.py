import asyncio
import copy
from functools import wraps
import dataclasses
import json
from typing import Any
from anyio import Path
from rich.progress import Progress
import yaml

from project_rossum_deploy.utils.consts import GIT_CHARACTERS, Settings


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def templatize_name_id(name, id):
    return f"{name}_[{id}]"


# ID_BRACKET_RE = re.compile(r"(\[\d+\])$")


async def merge_hook_changes(changes, org_path):
    merged_changes = []
    for change in changes:
        if not change:
            continue
        change = change.strip()
        op, path = tuple(change.strip().split(" ", maxsplit=1))
        path = path.strip('"')
        if op == GIT_CHARACTERS.UPDATED and (
            path.endswith("py") or path.endswith("js")
        ):
            with open(path, "r") as file:
                code_str = file.read()
                object_path = org_path / (
                    path.removesuffix(".py").removesuffix(".js") + ".json"
                )
                hook_object = await read_json(object_path)
                hook_object["config"]["code"] = code_str
                await write_json(object_path, hook_object)
                new_change = f'M "{object_path}"'
                if new_change not in merged_changes:
                    print(new_change)
                    merged_changes.append(new_change)
        elif change not in merged_changes:
            print(change)
            merged_changes.append(change)
    print(merged_changes)
    return merged_changes


def detemplatize_name_id(joint_name: str) -> tuple[str, int]:
    parts = joint_name.split("_")
    return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))


def extract_id_from_url(url: str) -> int:
    if not url:
        return None
    return int(url.split("/")[-1])


async def write_str(path: Path, code: str):
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        wf.write(code)


def get_mapping_key_index(key: str):
    try:
        return Settings.MAPPING_KEYS_ORDER.index(key)
    except Exception:
        return -1


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
        yaml.dump(object, wf, sort_keys=False)


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
            "target_object": None,
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
        targets["organization"] = mapping["organization"]["target_object"]
        sources["organization"] = mapping["organization"]["id"]

    for ws in mapping["organization"]["workspaces"]:
        sources["workspaces"].append(ws["id"])
        if ws["target_object"]:
            targets["workspaces"].append(ws["target_object"])

        for q in ws["queues"]:
            sources["queues"].append(q["id"])
            if q["target_object"]:
                targets["queues"].append(q["target_object"])

            sources["inboxes"].append(q["inbox"]["id"])
            if q["inbox"] and q["inbox"]["target_object"]:
                targets["inboxes"].append(q["inbox"]["target_object"])

    for schema in mapping["organization"]["schemas"]:
        sources["schemas"].append(schema["id"])
        if schema["target_object"]:
            targets["schemas"].append(schema["target_object"])

    for hook in mapping["organization"]["hooks"]:
        sources["hooks"].append(hook["id"])
        if hook["target_object"]:
            targets["hooks"].append(hook["target_object"])

    return sources, targets


def extract_source_target_pairs(mapping: dict) -> dict:
    sources, targets = extract_sources_targets(mapping, include_organization=False)
    pairs = {}
    for object_type, sources in sources.items():
        pairs[object_type] = dict(zip(sources, targets[object_type]))
    return pairs


# https://stackoverflow.com/questions/73464511/rich-prompt-confirm-not-working-in-rich-progress-context-python
class PauseProgress:
    def __init__(self, progress: Progress) -> None:
        self._progress = progress

    def _clear_line(self) -> None:
        UP = "\x1b[1A"
        CLEAR = "\x1b[2K"
        for _ in self._progress.tasks:
            print(UP + CLEAR + UP)

    def __enter__(self):
        self._progress.stop()
        self._clear_line()
        return self._progress

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._progress.start()
