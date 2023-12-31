import click

from project_rossum_deploy.commands.download.download import download_organization
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate import migrate_project

# ! Download each object individually to get all of its details

# TODO: attribute_override updating in mapping

# TODO: first migrate (without left hand side) -> add target

# TODO: deploy to Rossum
# Update only what changed (programmatically call git to find out)

# TODO: Migrate
# ? PATCH dependency of hook to includes a queue: does the queue automatically get its dependency patched as wel?
# TODO: Aggregate errors and log them into a single file and STDOUT

# TODO: change .env to config.yaml

@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_organization)
main.add_command(init_project)
main.add_command(migrate_project)