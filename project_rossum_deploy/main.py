import click

from project_rossum_deploy.commands.download import download_project
from project_rossum_deploy.commands.initialize import init_project


@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_project)
main.add_command(init_project)