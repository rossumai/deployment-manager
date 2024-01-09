import click

from project_rossum_deploy.commands.download.download import (
    download_organization_wrapper,
)
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate.migrate import migrate_project
from project_rossum_deploy.commands.upload import upload_project_wrapper

# TODO: preserve comments in yaml
# TODO: custom key sorting in yaml

# TODO: sanitize names of Rossum objects when saving them locally (e.g. '/')

# TODO: Migrate
# TODO: Aggregate errors and log them into a single file and STDOUT

# TODO: change .env to config.yaml


@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_organization_wrapper)
main.add_command(init_project)
main.add_command(upload_project_wrapper)
main.add_command(migrate_project)
