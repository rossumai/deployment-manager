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
from rich.console import Console
from rich.panel import Panel
from rossum_api import ElisAPIClient

import yaml

from project_rossum_deploy.utils.consts import (
    GIT_CHARACTERS,
    settings,
)


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


FORBIDDEN_CHARS_REGEX = re.compile(r"[/\\\"\'\`]")


def templatize_name_id(name: str, id: int):
    return f"{re.sub(FORBIDDEN_CHARS_REGEX, '', name)}_[{id}]"


# ID_BRACKET_RE = re.compile(r"(\[\d+\])$")


def convert_source_to_target_value(source_value, lookup_table: dict):
    """Finds a counterpart id in the lookup table file and replace it based on the type of the original value"""
    type, source_id = convert_reference_to_int_id(source_value)
    target_id = lookup_table.get(source_id, None)
    if target_id is not None:
        match type:
            case "str":
                return str(target_id)
            case "url":
                parts = source_value.split("/")[:-1]
                parts.append(str(target_id))
                return "".join(parts)
            case "int":
                return target_id
    return None


def convert_reference_to_int_id(value):
    """Converts value into int if necessary and returns the original type - supports int, str and url (ie. https://elis.rossum.ai/api/v1/queues/156)"""
    if isinstance(value, int):
        return "int", value
    elif isinstance(value, str) and "https" in value:
        return "url", int(value.split("/")[-1])
    elif isinstance(value, str):
        return "str", int(value)


def flatten(x):
    result = []
    for el in x:
        if isinstance(el, list):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


async def find_all_object_paths(base_directory: Path) -> list[Path]:
    return [file async for file in base_directory.glob("**/*.json")]


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
        path: Path
        op, path = change
        if (
            op == GIT_CHARACTERS.CREATED or op == GIT_CHARACTERS.CREATED_STAGED
        ) and path.suffix == ".json":
            object_path = org_path / path
            object = await read_json(object_path)
            id = object.get("id", None)
            obj = None
            if str(path).endswith("workspace.json"):
                if id:
                    obj = await client.retrieve_workspace(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path).endswith("queue.json"):
                if id:
                    obj = await client.retrieve_queue(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path.parent).endswith("hooks"):
                if id:
                    obj = await client.retrieve_hook(id)
                if not obj and not is_change_existing(change, changes_updated):
                    changes_updated.append(change)
            elif str(path.parent).endswith("schemas"):
                if id:
                    obj = await client.retrieve_schema(id)
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
        path = str(path)
        if (
            op == GIT_CHARACTERS.UPDATED
            or op == GIT_CHARACTERS.CREATED
            or op == GIT_CHARACTERS.CREATED_STAGED
        ) and (path.endswith("py") and "hooks" in path):
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


async def merge_formula_changes(changes):
    merged_changes = []
    for change in changes:
        op: str
        path: Path
        op, path = change
        str_path = str(path)

        if (
            (
                op == GIT_CHARACTERS.UPDATED
                or op == GIT_CHARACTERS.CREATED
                or op == GIT_CHARACTERS.CREATED_STAGED
            )
            and (path.suffix == ".py")
            and "schemas" in str_path
        ):
            formula_code = await read_formula_file(path)
            formula_name = path.stem

            schema_file_name = str(path.parent.stem).removeprefix(
                settings.FORMULA_DIR_PREFIX
            )
            schema_path = path.parent.parent / f"{schema_file_name}.json"
            schema = await read_json(schema_path)

            schema_id = find_schema_id(schema["content"], formula_name)
            schema_id["formula"] = formula_code

            await write_json(schema_path, schema)
            new_change = ("M", schema_path)
            if not is_change_existing(new_change, merged_changes):
                merged_changes.append(new_change)
        elif not is_change_existing(change, merged_changes):
            merged_changes.append(change)
    return merged_changes


async def read_formula_file(path: Path):
    return await path.read_text()


def find_schema_id(schema: Any, schema_id: str):
    if isinstance(schema, list):
        for subschema in schema:
            result = find_schema_id(subschema, schema_id)
            if result:
                return result
    elif isinstance(schema, dict) and "children" in schema:
        if isinstance(schema["children"], dict):
            result = find_schema_id(schema["children"], schema_id)
            if result:
                return result
        elif isinstance(schema["children"], list):
            for subschema in schema["children"]:
                result = find_schema_id(subschema, schema_id)
                if result:
                    return result
    elif isinstance(schema, dict) and schema.get("id", None) == schema_id:
        return schema


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
        return settings.MAPPING_KEYS_ORDER.index(key)
    except Exception:
        return -1


async def write_json(path: Path, object: dict, type: str = None):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    if type:
        ignored_keys = settings.IGNORED_KEYS.get(type)
        if ignored_keys:
            for key in ignored_keys:
                if key in object:
                    del object[key]
    with open(path, "w") as wf:
        json.dump(object, wf, indent=2)


async def read_json(path: Path) -> dict:
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
            if lower and k.lower() in uppercase_fields:
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

            inbox = q.get("inbox", {})
            if inbox and (inbox_id := inbox.get("id", None)):
                sources["inboxes"].append(inbox_id)
                if inbox_target_id := q["inbox"]["target_object"]:
                    targets["inboxes"].append(inbox_target_id)

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
    pairs = {
        "workspaces": {},
        "queues": {},
        "inboxes": {},
        "schemas": {},
        "hooks": {},
    }

    for ws in mapping["organization"]["workspaces"]:
        pairs["workspaces"][ws["id"]] = ws.get("target_object", None)

        for q in ws["queues"]:
            pairs["queues"][q["id"]] = q.get("target_object", None)

            inbox = q.get("inbox", {})
            if inbox and (inbox_id := inbox.get("id", None)):
                pairs["inboxes"][inbox_id] = q["inbox"].get("target_object", None)

    for schema in mapping["organization"]["schemas"]:
        pairs["schemas"][schema["id"]] = schema.get("target_object", None)

    for hook in mapping["organization"]["hooks"]:
        pairs["hooks"][hook["id"]] = hook.get("target_object", None)

    return pairs


def extract_flat_lookup_table(mapping: dict) -> dict:
    pairs_by_type = extract_source_target_pairs(mapping)
    table = {}
    for pairs in pairs_by_type.values():
        table = {**table, **pairs}
    return table


def display_error(error_msg: str, exception: Exception):
    console = Console()
    logging.exception(exception)
    console.print(Panel(error_msg), style='bold red')


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
