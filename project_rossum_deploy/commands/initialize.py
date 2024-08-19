import os
from pathlib import Path
import shutil
import subprocess
from rich import print
from rich.panel import Panel

import click

from project_rossum_deploy.utils.consts import settings


@click.command(
    name=settings.INITIALIZE_COMMAND_NAME,
    help="""
Creates a new project directory with the specified name with basic files.
Also initializes it as a git repository.
The user is then expected to provide .env credentials and download Rossum objects.
               """,
)
@click.argument("name", default=".", type=click.Path(path_type=Path))
def init_project(name: Path):
    if not os.path.exists(name) and name != ".":
        os.mkdir(name)

    # (re)initialize GIT
    subprocess.run(["git", "init", name])

    git_ignore_path = name / ".gitignore"
    credentials_ignore_line = "\ncredentials.json"

    git_ignore_contents = git_ignore_path.read_text()

    if credentials_ignore_line not in git_ignore_contents:
        with open(name + "/.gitignore", "a") as wf:
            wf.write(credentials_ignore_line)

    credentials_path = name / "credentials.json"
    copy_dummy_credentials_file(credentials_path)

    config_path = name / "prd_config.yaml"
    copy_dummy_config_file(config_path)

    print(Panel(f'Initialized a new PRD directory in "{name}" .'))


def copy_dummy_credentials_file(destination: Path):
    if not os.path.exists(destination):
        example_credentials_path = (
            Path(__file__).parent.parent / "dummy_credentials.json"
        )
        shutil.copyfile(example_credentials_path, destination)


def copy_dummy_config_file(destination: Path):
    if not os.path.exists(destination):
        example_config_path = Path(__file__).parent.parent / "dummy_config.yaml"
        shutil.copyfile(example_config_path, destination)
