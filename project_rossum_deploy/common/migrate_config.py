from anyio import Path

from project_rossum_deploy.common.read_write import read_json, write_yaml
from project_rossum_deploy.utils.consts import settings


async def migrate_config():
    config_path = Path("./") / settings.CONFIG_FILENAME

    if await config_path.exists():
        return

    credentials_path = Path("./") / settings.CREDENTIALS_FILENAME
    if not await credentials_path.exists():
        return

    credentials = await read_json(credentials_path)

    config = {
        "source_api_base": credentials.get("source", {}).get("api_base", ""),
        "use_same_org_as_target": credentials.get("use_same_org_as_target", True),
        "target_api_base": credentials.get("target", {}).get("api_base", ""),
    }

    await write_yaml(config_path, config)
