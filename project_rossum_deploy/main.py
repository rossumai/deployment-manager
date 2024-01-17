import click

from project_rossum_deploy.commands.download.download import (
    download_project_wrapper,
)
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate.migrate import migrate_project_wrapper
from project_rossum_deploy.commands.upload import upload_project_wrapper

# TODO: think about ways to make it work within a single repo

# TODO: token owner in different org (take it from credentials)

# TODO: multitarget in mapping
# List of objects: id, attribute_override
# Put attr_override under target objects

# TODO: custom key sorting in yaml

# TODO: push differentiate staged/unstaged changes (ignore those)

# TODO: specify in mapping you want to target ALL queues etc. (not by ID)
# TODO: specify in mapping you want to update only certain fields

# TODO: preserve comments in yaml

# TODO: array of targets in mapping (incl. attribute_override for each)
# Preserve a single ID
# ? You specify 2 targets and they download into separate folders. If you redownload, you would need to check target order in mapping to know where to put it? ([2] -> target_3/)
# ? 

# TODO: Push
# TODO: workspaces can only be deleted after they have no queues
# TODO: queues should have the delete_after: 0 query param set so that their schema can be deleted immediately

# TODO: sanitize names of Rossum objects when saving them locally (e.g. '/')

# TODO: Migrate
# TODO: Aggregate errors and log them into a single file and STDOUT

# TODO: change mapping.yaml to mapping.json or allow both

# TODO: remove countdown from progress bars

@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_project_wrapper)
main.add_command(init_project)
main.add_command(upload_project_wrapper)
main.add_command(migrate_project_wrapper)
