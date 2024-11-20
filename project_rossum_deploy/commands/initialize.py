import os
from pathlib import Path
import subprocess
import questionary
from rich import print
from rich.panel import Panel

import click

from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.utils.consts import settings


@click.command(
    name=settings.INITIALIZE_COMMAND_NAME,
    help="""
Creates a new project directory with the specified name with basic files.
Also initializes it as a git repository.
               """,
)
@click.argument("name", default=".", type=click.Path(path_type=Path, exists=False))
def init_project(name: Path):
    if not os.path.exists(name) and name != ".":
        os.mkdir(name)

    # (re)initialize GIT
    subprocess.run(["git", "init", name])

    git_ignore_path = name / ".gitignore"
    credentials_ignore_lines = ["\n**/credentials.json", "\n**/credentials.yaml"]

    git_ignore_contents = (
        git_ignore_path.read_text() if git_ignore_path.exists() else ""
    )

    with open(name / ".gitignore", "a") as wf:
        for ignore_line in credentials_ignore_lines:
            if ignore_line not in git_ignore_contents:
                wf.write(ignore_line)

    config_path = name / settings.CONFIG_FILENAME
    if config_path.exists():
        previous_config = config_path.read_text()
    else:
        previous_config = "{}"
    config = DeployYaml(previous_config)
    if settings.CONFIG_KEY_DIRECTORIES not in config.data:
        config.data[settings.CONFIG_KEY_DIRECTORIES] = {}
    directories = config.data[settings.CONFIG_KEY_DIRECTORIES]
    credentials = {}

    while questionary.confirm(
        "Would you like to specify a(nother) org-level directory?"
    ).ask():
        org_dir_name = questionary.text("org-level directory name:").ask()
        org_id = questionary.text("ORG ID:").ask()
        api_base_url = questionary.text(
            f"Base API URL: (e.g., {settings.DEPLOY_DEFAULT_TARGET_URL})"
        ).ask()
        token = questionary.text("API token:").ask()
        directories[org_dir_name] = {
            settings.DOWNLOAD_KEY_ORG_ID: org_id,
            settings.CONFIG_KEY_API_BASE_URL: api_base_url,
            settings.CONFIG_KEY_SUBDIRECTORIES: {},
        }
        credentials[org_dir_name] = token
        while questionary.confirm(
            f"Would you like to specify a(nother) subdirectory inside {org_dir_name}?"
        ).ask():
            subdir_name = questionary.text("subdir name:").ask()
            subdir_regex = questionary.text("subdir regex:").ask()
            directories[org_dir_name][settings.CONFIG_KEY_SUBDIRECTORIES][
                subdir_name
            ] = {settings.DOWNLOAD_KEY_REGEX: subdir_regex}

    config.save_to_file(config_path)

    for org_dir in directories.keys():
        os.mkdir(name / org_dir)
        for subdir in directories[org_dir][settings.CONFIG_KEY_SUBDIRECTORIES].keys():
            os.mkdir(name / org_dir / subdir)

    for org_dir, token in credentials.items():
        credentials_yaml = DeployYaml("{}")
        credentials_yaml.data = {settings.CONFIG_KEY_TOKEN: token}
        credentials_yaml.save_to_file(name / org_dir / settings.CREDENTIALS_FILENAME)

    print(Panel(f'Initialized a new PRD directory in "{name}" .'))
