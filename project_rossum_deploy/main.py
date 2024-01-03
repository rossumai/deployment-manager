import click

from project_rossum_deploy.commands.download.download import download_organization_wrapper
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate.migrate import migrate_project

# TODO: uppercase schemas, hooks, queues...

# TODO: attribute_override updating in mapping

# TODO: preserve comments in yaml

# TODO: support token authentication (for support accounts)

# TODO: deploy to Rossum
# Update only what changed (programmatically call git to find out)

# TODO: Migrate
# TODO: Aggregate errors and log them into a single file and STDOUT

# TODO: change .env to config.yaml

# TODO: Push functionality
# TODO: push --all

@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_organization_wrapper)
main.add_command(init_project)
main.add_command(migrate_project)