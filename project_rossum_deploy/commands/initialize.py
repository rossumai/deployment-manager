import os
from pathlib import Path
import shutil
import subprocess

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
@click.argument("name")
def init_project(name):
    if not os.path.exists(name):
        os.mkdir(name)
    else:
        click.echo(f'Directory "{name}" already exists, skipping.')
        return

    with open(name + "/.gitignore", "w") as wf:
        wf.write(".env")
    env_example_path = Path(__file__).parent.parent.parent / '.env.example'
    shutil.copyfile(env_example_path, name + '/.env')

    os.chdir(name)
    subprocess.run(['git', 'init'])

    click.echo(f'Initialized a new directory "{name}".')
