from rossum_api import ElisAPIClient
import click


@click.command(
    name="download",
    help="""
Downloads all Rossum objects from the user's default (first) organization.
Creates a local directory structure with the configs of these objects.
If such a directory already exists, it gets overwritten.
               """,
)
def download_project():
    # client = ElisAPIClient(base_url=base_url, token=token)
    click.echo("")

    # return await client.retrieve_organization()
    # print(o)
