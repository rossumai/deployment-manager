import subprocess

import click

from project_rossum_deploy.utils.consts import settings

PRD_GIT_URL = "https://raw.githubusercontent.com/rossumai/prd/main/install.sh"


@click.command(
    name=settings.UPDATE_COMMAND_NAME,
    help="""Updates the PRD command to the latest version.""",
)
def update_prd():
    script = subprocess.run(
        ["curl", "-fsSL", PRD_GIT_URL], capture_output=True
    ).stdout.decode()
    subprocess.run([script], shell=True)
