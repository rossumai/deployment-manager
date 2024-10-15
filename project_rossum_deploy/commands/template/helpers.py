from project_rossum_deploy.common.read_write import read_json


import questionary
from anyio import Path


async def prepare_choices(paths: list[Path], preselect: bool = False):
    choices = []

    for path in paths:
        object = await read_json(path)
        name, id = object.get("name", ""), object.get("id", "")
        if not id:
            continue
        choice = questionary.Choice(
            title=f"{name} [{id}]" if name else id,
            value={**object, "path": path},
            checked=preselect,
        )
        choices.append(choice)

    return choices
