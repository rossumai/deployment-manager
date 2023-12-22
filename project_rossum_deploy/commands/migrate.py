from anyio import Path
import click
from rossum_api import ElisAPIClient

from project_rossum_deploy.utils.consts import settings
from project_rossum_deploy.utils.functions import read_yaml


@click.command(
    name="migrate",
    help="""
Applies selected changes onto other objects.
If these objects don't exist, they get crated.
The specifics of what objects to migrate where can be specified in a mapping.yaml file.
               """,
)
@click.option(
    "--mapping",
    default=settings.MAPPING_FILENAME,
    show_default=True,
    help="Path to the mapping file to use.",
)
def migrate_project(mapping: str):
    org_path = Path("./")
    mapping = read_yaml(org_path / mapping)

    target_organization = mapping["organization"]["target"]
    if not target_organization:
        raise click.ClickException(
            "No target for organization. If you want to migrate inside the same organization, just target its own ID."
        )

    # Create/update workspaces -> update mapping
    # Create update schemas -> update mapping
    # Create/update queues -> update mapping
    # Create update hooks -> update mapping

    client = ElisAPIClient(
        base_url=settings.TO_API_URL,
        username=settings.TO_USERNAME,
        password=settings.TO_PASSWORD,
    )
