from pydantic import HttpUrl, ValidationError
import questionary
from rossum_api import APIClientError, ElisAPIClient
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from deployment_manager.common.read_write import (
    read_prd_cred_file,
    read_prd_project_config,
)
from deployment_manager.utils.consts import display_error, settings


from anyio import Path


async def get_api_url_from_config(base_path: Path, org_name: str):
    try:
        config_data = await read_prd_project_config(base_path)
        if not config_data:
            return ""

        return (
            config_data.get(settings.CONFIG_KEY_DIRECTORIES, {})
            .get(org_name, {})
            .get(settings.CONFIG_KEY_API_BASE_URL, "")
        )
    except Exception:
        ...

    return ""


async def get_token_from_cred_file(org_path: Path):
    credentials_path: Path = org_path / settings.CREDENTIALS_FILENAME
    if await credentials_path.exists():
        try:
            cred_data = await read_prd_cred_file(org_path)
            if not cred_data:
                return ""
            return cred_data.get(settings.CONFIG_KEY_TOKEN, "")
        except Exception:
            ...
    return ""


async def get_api_url_from_user(type: str = "Rossum", default: str = ""):
    if default is None:
        default = ""
    api_url = await questionary.text(
        f"What is the {type} API URL (e.g., {settings.DEPLOY_DEFAULT_TARGET_URL}):",
        default=default,
    ).ask_async()

    try:
        HttpUrl(api_url)
    except ValidationError:
        display_error(f"Invalid {type} URL provided: {api_url}. Please retry.")
        return await get_api_url_from_user(type=type, default=default)

    return api_url


async def get_token_from_user(type: str = "Rossum"):
    return await questionary.text(f"Enter token for the {type} API:").ask_async()


async def validate_credentials(credentials: Credentials):
    if not credentials.url:
        raise Exception(f"No {settings.CONFIG_KEY_API_BASE_URL} in credentials")
    elif not credentials.token:
        raise Exception(f"No {settings.CONFIG_KEY_TOKEN} in credentials")

    try:
        await ElisAPIClient(base_url=credentials.url, token=credentials.token).request(
            "get", "auth/user"
        )
    except APIClientError as e:
        if e.status_code == 401:
            raise Exception(
                f'Invalid API token "{credentials.token}" for URL "{credentials.url}"'
            )

        raise e


# TODO: likely duplicated in another file
async def get_filename_from_user(org_path: Path, default: str = ""):
    deploy_filename: str = await questionary.text(
        "Name for the deploy file:",
        default=default,
    ).ask_async()
    deploy_filepath = org_path / deploy_filename

    if await deploy_filepath.exists():
        overwrite = await questionary.confirm(
            f'File "{deploy_filepath}" already exists. Overwrite?', default=False
        ).ask_async()
        if not overwrite:
            return await get_filename_from_user(org_path)

    return deploy_filepath
