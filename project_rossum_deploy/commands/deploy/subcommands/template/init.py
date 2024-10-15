from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.commands.deploy.subcommands.template.helpers import (
    create_deploy_file_template,
    get_filename_from_user,
)
from project_rossum_deploy.utils.consts import settings


from anyio import Path


async def init_deploy_template_file(
    org_path: Path = None,
):
    if not org_path:
        org_path = Path("./")

    deploy_file_template = create_deploy_file_template()

    yaml = DeployYaml(deploy_file_template)

    deploy_filepath = await get_filename_from_user(
        org_path, default=settings.DEFAULT_DEPLOY_FILENAME
    )

    yaml.save_to_file(deploy_filepath)
