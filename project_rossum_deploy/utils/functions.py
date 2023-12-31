import asyncio
from functools import wraps
import dataclasses
import json
from anyio import Path

import yaml

def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper

def templatize_name_id(name, id):
    return f'{name}_[{id}]'

def detemplatize_name_id(joint_name: str) -> tuple[str, int]:
    parts = joint_name.split('_')
    return parts[0], int(parts[1].removeprefix('[').removesuffix(']'))

async def write_json(path: Path, object: dict):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    if path.parent:
        await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        json.dump(object, wf)

async def write_yaml(path: Path, object: dict):
    if dataclasses.is_dataclass(object):
        object = dataclasses.asdict(object)
    await path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as wf:
        yaml.dump(object, wf)

def read_yaml(path: Path):
    with open(path, "r") as rf:
        return yaml.safe_load(rf)
