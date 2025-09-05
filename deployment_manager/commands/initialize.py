from copy import deepcopy
import os
from anyio import Path
import subprocess
import questionary
from rich import print
from rich.panel import Panel

import click

from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.utils.consts import settings
from deployment_manager.utils.functions import coro


@click.command(
    name=settings.INITIALIZE_COMMAND_NAME,
    help="""
Creates a new project directory with the specified name with basic files.
Also initializes it as a git repository.
               """,
)
@click.argument("name", default=".", type=click.Path(path_type=Path, exists=False))
@coro
async def init_project(name: Path):
    if not await name.exists() and name != ".":
        os.mkdir(name)

    # (re)initialize GIT
    subprocess.run(["git", "init", name])

    git_ignore_path = name / ".gitignore"
    credentials_ignore_lines = [
        "\n**/credentials.json",
        f"\n**/{settings.CREDENTIALS_FILENAME}",
        f"\n**/{settings.DEFAULT_DEPLOY_SECRETS_PARENT}/",
        f"\n**/**/{settings.NON_VERSIONED_ATTRIBUTES_FILE_NAME}",
        f"\n**/{settings.DEFAULT_HOOK_SYNC_PARENT}/"
    ]

    git_ignore_contents = (
        await git_ignore_path.read_text() if await git_ignore_path.exists() else ""
    )

    with open(name / ".gitignore", "a") as wf:
        for ignore_line in credentials_ignore_lines:
            if ignore_line not in git_ignore_contents:
                wf.write(ignore_line)

    config_path = name / settings.CONFIG_FILENAME
    if await config_path.exists():
        previous_config = await config_path.read_text()
    else:
        previous_config = "{}"
    config = DeployYaml(previous_config)
    if settings.CONFIG_KEY_DIRECTORIES not in config.data:
        config.data[settings.CONFIG_KEY_DIRECTORIES] = {}
    directories = config.data[settings.CONFIG_KEY_DIRECTORIES]
    previous_directories = deepcopy(directories)
    credentials = {}

    while (
        not len(directories)
        or await questionary.confirm(
            "Would you like to specify another **ORG-LEVEL** directory?"
        ).ask_async()
    ):
        org_dir_name = await questionary.text("ORG-LEVEL directory name:").ask_async()
        org_id = await questionary.text("ORG ID:").ask_async()
        api_base_url = await questionary.text(
            f"Base API URL: (e.g., {settings.DEPLOY_DEFAULT_TARGET_URL})"
        ).ask_async()
        token = await questionary.text("API token:").ask_async()
        directories[org_dir_name] = {
            settings.DOWNLOAD_KEY_ORG_ID: org_id,
            settings.CONFIG_KEY_API_BASE_URL: api_base_url,
            settings.CONFIG_KEY_SUBDIRECTORIES: {},
        }
        credentials[org_dir_name] = token
        await add_subdirs(directories=directories, org_dir_name=org_dir_name)

    # Add subdirs to already existing directories
    if previous_directories:
        for org_dir_name in previous_directories.keys():
            await add_subdirs(directories=directories, org_dir_name=org_dir_name)

    await config.save_to_file(config_path)

    for org_dir in directories.keys():
        for subdir in directories[org_dir][settings.CONFIG_KEY_SUBDIRECTORIES].keys():
            os.makedirs(name / org_dir / subdir, exist_ok=True)

    for org_dir, token in credentials.items():
        credentials_yaml = DeployYaml("{}")
        credentials_yaml.data = {settings.CONFIG_KEY_TOKEN: token}
        await credentials_yaml.save_to_file(
            name / org_dir / settings.CREDENTIALS_FILENAME
        )

    print(Panel(f'Initialized a new PRD directory in "{name}"'))


async def add_subdirs(directories: dict, org_dir_name: str):
    subdirs = directories[org_dir_name][settings.CONFIG_KEY_SUBDIRECTORIES]
    while (
        not len(subdirs)
        or await questionary.confirm(
            f"Would you like to specify another **SUBDIR** inside {org_dir_name}?"
        ).ask_async()
    ):
        subdir_name = await questionary.text("SUBDIR name:").ask_async()
        subdir_regex = await questionary.text("subdir regex (OPTIONAL):").ask_async()
        subdirs[subdir_name] = {settings.DOWNLOAD_KEY_REGEX: subdir_regex}
