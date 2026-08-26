import importlib.metadata

import click

from deployment_manager.commands.deploy.deploy import deploy
from deployment_manager.commands.document.document import generate_documentation_wrapper
from deployment_manager.commands.download.download import download_project_wrapper
from deployment_manager.commands.hook.hook import hook
from deployment_manager.commands.initialize import init_project
from deployment_manager.commands.llm_chat.llm_chat import llm_chat_wrapper
from deployment_manager.commands.purge.purge import purge_object_types_wrapper
from deployment_manager.commands.update import (
    notify_if_new_version_available,
    update_application,
)
from deployment_manager.commands.upload.upload import upload_project_wrapper
from deployment_manager.utils.consts import settings


@click.group(context_settings={"max_content_width": 120})
@click.version_option(version=importlib.metadata.version("deployment-manager"))
@click.pass_context
def main(ctx):
    # Let the user know if a newer release is available, skip for the update command itself
    if ctx.invoked_subcommand != settings.UPDATE_COMMAND_NAME:
        notify_if_new_version_available()


main.add_command(download_project_wrapper)
main.add_command(init_project)
main.add_command(deploy)
main.add_command(hook)
main.add_command(generate_documentation_wrapper)
main.add_command(llm_chat_wrapper)
main.add_command(purge_object_types_wrapper)
main.add_command(upload_project_wrapper)
main.add_command(update_application)

# For debugging purposes
if __name__ == "__main__":
    main()
