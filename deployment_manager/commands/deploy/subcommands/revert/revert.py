from copy import deepcopy
from anyio import Path
from pydantic import ValidationError
import questionary
from rossum_api import ElisAPIClient

from deployment_manager.commands.deploy.subcommands.run.object_release import (
    DeployException,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
    generate_deploy_timestamp,
    get_new_deploy_file_path,
    get_url_and_credentials,
)

from deployment_manager.commands.deploy.subcommands.revert.revert_deploy_file import (
    RevertDeployFile,
)
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.utils.consts import (
    display_error,
    display_info,
    settings,
)


async def revert_release_file(
    deploy_file_path: Path,
    project_path: Path = None,
    target_client: ElisAPIClient = None,
    commit: bool = False,
    commit_message: str = "",
):
    release_file = await deploy_file_path.read_text()
    yaml = DeployYaml(release_file)
    if not check_required_keys(yaml.data):
        return

    if not project_path:
        project_path = Path("./")

    target_dir_subdir = yaml.data.get(settings.DEPLOY_KEY_TARGET_DIR, "")
    target_org_name = target_dir_subdir.split("/")[0]

    if not target_client:
        target_credentials = await get_url_and_credentials(
            project_path=project_path,
            org_name=target_org_name if target_dir_subdir else "",
            type=settings.TARGET_DIRNAME,
            yaml_data=yaml.data,
        )
        if not target_credentials:
            return
        target_client = ElisAPIClient(
            base_url=target_credentials.url, token=target_credentials.token
        )

    try:
        release = RevertDeployFile(
            **yaml.data,
            client=target_client,
            yaml=yaml,
            plan_only=False,
        )
        planned_release = RevertDeployFile(
            **deepcopy(yaml.data),
            client=target_client,
            yaml=deepcopy(yaml),
            plan_only=True,
        )
    except ValidationError as e:
        display_error(f"Missing information in the deploy file: {e}")
        return

    try:
        await planned_release.display_reverted_organization()

        await planned_release.revert_hooks()

        await planned_release.revert_workspaces()

        await planned_release.revert_queues()

    except DeployException as e:
        display_error(f"Planning failed: {e}")
        return
    except Exception as e:
        display_error(f"Planning failed: {e}", e)
        return

    if not (
        await questionary.confirm(
            "Do you wish to apply the plan?", default=False
        ).ask_async()
    ):
        return

    revert_error = False
    try:
        await release.revert_hooks()

        await release.revert_workspaces()

        await release.revert_queues()

    except Exception:
        revert_error = True
        display_error(
            "Encountered error during revert, see logs above. Saving intermediary results."
        )

    yaml.data[settings.DEPLOY_KEY_LAST_DEPLOYED_AT] = generate_deploy_timestamp()

    if not revert_error:
        yaml.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = None

    after_revert_file_path = await get_new_deploy_file_path(
        deploy_file_path=deploy_file_path,
        first_deploy=False,
    )
    await yaml.save_to_file(after_revert_file_path)

    display_info(f"After-revert file saved to [green]{after_revert_file_path}[/green]")

    if (
        revert_error
        and not await questionary.confirm(
            f"There was an error during {settings.DEPLOY_COMMAND_NAME}. Do you want to {settings.DOWNLOAD_COMMAND_NAME} the changes?",
            default=False,
        ).ask_async()
    ):
        return

    if target_dir_subdir:
        target_dir_subdir_path = project_path / Path(target_dir_subdir)
        await download_destinations(
            destinations=[target_dir_subdir_path],
            project_path=project_path,
            commit=commit,
            commit_message=commit_message,
        )


# TODO: log all messages to stdout and into a separate file as well
