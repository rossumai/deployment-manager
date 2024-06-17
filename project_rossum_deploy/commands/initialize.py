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
@click.argument(
    "name",
    default=".",
)
def init_project(name):
    if os.path.exists(name) and name != ".":
        print(Panel(f'Directory "{name}" already exists, skipping.'))
        return

    credentials_path = name + "/credentials.json"
    if os.path.exists(credentials_path):
        print(Panel(f'"{credentials_path}" already exists, skipping.'))
        return

    if not os.path.exists(name) and name != ".":
        os.mkdir(name)

        os.chdir(name)
        subprocess.run(["git", "init"])
        os.chdir('..')

    with open(name + "/.gitignore", "a") as wf:
        wf.write("\ncredentials.json")
    example_credentials_path = Path(__file__).parent.parent / "dummy_credentials.json"

    shutil.copyfile(example_credentials_path, credentials_path)

    print(Panel(f'Initialized a new directory in "{name}" .'))
