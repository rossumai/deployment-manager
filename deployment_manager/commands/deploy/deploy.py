import click
from anyio import Path

from deployment_manager.commands.deploy.subcommands.revert.revert import (
    revert_release_file,
)
from deployment_manager.commands.deploy.subcommands.run.run import (
    deploy_release_file,
)

from deployment_manager.commands.deploy.subcommands.template.create import (
    create_deploy_template,
)

from deployment_manager.commands.deploy.subcommands.template.reverse import (
    DeployFileReverser,
)
from deployment_manager.utils.consts import (
    settings,
)
from deployment_manager.utils.functions import (
    coro,
)


@click.group(
    name=settings.DEPLOY_COMMAND_NAME,
    help="Group of commands related to deploying from source to target",
)
def deploy(): ...


@deploy.group(
    name=settings.DEPLOY_TEMPLATE_COMMAND_NAME,
    help=f"""Create/update/reverse a deploy file that can be used with the {settings.DEPLOY_COMMAND_NAME} command.""",
)
def template(): ...


@template.command(
    name=settings.DEPLOY_TEMPLATE_CREATE_COMMAND_NAME,
    help=f"""Create a deploy file that can be used with the {settings.DEPLOY_COMMAND_NAME} command.""",
)
@click.option(
    "--mapping-file",
    "-mf",
    help="PRD v1 mapping for reusing IDs and attribute overrides",
    type=click.Path(path_type=Path, exists=True),
)
@coro
async def create_deploy_template_wrapper(
    mapping_file: Path = None,
):
    await create_deploy_template(
        input_file_path=None,
        mapping_file_path=mapping_file,
        interactive=True,
    )


@template.command(
    name=settings.DEPLOY_TEMPLATE_UPDATE_COMMAND_NAME,
    help=f"""Update a deploy file that can be used with the {settings.DEPLOY_COMMAND_NAME} command.""",
)
@click.argument("deploy_file", type=click.Path(path_type=Path), required=True)
@click.option(
    "--interactive",
    "-i",
    help="Allows the user to change/add parts of the deploy file",
    is_flag=True,
    default=False,
)
@click.option(
    "--mapping-file",
    "-mf",
    help="PRD v1 mapping for reusing IDs and attribute overrides",
    type=click.Path(path_type=Path, exists=True),
)
@coro
async def create_deploy_template_wrapper(
    deploy_file: Path = None,
    interactive: bool = False,
    mapping_file: Path = None,
):
    await create_deploy_template(
        input_file_path=deploy_file,
        mapping_file_path=mapping_file,
        interactive=interactive,
    )


@template.command(
    name=settings.DEPLOY_TEMPLATE_REVERSE_COMMAND_NAME,
    help=f"""Create a deploy file that reverses source and target of an existing deploy file. Can be used for reverse {settings.MIGRATE_COMMAND_NAME}""",
)
@click.argument("deploy_file", type=click.Path(path_type=Path, exists=True))
@coro
async def reverse_deploy_template_wrapper(deploy_file: Path, project_path: Path = None):
    if not project_path:
        project_path = Path("./")

    reverser = DeployFileReverser(
        input_file_path=deploy_file,
        project_path=project_path,
    )

    await reverser.initialize()

    await reverser.reverse_deploy_file()


@deploy.command(
    name=settings.DEPLOY_RUN_COMMAND_NAME,
    help="""
Applies selected changes onto other objects based on the provided deploy.yaml file.
If these objects don't exist, they get created.
               """,
)
@click.argument("deploy_file", type=click.Path(path_type=Path, exists=True))
# @click.option(
#     "--auto-delete",
#     "-ad",
#     default=False,
#     is_flag=True,
#     help="Checks if source object exists and if not, deletes target + removes the object from deploy file.",
# )
@click.option(
    "--prefer",
    type=click.Choice(
        [settings.SOURCE_DIRNAME, settings.TARGET_DIRNAME], case_sensitive=False
    ),
    default=None,
    help=f"When resolving merge conflicts, prefer {settings.SOURCE_DIRNAME} or {settings.TARGET_DIRNAME} values. If unset, neither is preferred and conflicts will be raised.",
)
@click.option(
    "--no-rebase",
    default=False,
    is_flag=True,
    help="Does not ask user about any rebase from target.",
)
@click.option(
    "--auto-apply",
    "-y",
    default=False,
    is_flag=True,
    help="Does not ask user for confirmation of the plan - applies it blindly.",
)
@click.option(
    "--commit",
    "-c",
    default=False,
    is_flag=True,
    help="Commits the changes automatically.",
)
@click.option(
    "--message",
    "-m",
    default="Deployed changes to target organization",
    help="Commit message.",
)
@coro
async def deploy_project_wrapper(
    deploy_file: Path,
    # auto_delete: bool,
    auto_apply: bool,
    commit: bool,
    message: str,
    prefer: str = None,
    no_rebase: bool = False,
):
    if prefer:
        prefer = prefer.lower()  # Normalize input
    else:
        prefer = "neither"

    await deploy_release_file(
        deploy_file_path=deploy_file,
        prefer=prefer,
        no_rebase=no_rebase,
        # auto_delete=auto_delete,
        auto_apply_plan=auto_apply,
        commit=commit,
        commit_message=message,
    )


@deploy.command(
    name=settings.DEPLOY_REVERT_COMMAND_NAME,
    help="""
Reverts the deploy by deleting all target objects found in the provided deploy file               """,
)
@click.argument("deploy_file", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--commit",
    "-c",
    default=False,
    is_flag=True,
    help="Commits the changes automatically.",
)
@click.option(
    "--message",
    "-m",
    default="Reverted changes in target organization",
    help="Commit message.",
)
@coro
async def revert_project_wrapper(
    deploy_file: Path,
    commit: bool,
    message: str,
):
    await revert_release_file(
        deploy_file_path=deploy_file,
        commit=commit,
        commit_message=message,
    )
