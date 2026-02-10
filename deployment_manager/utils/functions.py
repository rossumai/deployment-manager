import asyncio
import re
from functools import wraps
from typing import Any

from anyio import Path
from click import progressbar


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


FORBIDDEN_CHARS_REGEX = re.compile(r"[/\\\"\'\`]")


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


def templatize_name_id(name: str, id: int):
    return f"{re.sub(FORBIDDEN_CHARS_REGEX, '', name)}_[{id}]"


def detemplatize_name_id(path: Path | str) -> tuple[str, int]:
    if isinstance(path, str):
        parts = path.split("_")
        return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))

    if str(path.stem) in ["queue", "workspace", "inbox", "schema"]:
        parts = path.parent.name.split("_")
        return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))
    elif str(path.parent.stem) in ["hooks", "email_templates"]:
        parts = path.stem.split("_")
        return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))


def extract_id_from_url(url: str) -> int:
    if not url:
        return None
    return int(url.split("/")[-1])


async def make_request_with_progress(coro, progress, task):
    result = await coro
    progress.update(task, advance=1)
    return result


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


def apply_concurrency_override(concurrency: int | None):
    """Override the global concurrency setting if a value is provided.

    Args:
        concurrency: The concurrency limit to apply, or None to use existing setting
    """
    if concurrency is not None:
        from deployment_manager.utils.consts import settings

        if settings:
            settings.CONCURRENCY = concurrency


async def gather_with_concurrency(*coros, n=None):
    # Determine concurrency limit: CLI flag > env var > default 5
    if n is None:
        from deployment_manager.utils.consts import settings

        n = settings.CONCURRENCY if settings else 5

    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))


async def find_object_in_project(object: dict, base_path: Path):
    file_name = templatize_name_id(object["name"], object["id"])
    return await (base_path / file_name).exists() or await (base_path / (file_name + ".json")).exists()


def find_object_by_key(key: str, value: str, objects: list):
    object = None
    for candidate in objects:
        if candidate[key] == value:
            object = candidate
            break
    return object


def find_object_by_id(id: int, objects: list):
    return find_object_by_key(key="id", value=id, objects=objects)


async def find_all_hook_paths_in_destination(destination_path: Path):
    hooks_dir = destination_path / "hooks"
    if not (await hooks_dir.exists()):
        return []
    return [
        hook_path
        async for hook_path in hooks_dir.iterdir()
        if await hook_path.is_file() and hook_path.suffix == ".json"
    ]


async def find_all_schema_paths_in_destination(destination_path: Path):
    schemas_dir = destination_path / "schemas"
    if not (await schemas_dir.exists()):
        return []

    return [schema_path async for schema_path in schemas_dir.iterdir() if await schema_path.is_file()]

def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default
