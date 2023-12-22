import click

from project_rossum_deploy.utils.consts import settings


@click.command(
    name="migrate",
    help="""
Creates a new project directory with the specified name with basic files.
Also initializes it as a git repository.
The user is then expected to provide .env credentials and download Rossum objects.
               """,
)
@click.option(
    "--mapping",
    default=settings.MAPPING_FILENAME,
    show_default=True,
    help="Path to the mapping file to use.",
)
def migrate_project(mapping):
    click.echo(f'Initialized a new directory "{mapping}".')
