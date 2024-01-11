from anyio import Path
from project_rossum_deploy.commands.download.mapping import read_mapping, write_mapping
from project_rossum_deploy.utils.consts import settings


async def create_self_targetting_org(tmp_path: Path, undo=False):
    mapping = await read_mapping(tmp_path / settings.MAPPING_FILENAME)
    mapping["organization"]["target"] = None if undo else mapping["organization"]["id"]
    await write_mapping(tmp_path / settings.MAPPING_FILENAME, mapping)
