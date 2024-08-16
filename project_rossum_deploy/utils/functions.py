import asyncio
from functools import wraps
import re
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

    if str(path.stem) in ["queue", "workspace", "inbox"]:
        parts = path.parent.name.split("_")
        return "_".join(parts[:-1]), int(parts[-1].removeprefix("[").removesuffix("]"))
    elif str(path.parent.stem) in ["hooks", "schemas", "email_templates"]:
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


async def gather_with_concurrency(n, *coros):
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))


async def find_object_in_project(object: dict, base_path: Path):
    file_name = templatize_name_id(object["name"], object["id"])
    return (
        await (base_path / file_name).exists()
        or await (base_path / (file_name + ".json")).exists()
    )


def find_object_by_key(key: str, value: str, objects: list):
    object = None
    for candidate in objects:
        if candidate[key] == value:
            object = candidate
            break
    return object


def find_object_by_id(id: int, objects: list):
    return find_object_by_key(key="id", value=id, objects=objects)
