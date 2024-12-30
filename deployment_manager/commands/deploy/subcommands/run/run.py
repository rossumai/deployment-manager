from copy import deepcopy
from anyio import Path
from pydantic import ValidationError
import questionary
from dataclasses import fields
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.models.organization import Organization

from deployment_manager.commands.deploy.subcommands.run.object_release import (
    DeployException,
)
from deployment_manager.commands.deploy.subcommands.run.release_file import (
    ReleaseFile,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
    generate_deploy_timestamp,
    get_new_deploy_file_path,
    get_url_and_credentials,
    update_ignore_flags_in_yaml,
)

from deployment_manager.commands.deploy.subcommands.run.reverse_override import (
    reverse_source_target_in_yaml,
)
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.common.read_write import read_json
from deployment_manager.utils.consts import (
    display_error,
    display_info,
    settings,
)


# TODO: yes flag to skip the question after plan
async def deploy_release_file(
    deploy_file_path: Path,
    project_path: Path = None,
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

    if not project_path:
        project_path = Path("./")

    source_dir_subdir = yaml.data[settings.DEPLOY_KEY_SOURCE_DIR]

    source_org_name = source_dir_subdir.split("/")[0]

    if not source_client:
        source_credentials = await get_url_and_credentials(
            project_path=project_path,
            org_name=source_org_name,
            type=settings.SOURCE_DIRNAME,
            yaml_data=yaml.data,
        )
        if not source_credentials:
            return
        source_client = ElisAPIClient(
            base_url=source_credentials.url, token=source_credentials.token
        )

    source_org_path = project_path / source_org_name / "organization.json"
    if not await source_org_path.exists():
        display_error(f'Could not find organization.json under "{source_org_path}"')
        return
    source_org_dict = await read_json(source_org_path)
    source_org = Organization(
        **{
            k: v
            for k, v in source_org_dict.items()
            if k in {f.name for f in fields(Organization)}
        }
    )

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

    target_org_path: Path = project_path / target_org_name / "organization.json"
    if await target_org_path.exists():
        target_org_dict = await read_json(target_org_path)
        target_org = Organization(
            **{
                k: v
                for k, v in target_org_dict.items()
                if k in {f.name for f in fields(Organization)}
            }
        )

    else:
        target_org_choices = []
        async for org in target_client.list_all_organizations():
            target_org_choices.append(questionary.Choice(title=org.name, value=org))
        if len(target_org_choices) > 1:
            target_org = await questionary.select(
                "Select target organization:", choices=target_org_choices
            ).ask_async()
        else:
            target_org = target_org_choices[0].value

    source_dir_path = project_path / Path(source_dir_subdir)
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
            **deepcopy(yaml.data),
            client=target_client,
            source_client=source_client,
            source_dir_path=source_dir_path,
            yaml=deepcopy(yaml),
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
            "Do you wish to apply the plan?", default=False
        ).ask_async()
    ):
        return

    # Take what the user inputted (or the same if user input not applicable)
    yaml.data[settings.DEPLOY_KEY_TOKEN_OWNER] = planned_release.token_owner_id
    update_ignore_flags_in_yaml(yaml.data, planned_release.queue_ignore_warnings)
    release.token_owner_id = planned_release.token_owner_id
    release.hook_templates = planned_release.hook_templates
    release.ignore_timestamp_mismatches = planned_release.ignore_timestamp_mismatches

    deploy_error = False
    try:
        await release.deploy_organization()

        await release.deploy_hooks()
        await release.migrate_hook_dependency_graph()

        await release.deploy_workspaces()

        await release.deploy_queues()

        await release.apply_implicit_id_override()
    except Exception:
        deploy_error = True
        display_error(
            "Encountered error during deploy, see logs above. Saving intermediary results."
        )

    # To conform with the Elis API modified_at format
    yaml.data[settings.DEPLOY_KEY_LAST_DEPLOYED_AT] = generate_deploy_timestamp()
    yaml.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = target_org.id

    after_deploy_file_path = await get_new_deploy_file_path(
        deploy_file_path=deploy_file_path,
        first_deploy=first_deploy,
    )
    await yaml.save_to_file(after_deploy_file_path)

    display_info(f"After-deploy file saved to [green]{after_deploy_file_path}[/green]")

    reverse_mapping = yaml.data.get(settings.DEPLOY_KEY_REVERSE_MAPPING, False)
    if reverse_mapping:
        try:
            reversed_yaml = await reverse_source_target_in_yaml(
                yaml=yaml,
                source_org=source_org,
                target_org=target_org,
                prev_source_client=source_client,
                prev_target_client=target_client,
            )

            reverse_deploy_file_path = await get_new_deploy_file_path(
                deploy_file_path=deploy_file_path,
                first_deploy=True,
                suffix="_reversed",
            )
            await reversed_yaml.save_to_file(reverse_deploy_file_path)
        except Exception as e:
            display_error("Error while reversing mapipng in the deploy file. ^", e)

    if (
        deploy_error
        and not await questionary.confirm(
            f"There was an error during {settings.DEPLOY_COMMAND_NAME}. Do you want to {settings.DOWNLOAD_COMMAND_NAME} the changes?",
            default=False,
        ).ask_async()
    ):
        return

    # TODO: remember what was deployed, if those IDs exist locally, they should be automatically moved (pulled) into the new (sub)dir <- important for same-org
    # ! TODO: if there is not target dir, ask the user for a name. Then offer to download all new objects into that dir
    if not target_dir_subdir:
        if await questionary.confirm(
            f"Would you like to specify target directory and {settings.DOWNLOAD_COMMAND_NAME} the deployed objects?"
        ).ask_async():
            print("TBD")
            # target_dir_subdir_path = project_path / Path(target_dir_subdir)
    else:
        target_dir_subdir_path = project_path / Path(target_dir_subdir)
        await download_destinations(
            destinations=[target_dir_subdir_path], project_path=project_path
        )


# TODO: more granular error handling for hook dep graph and implicit attribute override

# TODO: diff could show ID and (name)

# TODO: check if remote was not modified when updating?


# TODO: log all messages to stdout and into a separate file as well
