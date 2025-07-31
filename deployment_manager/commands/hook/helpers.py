from anyio import Path
import re

from deployment_manager.common.read_write import read_object_from_json
from deployment_manager.utils.consts import display_error


async def load_hook_object(hook_path: Path):
    try:
        if hook_path.suffix != ".json":
            raise Exception(f"Incorrect suffix for {hook_path}")
        return await read_object_from_json(hook_path)
    except Exception as e:
        display_error(f"Error while loading hook with path {hook_path}: {e}")


def get_project_path_from_hook_path(hook_path: Path):
    # project_path / org-dir / subdir / hooks / hook.json
    return hook_path.parent.parent.parent.parent


def get_org_name_from_hook_path(hook_path: Path):
    # project_path / org-dir / subdir / hooks / hook.json
    return hook_path.parent.parent.parent.stem


def get_annotation_id_from_frontend_url(url: str):
    match = re.search(r"/document/(\d+)", url)

    if match:
        return match.group(1)

    return ""
