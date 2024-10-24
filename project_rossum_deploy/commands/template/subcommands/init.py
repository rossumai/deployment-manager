from project_rossum_deploy.commands.deploy.helpers import DeployYaml
from project_rossum_deploy.commands.deploy.common.helpers import (
    get_filename_from_user,
)
from project_rossum_deploy.utils.consts import settings


from anyio import Path


async def create_input_file(
    org_path: Path = None,
):
    if not org_path:
        org_path = Path("./")

    # TODO: attribute override specification in input file

    # TODO: unselected hooks (once dep graph and dep replacement works better)

    # This is done to control the order of the keys
    deploy_file_template = f"""\
# The API URL where changes should be deployed (e.g., https://my-org.rossum.app/api/v1)
# The organization's ID is determined automatically based on the token / user credentials.
{settings.DEPLOY_KEY_TARGET_URL}:
# Which local folder is considered to be the source
{settings.DEPLOY_KEY_SOURCE_DIR}:
    
# Define anchors in the following way:
# x_any_name: &anchor_name
#     name: Name from Variable
#     another_attr: 4
# These will be copied over into the deploy file

# List IDs of queues that should not be deployed, even if they belong to selected WS
unselected_queues:
"""

    yaml = DeployYaml(deploy_file_template)

    deploy_filepath = await get_filename_from_user(
        org_path, default=settings.DEFAULT_INIT_FILENAME
    )

    yaml.save_to_file(deploy_filepath)
