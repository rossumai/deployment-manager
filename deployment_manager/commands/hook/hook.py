import click
from anyio import Path

from deployment_manager.commands.hook.payload import generate_and_save_hook_payload
from deployment_manager.commands.hook.sync.sync import sync_hook
from deployment_manager.commands.hook.sync.template import create_sync_template

from deployment_manager.commands.hook.test import test_hook
from deployment_manager.utils.consts import (
    settings,
)
from deployment_manager.utils.functions import (
    coro,
)


@click.group(
    name=settings.HOOK_COMMAND_NAME,
    help="Group of commands related to working with hooks",
)
def hook(): ...


@hook.command(
    name=settings.HOOK_PAYLOAD_COMMAND_NAME,
    help="""Create a payload for the hook under the specified path (JSON)""",
)
@click.argument(
    "hook-path",
    nargs=1,
    type=click.Path(path_type=Path, exists=True),
)
@click.option(
    "--annotation-url",
    "-au",
    help="URL of the annotation to create the payload with",
)
@coro
async def generate_hook_payload_wrapper(hook_path: Path, annotation_url: str = ""):
    await generate_and_save_hook_payload(
        hook_path=hook_path, annotation_url=annotation_url
    )


@hook.command(
    name=settings.HOOK_TEST_COMMAND_NAME,
    help="""Run the hook under the specified path (JSON)""",
)
@click.argument(
    "hook-path",
    nargs=1,
    type=click.Path(path_type=Path, exists=True),
)
@click.option(
    "--payload-path",
    "-pp",
    help="Path to hook payload (JSON) to test",
    type=click.Path(path_type=Path, exists=True),
)
@click.option(
    "--annotation-url",
    "-au",
    help="URL of the annotation to create the payload with",
)
@coro
async def test_hook_wrapper(
    hook_path: Path, payload_path: Path, annotation_url: str = ""
):
    await test_hook(
        hook_path=hook_path, payload_path=payload_path, annotation_url=annotation_url
    )


@hook.group(
    name=settings.HOOK_SYNC_COMMAND_NAME,
    help="Group of commands related to working with hook syncs",
)
def sync(): ...


@sync.command(
    name=settings.DEPLOY_TEMPLATE_COMMAND_NAME,
    help="""Create new template for hook sync"""
)
@coro
async def create_deploy_template_wrapper(
):
    await create_sync_template()


@sync.command(
    name=settings.DEPLOY_RUN_COMMAND_NAME,
    help="""Sync the local scripts with remote from ps-serverless-functions""",
)
@click.argument("sync_file", type=click.Path(path_type=Path, exists=True))
@coro
async def pull_hook_wrapper(
    sync_file: Path,
):
    await sync_hook(
        sync_file=sync_file,
    )
