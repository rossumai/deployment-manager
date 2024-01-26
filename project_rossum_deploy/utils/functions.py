import asyncio
import copy
import logging
from functools import wraps
import dataclasses
import json
import os
import re
from typing import Any
from anyio import Path
from click import progressbar
from rich.prompt import Confirm
from rossum_api import ElisAPIClient

import yaml

from project_rossum_deploy.utils.consts import GIT_CHARACTERS, Settings


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


FORBIDDEN_CHARS_REGEX = re.compile(r"[/\\]")


def templatize_name_id(name: str, id: int):
    return f"{re.sub(FORBIDDEN_CHARS_REGEX, '', name)}_[{id}]"


# ID_BRACKET_RE = re.compile(r"(\[\d+\])$")


async def evaluate_delete_dependencies(changes, org_path):
    changes_updated = []
    for change in changes:
        op, path = change
        if op == GIT_CHARACTERS.DELETED:
            if str(path).endswith("workspace.json"):
                if not Confirm.ask(
                    "You are about to delete a workspace - the tool will cascade delete all associated queues/inboxes with the workspace. Are you sure you want to proceed?",
                ):
                    continue
                changes_updated = await cascade_delete_ops(
                    path, change, changes_updated, org_path
                )
            elif str(path).endswith("queue.json"):
                changes_updated = await cascade_delete_ops(
                    path, change, changes_updated, org_path
                )
            else:
                if not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
        else:
            if not is_change_existing(change, changes_updated):
                changes_updated.append(change)

    return changes_updated


async def cascade_delete_ops(path, change, changes_updated, org_path):
    abs_path = await path.parent.absolute()
    file_set = set()
    for dir_, _, files in os.walk(str(abs_path)):
        for file_name in files:
            rel_dir = os.path.relpath(dir_, str(abs_path))
            rel_file = os.path.join(rel_dir, file_name)
            file_set.add(rel_file)
    for object in file_set:
        new_path = Path("source") / org_path / Path(object)
        if (
            new_path.stem == "inbox"
        ):  # ignore deleting inboxes, it will be deleted when queue is deleted
            continue
        op_obj = ("D", new_path)
        if not is_change_existing(op_obj, changes_updated):
            changes_updated.append(op_obj)
    if not is_change_existing(change, changes_updated):
        changes_updated.append(change)
    return changes_updated


async def evaluate_create_dependencies(changes, org_path, client: ElisAPIClient):
    changes_updated = []
    for change in changes:
        op, path = change
        if op == GIT_CHARACTERS.CREATED or op == GIT_CHARACTERS.CREATED_STAGED:
            object_path = org_path / path
            object = await read_json(object_path)
            id = object["id"]
            obj = None
            if str(path).endswith("workspace.json"):
                if id:
                    obj = client.retrieve_workspace(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path).endswith("queue.json"):
                if id:
                    obj = client.retrieve_queue(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path.parent).endswith("hooks"):
                if id:
                    obj = client.retrieve_hook(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path.parent).endswith("schemas"):
                if id:
                    obj = client.retrieve_schema(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path).endswith("inbox.json") or str(path).endswith(
                "organization.json"
            ):
                logging.warning(
                    f"Creating organization or inbox is not supported.{path}"
                )
            else:
                if not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
        else:
            changes_updated.append(change)

    return changes_updated


async def merge_hook_changes(changes, org_path):
    merged_changes = []
    for change in changes:
        op, path = change
        if (op == GIT_CHARACTERS.UPDATED or op == GIT_CHARACTERS.CREATED or op == GIT_CHARACTERS.CREATED_STAGED) and (str(path).endswith("py") or str(path).endswith("js")):
            with open(path, "r") as file:
                code_str = file.read()
                object_path = org_path / (
                    Path(str(path).removesuffix(".py").removesuffix(".js") + ".json")
                )
                hook_object = await read_json(object_path)
                hook_object["config"]["code"] = code_str
                await write_json(object_path, hook_object)
                new_change = ("M", object_path)
                exists = is_change_existing(new_change, merged_changes)
                if not exists:
                    merged_changes.append(new_change)
        elif not is_change_existing(change, merged_changes):
            merged_changes.append(change)
    return merged_changes


def detemplatize_name_id(path: Path | str) -> tuple[str, int]:
    if isinstance(path, str):
        parts = path.split("_")
        return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))

    if str(path.stem) in ["queue", "workspace"]:
        parts = path.parent.stem.split("_")
        return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))
    elif str(path.parent.stem) in ("hooks, schemas"):
        parts = path.stem.split("_")
        return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))


def is_change_existing(change, changes):
    c_op, c_path = change
    for op, path in changes:
        if c_op == op and str(c_path) == str(path):
            return True
    return False


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


async def write_json(path: Path, object: dict, type: str = None):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    if type:
        ignored_keys = Settings.IGNORED_KEYS.get(type)
        if ignored_keys:
            for key in ignored_keys:
                if key in object:
                    del object[key]
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
    def __init__(self, progress: progressbar) -> None:
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
