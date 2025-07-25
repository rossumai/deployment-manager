import importlib.metadata
import click

from deployment_manager.commands.deploy.deploy import deploy
from deployment_manager.commands.hook.hook import hook
from deployment_manager.commands.download.download import (
    download_project_wrapper,
)
from deployment_manager.commands.initialize import init_project
from deployment_manager.commands.purge.purge import purge_object_types_wrapper
from deployment_manager.commands.upload.upload import upload_project_wrapper
from deployment_manager.commands.update import update_application


@click.group(context_settings={"max_content_width": 120})
@click.version_option(version=importlib.metadata.version("deployment-manager"))
def main(): ...


main.add_command(download_project_wrapper)
main.add_command(init_project)
main.add_command(deploy)
main.add_command(hook)
main.add_command(purge_object_types_wrapper)
main.add_command(upload_project_wrapper)
main.add_command(update_application)

# For debugging purposes
if __name__ == "__main__":
    main()
