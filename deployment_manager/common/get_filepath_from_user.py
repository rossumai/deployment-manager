import questionary
from anyio import Path


async def get_filepath_from_user(
    project_path: Path, default: str = "", default_text="Name for the output file:", should_confirm_overwrite: bool = True
):
    filename: str = await questionary.text(
        default_text,
        default=default,
    ).ask_async()
    filepath = project_path / filename

    if await filepath.exists() and should_confirm_overwrite:
        overwrite = await questionary.confirm(
            f'File "{filepath}" already exists. Overwrite?', default=False
        ).ask_async()
        if not overwrite:
            return await get_filepath_from_user(project_path)

    return filepath
