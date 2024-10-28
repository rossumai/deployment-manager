import datetime
from anyio import Path
from pydantic import ValidationError
import questionary
from rossum_api import APIClientError, ElisAPIClient


from project_rossum_deploy.commands.deploy.common.helpers import get_filename_from_user
from project_rossum_deploy.commands.deploy.subcommands.run.release_file import (
    DeployException,
    ReleaseFile,
)
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
    get_url_and_credentials,
)

from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    display_error,
    display_warning,
    settings,
)


# TODO: yes flag to skip the question after plan
async def deploy_release_file(
    deploy_file_path: Path,
    org_path: Path = None,
    source_client: ElisAPIClient = None,
    target_client: ElisAPIClient = None,
    # force: bool = False,
    # commit: bool = False,
    # commit_message: str = "",
):
    first_deploy = True

    release_file = await deploy_file_path.read_text()
    yaml = DeployYaml(release_file)
    if not check_required_keys(yaml.data):
        return

    if not org_path:
        org_path = Path("./")
    source_dir_path = org_path / yaml.data[settings.DEPLOY_KEY_SOURCE_DIR]

    source_org = await read_json(source_dir_path / "organization.json")

    if not target_client:
        target_credentials = await get_url_and_credentials(
            org_path=org_path, type=settings.TARGET_DIRNAME, yaml_data=yaml.data
        )
        if not target_credentials:
            return
        target_client = ElisAPIClient(
            base_url=target_credentials.url, token=target_credentials.token
        )

    if not source_client:
        source_credentials = await get_url_and_credentials(
            org_path=org_path, type=settings.SOURCE_DIRNAME, yaml_data=yaml.data
        )
        if not source_credentials:
            return
        source_client = ElisAPIClient(
            base_url=source_credentials.url, token=source_credentials.token
        )

    target_org_choices = []
    async for org in target_client.list_all_organizations():
        target_org_choices.append(questionary.Choice(title=org.name, value=org))
    if len(target_org_choices) > 1:
        target_org = await questionary.select(
            "Select target organization:", choices=target_org_choices
        ).ask_async()
    else:
        target_org = target_org_choices[0].value

    try:
        release = ReleaseFile(
            **yaml.data,
            client=target_client,
            source_client=source_client,
            source_dir_path=source_dir_path,
            yaml=yaml,
            source_org=source_org,
            target_org=target_org,
            plan_only=False,
        )
        planned_release = ReleaseFile(
            **yaml.data,
            client=target_client,
            source_client=source_client,
            source_dir_path=source_dir_path,
            yaml=yaml,
            source_org=source_org,
            target_org=target_org,
            plan_only=True,
        )
    except ValidationError as e:
        display_error(f"Missing information in the deploy file: {e}")
        return

    if release.deployed_org_id:
        first_deploy = False
        try:
            await target_client.retrieve_organization(release.deployed_org_id)
        except APIClientError as e:
            if e.status_code == 404:
                display_error(
                    f'Organization with ID "{release.deployed_org_id}" not found with the specified token in {target_client._http_client.base_url}. Please make sure you have to correct token and target URL.'
                )
                return

    try:
        await planned_release.deploy_organization()

        await planned_release.deploy_schemas()

        await planned_release.deploy_hooks()
        await planned_release.migrate_hook_dependency_graph()

        await planned_release.deploy_workspaces()

        await planned_release.deploy_queues()

        await planned_release.apply_implicit_id_override()
    except DeployException as e:
        display_error(f"Planning failed: {e}")
        return
    except Exception as e:
        display_error(f"Planning failed: {e}", e)
        return

    if not (
        await questionary.confirm(
            "Do you wish to apply the plan?", default=True
        ).ask_async()
    ):
        return

    # Take what the user inputted (or the same if user input not applicable)
    yaml.data[settings.DEPLOY_KEY_TOKEN_OWNER] = planned_release.token_owner_id
    release.token_owner_id = planned_release.token_owner_id
    release.hook_templates = planned_release.hook_templates

    try:
        await release.deploy_organization()

        await release.deploy_schemas()

        await release.deploy_hooks()
        await release.migrate_hook_dependency_graph()

        await release.deploy_workspaces()

        await release.deploy_queues()

        await release.apply_implicit_id_override()
    except Exception:
        display_warning(
            "Encountered error during deploy, see logs above. Saving intermediary results."
        )

    yaml.data[settings.DEPLOY_KEY_LAST_DEPLOYED_AT] = (
        datetime.datetime.now().isoformat()
    )
    yaml.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = target_org.id

    # TODO: extract into function
    if first_deploy:
        deployed_deploy_file_path = deploy_file_path.with_stem(
            f"{deploy_file_path.stem}_deployed"
        )
        if await deployed_deploy_file_path.exists():
            overwrite = await questionary.confirm(
                f'File "{deployed_deploy_file_path}" already exists. Overwrite?',
                default=False,
            ).ask_async()
            if not overwrite:
                deployed_deploy_file_path = await get_filename_from_user(org_path)
    else:
        deployed_deploy_file_path = deploy_file_path

    yaml.save_to_file(deployed_deploy_file_path)

    return


# TODO: more granular error handling for hook dep graph and implicit attribute override

# TODO: diff could show ID and (name)


# TODO: check if remote was not modified when updating?


# check if queue has its WS being deployed or it is a queue with an existing target_id

# TODO: log all messages to stdout and into a separate file as well

# TODO: make purge work with deploy files as well
# Just specify the deploy file. It will look at the target URL/dir
# If the dir was found locally, the files will be deleted as well

# TODO: download changes into proper dir (based on the deploy file) (once pull is updated)
# TODO: if the objects existed in some other dir, remove it from there (the pull command will not be built for that anymore)

# TODO: prod to UAT deploy and reverse the deploy file


# TODO: if there is not target dir, ask the user for a name. Then offer to download all new objects into that dir

# TODO: support for secrets
