import click

from project_rossum_deploy.commands.download.download import (
    download_project_wrapper,
)
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate.migrate import migrate_project_wrapper
from project_rossum_deploy.commands.migrate_mapping import migrate_mapping_wrapper
from project_rossum_deploy.commands.purge.purge import purge_project_wrapper
from project_rossum_deploy.commands.upload.upload import upload_project_wrapper
from project_rossum_deploy.commands.visualize.visualize import visualize


@click.group()
@click.version_option()
def main(): ...


main.add_command(download_project_wrapper)
main.add_command(init_project)
main.add_command(migrate_project_wrapper)
main.add_command(migrate_mapping_wrapper)
main.add_command(purge_project_wrapper)
main.add_command(upload_project_wrapper)
main.add_command(visualize)

# For debugging purposes
if __name__ == "__main__":
    main()
