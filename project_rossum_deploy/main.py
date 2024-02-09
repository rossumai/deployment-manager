import click

from project_rossum_deploy.commands.download.download import (
    download_project_wrapper,
)
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate.migrate import migrate_project_wrapper
from project_rossum_deploy.commands.upload import upload_project_wrapper

# TODO: selective pull
# When pushing changes, repull only the last_modified_date from the API, not everything
# When pulling, local and remote LMD must be equal, otherwise raise a warning/prompt
# If they are equal, nothing gets overriden
# Detect files that were not remotely found and delete them

# TODO: selective push
# First, check that all files have LMD equal to remote, otherwise, prompt
# Second: upload individual files (and repull the new LMD)

# TODO: multitarget in mapping
# List of objects: id, attribute_override
# Put attr_override under target objects

# TODO: specify in mapping you want to target ALL queues etc. (not by ID)
# TODO: specify in mapping you want to update only certain fields

# TODO: preserve comments in yaml

# TODO: Push --force param (will push everything even if you have no changes)

# TODO: Pull ignores some keys (e.g., count for queues) which get updated all the time

# TODO: array of targets in mapping (incl. attribute_override for each)
# Preserve a single ID
# ? You specify 2 targets and they download into separate folders. If you redownload, you would need to check target order in mapping to know where to put it? ([2] -> target_3/)
# ? 

# TODO: Push
# TODO: workspaces can only be deleted after they have no queues
# TODO: queues should have the delete_after: 0 query param set so that their schema can be deleted immediately

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
