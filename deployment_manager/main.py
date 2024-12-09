import click

from deployment_manager.commands.deploy.deploy import deploy
from deployment_manager.commands.update import update_prd
from deployment_manager.commands.download.download import (
    download_project_wrapper,
)
from deployment_manager.commands.initialize import init_project
from deployment_manager.commands.migrate_mapping import migrate_mapping_wrapper
from deployment_manager.commands.purge.purge import purge_object_types_wrapper
from deployment_manager.commands.upload.upload import upload_project_wrapper


@click.group()
@click.version_option()
def main(): ...


main.add_command(download_project_wrapper)
main.add_command(init_project)
main.add_command(migrate_mapping_wrapper)
main.add_command(deploy)
main.add_command(purge_object_types_wrapper)
main.add_command(upload_project_wrapper)
main.add_command(update_prd)

# For debugging purposes
if __name__ == "__main__":
    main()
