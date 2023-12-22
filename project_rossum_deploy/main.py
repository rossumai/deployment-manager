import click

from project_rossum_deploy.commands.download import download_organization
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate import migrate_project


# TODO: deploy to Rossum
# Update only what changed (programmatically call git to find out)

# TODO: Migrate
# emtpy right hand side (e.g., `39393:`) -> create new object
# non-empty right hand side (e.g., `393939:77278`) -> update the object
# IGNORE keyword
# ! instead of templating, we could use mapping to replace all values (take the config, find id in the left side, replace with right side)

@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_organization)
main.add_command(init_project)
main.add_command(migrate_project)