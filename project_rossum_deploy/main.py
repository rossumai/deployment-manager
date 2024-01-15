import click

from project_rossum_deploy.commands.download.download import (
    download_organization_wrapper,
)
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate.migrate import migrate_project_wrapper
from project_rossum_deploy.commands.upload import upload_project_wrapper

# TODO: think about ways to make it work within a single repo

# TODO: specify in mapping you want to target ALL queues etc. (not by ID)
# TODO: specify in mapping you want to update only certain fields

# TODO: preserve comments in yaml
# TODO: custom key sorting in yaml

# TODO: sanitize names of Rossum objects when saving them locally (e.g. '/')

# TODO: INIT: option to use an existing folder

# TODO: extract serverless-function code and edit it unescaped. Then put it back.

# TODO: Migrate
# TODO: you use an existing object as a target of something else. What happens?
# TODO: Aggregate errors and log them into a single file and STDOUT

# TODO: change .env to config.json
# TODO: change mapping.yaml to mapping.json or allow both


@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_organization_wrapper)
main.add_command(init_project)
main.add_command(upload_project_wrapper)
main.add_command(migrate_project_wrapper)
