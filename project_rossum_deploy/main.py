import click

from project_rossum_deploy.commands.download import download_organization
from project_rossum_deploy.commands.initialize import init_project

# TODO: put queues into workspaces

@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_organization)
main.add_command(init_project)