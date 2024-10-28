import click
from anyio import Path

from project_rossum_deploy.commands.deploy.subcommands.run.run import (
    deploy_release_file,
)

from project_rossum_deploy.commands.deploy.subcommands.template.create import (
    create_deploy_template,
)
from project_rossum_deploy.commands.deploy.subcommands.template.init import (
    init_deploy_template_file,
)
from project_rossum_deploy.utils.consts import (
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
)


@click.group(
    name=settings.DEPLOY_COMMAND_NAME,
    help="Group of commands related to deploying from source to target",
)
def deploy(): ...


@deploy.command(
    name=settings.DEPLOY_TEMPLATE_INIT_COMMAND_NAME,
    help=f"""Create an empty deploy file that can be used with the {settings.DEPLOY_COMMAND_NAME} command.""",
)
@coro
async def init_deploy_template_wrapper():
    await init_deploy_template_file()


@deploy.command(
    name=settings.DEPLOY_TEMPLATE_COMMAND_NAME,
    help=f"""Create a deploy file that can be used with the {settings.DEPLOY_COMMAND_NAME} command.""",
)
@click.option(
    "--deploy-file",
    "-f",
    help="Previous deploy file to speed up deploy file creation",
    type=click.Path(path_type=Path, exists=True),
)
@click.option(
    "--interactive",
    "-i",
    help="Allows the user to change/add parts of the deploy file",
    is_flag=True,
    default=False,
)
@coro
async def create_deploy_template_wrapper(
    deploy_file: Path = None, interactive: bool = False
):
    await create_deploy_template(input_file=deploy_file, interactive=interactive)


@deploy.command(
    name=settings.DEPLOY_RUN_COMMAND_NAME,
    help="""
Applies selected changes onto other objects based on the provided deploy.yaml file.
If these objects don't exist, they get created.
               """,
)
@click.argument("deploy_file", type=click.Path(path_type=Path, exists=True))
# @click.option(
#     "--force",
#     "-f",
#     default=False,
#     is_flag=True,
#     help="Ignores newer remote timestamps = overwrites remote with local version of objects.",
# )
# @click.option(
#     "--commit",
#     "-c",
#     default=False,
#     is_flag=True,
#     help="Commits the pushed changes automatically.",
# )
# @click.option(
#     "--message",
#     "-m",
#     default="Released changes to target organization",
#     help="Commit message for pulling.",
# )
@coro
async def deploy_project_wrapper(
    deploy_file: Path,
    # force: bool,
    # commit: bool,
    # message: str,
):
    await deploy_release_file(
        deploy_file_path=deploy_file,
        # force=force,
        # commit=commit,
        # commit_message=message,
    )
