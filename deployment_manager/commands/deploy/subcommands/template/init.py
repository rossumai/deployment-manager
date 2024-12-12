from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.template.helpers import (
    create_deploy_file_template,
)
from deployment_manager.utils.consts import settings


from anyio import Path


async def init_deploy_template_file(
    org_path: Path = None,
):
    if not org_path:
        org_path = Path("./")

    deploy_file_template = create_deploy_file_template()

    yaml = DeployYaml(deploy_file_template)

    deploy_filepath = await get_filepath_from_user(
        org_path, default=settings.DEFAULT_DEPLOY_PARENT + "/deploy_file.yaml"
    )

    await yaml.save_to_file(deploy_filepath)
