import subprocess

import click

from project_rossum_deploy.utils.consts import settings

PRD_GIT_URL = "https://github.com/rossumai/prd/blob/main/install.sh"


@click.command(
    name=settings.UPDATE_COMMAND_NAME,
    help="""Updates the PRD command to the latest version.""",
)
def update_prd():
    subprocess.run(["sh", "-c", f"$(curl -fsSL {PRD_GIT_URL})"])
