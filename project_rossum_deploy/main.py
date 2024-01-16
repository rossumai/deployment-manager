import click

from project_rossum_deploy.commands.download.download import (
    download_organization_wrapper,
)
from project_rossum_deploy.commands.initialize import init_project
from project_rossum_deploy.commands.migrate.migrate import migrate_project_wrapper
from project_rossum_deploy.commands.upload import upload_project_wrapper

# TODO: think about ways to make it work within a single repo
# ? PULL: implicitly only source (if different orgs), target download would go to target/
# Use env creds if both are there, otherwise it can only be either source or source+target (interorg) - download based on the command
# If inter-org, source and target dirs would have the same organization.json, it should not matter
# TODO: check repulling in commands - what about both orgs?

# ? PUSH: probably OK to just take the env credentials based on destination
# ? RELEASE: 

# TODO: specify in mapping you want to target ALL queues etc. (not by ID)
# TODO: specify in mapping you want to update only certain fields

# TODO: preserve comments in yaml
# TODO: custom key sorting in yaml

# TODO: array of targets in mapping (incl. attribute_override for each)
# Preserve a single ID
# ? You specify 2 targets and they download into separate folders. If you redownload, you would need to check target order in mapping to know where to put it? ([2] -> target_3/)
# ? 

# TODO: Push
# TODO: workspaces can only be deleted after they have no queues
# TODO: queues should have the delete_after: 0 query param set so that their schema can be deleted immediately

# TODO: sanitize names of Rossum objects when saving them locally (e.g. '/')

# TODO: INIT: option to use an existing folder

# TODO: extract serverless-function code and edit it unescaped. Then put it back.

# TODO: Migrate
# TODO: Aggregate errors and log them into a single file and STDOUT

# TODO: change .env to config.json
# TODO: change mapping.yaml to mapping.json or allow both

# TODO: remove countdown from progress bars

@click.group()
@click.version_option()
def main():
    ...


main.add_command(download_organization_wrapper)
main.add_command(init_project)
main.add_command(upload_project_wrapper)
main.add_command(migrate_project_wrapper)
