import asyncio
from functools import wraps
import dataclasses
import json
from typing import Any
from anyio import Path

import yaml

from project_rossum_deploy.utils.consts import settings


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def templatize_name_id(name, id):
    return f"{name}_[{id}]"


def detemplatize_name_id(joint_name: str) -> tuple[str, int]:
    parts = joint_name.split("_")
    return parts[0], int(parts[1].removeprefix("[").removesuffix("]"))


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


def adjust_keys(object: Any, lower: bool = True):
    if isinstance(object, dict):
        lowercased = {}
        for k, v in object.items():
            new_key = k
            if lower:
                new_key = k.lower()
            elif not lower and k in settings.MAPPING_UPPERCASE_FIELDS:
                new_key = k.upper()
            lowercased[new_key] = adjust_keys(v, lower)
        return lowercased
    elif isinstance(object, list):
        lowercased = []
        for v in object:
            lowercased.append(adjust_keys(v, lower))
        return lowercased
    else:
        return object

async def retrieve_with_progress(retrieve, progress, task):
    result = await retrieve()
    progress.update(task, advance=1)
    return result