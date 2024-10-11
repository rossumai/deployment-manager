import subprocess

import click

from project_rossum_deploy.utils.consts import settings

PRD_GIT_URL = "https://raw.githubusercontent.com/rossumai/prd/main/install.sh"


@click.command(
    name=settings.UPDATE_COMMAND_NAME,
    help="""Updates the PRD command to the latest version.""",
)
@click.option("--branch", help="GIT branch name other than the default one")
def update_prd(branch: str = ""):
    script = subprocess.run(
        ["curl", "-fsSL", PRD_GIT_URL], capture_output=True
    ).stdout.decode()

    script = f"BRANCH={branch}\n" + script
    subprocess.run([script], shell=True)
