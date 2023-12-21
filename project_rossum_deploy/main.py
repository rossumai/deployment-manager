import click

from project_rossum_deploy.commands.download import download_project


@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_project)
