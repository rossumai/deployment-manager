import importlib
import sys

import httpx
import subprocess
import questionary

import click

from packaging.version import parse as parse_version
from deployment_manager.utils.consts import settings, display_info, display_error
from deployment_manager.utils.functions import coro


@click.command(
    name=settings.UPDATE_COMMAND_NAME,
    help="""
Updates deployment-manager with the lastest version from github
               """,
)
@coro
async def update_application():
    latest_whl_url, latest_version = await get_latest_version()

    if not latest_whl_url or not latest_version:
        display_error(f"No latest version found in github repository. (Found url: {latest_whl_url}, version: {latest_version})")
        return

    current_version = parse_version(importlib.metadata.version("deployment-manager"))
    latest_version = parse_version(latest_version)

    if str(current_version) == "0.0.0" or current_version.is_devrelease:
        # 0.0.0 if installed via poetry, is_devrelease==True if pip is used
        if not await questionary.confirm(
            f"You probably installed deployment-manager project locally from source. Do you really want to update to a latest release {latest_version}?",
            default=False,
        ).ask_async():
            return
    elif current_version == latest_version:
        if not await questionary.confirm(
            f"You currently have the latest version installed ({current_version}). Do you want it to reinstall?",
            default=False,
        ).ask_async():
            return
    elif current_version > latest_version:
        if not await questionary.confirm(
            f"You currently have newer version installed ({current_version}) then the latest release available to download ({latest_version}). Do you want to install {latest_version}?",
            default=False,
        ).ask_async():
            return

    install_command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--no-cache-dir",
        latest_whl_url,
    ]

    try:
        subprocess.run(install_command, check=True, capture_output=True, text=True)
        display_info(
            f"Deployment manager successfully updated to latest version: {latest_version}"
        )
    except Exception as e:
        display_error(
            f"Deployment manager update to a version {latest_version} unsuccessful: {e}",
            e,
        )


async def get_latest_version() -> tuple[str | None, str | None]:
    repo_owner = settings.GITHUB_DEPLOYMENT_MANAGER_REPO_OWNER
    repo_name = settings.GITHUB_DEPLOYMENT_MANAGER_REPO_NAME
    api_url = settings.GITHUB_DEFAULT_LATEST_RELEASE_URL.format(
        repo_owner=repo_owner, repo_name=repo_name
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        if response.status_code != httpx.codes.OK:
            display_error(
                f"Github API request failed with status code {response.status_code}"
            )
            return None, None
        release_info = response.json()
        latest_version_str = release_info.get("tag_name", "").lstrip("vV")

        for asset in release_info.get("assets", []):
            if asset["name"].endswith(".whl"):
                return asset["browser_download_url"], latest_version_str
    return None, None
