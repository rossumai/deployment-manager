from anyio import Path
import anyio
from pydantic import ValidationError
import questionary
from dataclasses import fields
from deployment_manager.commands.deploy.subcommands.run.deploy_orchestrator.deploy_orchestrator import (
    DeployOrchestrator,
)
from deployment_manager.commands.deploy.subcommands.run.merge.state import DeployState
from deployment_manager.commands.deploy.subcommands.run.models import DeployException
from rossum_api import APIClientError, ElisAPIClient
from rossum_api.models.organization import Organization
from rich.spinner import Spinner
from rich.live import Live

from deployment_manager.commands.deploy.subcommands.run.helpers import (
    DeployYaml,
    check_required_keys,
    generate_deploy_timestamp,
    get_new_deploy_file_path,
    get_url_and_credentials,
)

from deployment_manager.commands.deploy.subcommands.run.reverse_override import (
    reverse_source_target_in_yaml,
)
from deployment_manager.commands.download.download import download_destinations
from deployment_manager.common.read_write import read_object_from_json
from deployment_manager.utils.consts import (
    display_error,
    display_info,
    settings,
)


async def deploy_release_file(
    deploy_file_path: Path,
    project_path: Path = None,
    source_client: ElisAPIClient = None,
    target_client: ElisAPIClient = None,
    auto_apply_plan: bool = False,
    prefer: str = None,
    # auto_delete: bool = False,
    commit: bool = False,
    commit_message: str = "",
):
    spinner = Spinner("dots", text="Initializing deploy process...")

    with Live(spinner, refresh_per_second=10):
        deploy_file = await deploy_file_path.read_text()
        yaml = DeployYaml(deploy_file)

        if not check_required_keys(yaml.data):
            return

        if not project_path:
            project_path = Path("./")

        # Ensure backwards compatibility with deploy files without deploy state file or path
        deploy_state_file_path = yaml.data.get(settings.DEPLOY_KEY_STATE_PATH, "")
        deploy_state_file_path = await DeployState.ensure_deploy_state_file(
            path=anyio.Path(deploy_state_file_path or ""),
            base_path=project_path,
            deploy_file_path=anyio.Path(deploy_file_path),
        )
        yaml.data[settings.DEPLOY_KEY_STATE_PATH] = str(deploy_state_file_path)

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
        source_org_dict = await read_object_from_json(source_org_path)
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
            target_org_dict = await read_object_from_json(target_org_path)
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
            release = DeployOrchestrator(
                **yaml.data,
                client=target_client,
                source_client=source_client,
                source_dir_path=source_dir_path,
                yaml=yaml,
                source_org=source_org,
                target_org=target_org,
                prefer=prefer,
                deploy_file_path=deploy_file_path,
                # auto_delete=auto_delete,
            )
        except ValidationError as e:
            display_error(f"Missing information in the deploy file: {e}")
            return

        if release.deployed_org_id:
            try:
                if release.deployed_org_id != target_org.id:
                    raise DeployException(
                        f"Target org ID in deploy file ({release.deployed_org_id}) is not the same as the selected target org ({target_org.id}). Please check your configuration."
                    )
                await target_client.retrieve_organization(release.deployed_org_id)
            except APIClientError as e:
                if e.status_code == 404:
                    display_error(
                        f'Organization with ID "{release.deployed_org_id}" not found with the specified token in {target_client._http_client.base_url}. Please make sure you have to correct token and target URL.'
                    )
                    return
                else:
                    raise e
            except DeployException as e:
                display_error(str(e))
                return

        try:
            await release.initialize_deploy_objects()

            await release.initialize_target_objects()

            await release.compare_object_versions()
        except DeployException as e:
            display_error(f"Planning failed: {e}")
            return
        except Exception as e:
            display_error(f"Planning failed: {e}", e)
            return

    try:
        await release.show_deploy_plan()
    except DeployException as e:
        display_error(f"Plan visualization failed: {e}")
        return
    except Exception as e:
        display_error(f"Plan visualization failed: {e}", e)
        return

    if not auto_apply_plan and not (
        await questionary.confirm(
            "Do you wish to apply the plan?", default=False
        ).ask_async()
    ):
        return

    # Take what the user inputted (or the same if user input not applicable)
    yaml.data[settings.DEPLOY_KEY_TOKEN_OWNER] = release.token_owner_id
    release.update_ignore_flags_in_yaml()

    deploy_error = False
    try:
        await release.run_deploy(is_first=True)

        await release.run_deploy(is_first=False)

        await release.save_deploy_state()
    except Exception as e:
        deploy_error = True
        display_error(
            "Encountered error during deploy, see logs above. Saving intermediary results.",
            e,
        )

    # To conform with the Elis API modified_at format
    yaml.data[settings.DEPLOY_KEY_LAST_DEPLOYED_AT] = generate_deploy_timestamp()
    yaml.data[settings.DEPLOY_KEY_DEPLOYED_ORG_ID] = target_org.id

    after_deploy_file_path = await get_new_deploy_file_path(
        deploy_file_path=deploy_file_path,
        create_with_suffix=False,
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
                create_with_suffix=True,
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

    if target_dir_subdir:
        target_dir_subdir_path = project_path / Path(target_dir_subdir)
        await download_destinations(
            destinations=[target_dir_subdir_path],
            project_path=project_path,
            commit=commit,
            commit_message=commit_message,
        )


# TODO: more granular error handling for hook dep graph and implicit attribute override

# TODO: diff could show ID and (name)

# TODO: log all messages to stdout and into a separate file as well
