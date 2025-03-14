from pydantic import HttpUrl, ValidationError
import questionary
from rossum_api import APIClientError, ElisAPIClient
from deployment_manager.commands.deploy.subcommands.run.upload_helpers import (
    Credentials,
)
from deployment_manager.common.read_write import (
    read_prd_cred_file,
    read_prd_project_config,
    write_prd_cred_file,
)
from deployment_manager.utils.consts import display_error, settings
from anyio import Path


from rossum_api.models.user import User
from rossum_api.models.group import Group


class InvalidCredentialsException(Exception): ...


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


async def get_directory_from_config(base_path: Path, org_name: str):
    try:
        config_data = await read_prd_project_config(base_path)
        if not config_data:
            return ""

        return config_data.get(settings.CONFIG_KEY_DIRECTORIES, {}).get(org_name, {})
    except Exception:
        ...

    return None


async def get_org_id_from_config(base_path: Path, org_name: str):
    try:
        config_data = await read_prd_project_config(base_path)
        if not config_data:
            return ""

        return int(
            config_data.get(settings.CONFIG_KEY_DIRECTORIES, {})
            .get(org_name, {})
            .get(settings.CONFIG_KEY_ORG_ID, "")
        )
    except Exception:
        ...

    return None


async def get_token_from_cred_file(org_path: Path, api_url: str):
    credentials_path: Path = org_path / settings.CREDENTIALS_FILENAME
    if not (await credentials_path.exists()):
        return ""

    try:
        cred_data = await read_prd_cred_file(org_path)
        if not cred_data:
            return ""

        token = cred_data.get(settings.CONFIG_KEY_TOKEN, "")
        await validate_credentials(Credentials(token=token, url=api_url))
        return token
    except InvalidCredentialsException:
        display_error(f"Token for {org_path} is invalid or expired.")
        new_token = await get_token_from_user(name=org_path)
        await validate_credentials(Credentials(token=new_token, url=api_url))
        await write_prd_cred_file(org_path, {settings.CONFIG_KEY_TOKEN: new_token})
        return new_token
    except Exception:
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


async def get_token_from_user(name: str = "Rossum"):
    return await questionary.text(f"Enter token for the {name} API:").ask_async()


def is_user_admin(user: User, user_roles: list[Group]):
    admin_urls = [
        role.url
        for role in user_roles
        if role.name in ["admin", "organization_group_admin"]
    ]
    for user_role_url in user.groups:
        if user_role_url in admin_urls:
            return True
    return False


async def get_token_owner_from_user(client: ElisAPIClient):
    users = [user async for user in client.list_all_users()]
    user_roles = [role async for role in client.list_all_user_roles()]
    user_choices = [
        questionary.Choice(title=user.username, value=user.id)
        for user in users
        if is_user_admin(user=user, user_roles=user_roles)
    ]
    token_owner_id = await questionary.select(
        "Please choose target hook token owner:", choices=user_choices
    ).ask_async()

    return token_owner_id


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
            raise InvalidCredentialsException(
                f'Invalid API token "{credentials.token}" for URL "{credentials.url}"'
            )

        raise e


# TODO: likely duplicated in another file
