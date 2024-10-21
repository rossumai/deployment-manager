import datetime
from anyio import Path
import questionary
from rossum_api import APIClientError, ElisAPIClient


from project_rossum_deploy.commands.deploy.subcommands.run.object_release import (
    PathNotFoundException,
)
from project_rossum_deploy.commands.deploy.subcommands.run.release_file import (
    ReleaseFile,
)
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
    get_target_credentials,
)

from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    display_error,
    settings,
)


# TODO: yes flag to skip the question after plan
async def deploy_release_file(
    deploy_file_path: Path,
    org_path: Path = None,
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

    # TODO: enable other non-target destinations
    source_org = await read_json(source_dir_path / "organization.json")

    if not target_client:
        target_url = yaml.data[settings.DEPLOY_KEY_TARGET_URL]
        target_credentials = await get_target_credentials(
            org_path=org_path, yaml_data=yaml.data
        )
        if not target_credentials:
            display_error("Missing credentials for target API.")
            return
        target_client = ElisAPIClient(
            base_url=target_url, token=target_credentials.token
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

    release = ReleaseFile(
        **yaml.data,
        client=target_client,
        source_dir_path=source_dir_path,
        yaml=yaml,
        source_org=source_org,
        target_org=target_org,
    )
    planned_release = ReleaseFile(
        **yaml.data,
        client=target_client,
        source_dir_path=source_dir_path,
        yaml=yaml,
        source_org=source_org,
        target_org=target_org,
    )

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
        await planned_release.deploy_organization(plan_only=True)

        await planned_release.deploy_schemas(plan_only=True)

        await planned_release.deploy_hooks(plan_only=True)
        await planned_release.migrate_hook_dependency_graph(plan_only=True)

        await planned_release.deploy_workspaces(plan_only=True)

        await planned_release.deploy_queues(plan_only=True)

        await planned_release.apply_implicit_id_override()
    except PathNotFoundException as e:
        display_error(f"{e}")
        return

    if not (
        await questionary.confirm(
            "Do you wish to apply the plan?", default=True
        ).ask_async()
    ):
        return

    await release.deploy_organization()

    await release.deploy_schemas()

    await release.deploy_hooks()
    await release.migrate_hook_dependency_graph()

    await release.deploy_workspaces()

    await release.deploy_queues()

    await release.apply_implicit_id_override()

    yaml.data[settings.DEPLOY_KEY_LAST_DEPLOYED_AT] = (
        datetime.datetime.now().isoformat()
    )
    yaml.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = target_org.id

    if first_deploy:
        deployed_deploy_file_path = deploy_file_path.with_stem(
            f"{deploy_file_path.stem}_deployed"
        )
    else:
        deployed_deploy_file_path = deploy_file_path

    yaml.save_to_file(deployed_deploy_file_path)

    return


# TODO: remember private hook url for the non-plan deploy or choose a different method
# Make plan non-parallel to allow good STDOUT experience, then parallelize

# TODO: check if remote was not modified when updating?

# check if queue has its WS being deployed or it is a queue with an existing target_id

# TODO: log all messages to stdout and into a separate file as well

# TODO: make purge work with deploy files as well

# TODO: download changes into proper dir (based on the deploy file)
