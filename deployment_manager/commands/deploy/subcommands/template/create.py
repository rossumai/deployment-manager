from deployment_manager.common.get_filepath_from_user import get_filepath_from_user
from deployment_manager.commands.deploy.common.helpers import (
    get_api_url_from_config,
    get_api_url_from_user,
)
from deployment_manager.commands.deploy.subcommands.run.helpers import DeployYaml
from deployment_manager.commands.deploy.subcommands.template.helpers import (
    add_override_to_deploy_file_objects,
    create_deploy_file_template,
    get_attribute_overrides_from_user,
    get_hooks_from_user,
    get_queues_from_user,
    get_dir_and_subdir_from_user,
    get_token_owner_from_user,
    get_workspaces_from_user,
)
from deployment_manager.utils.consts import display_error, settings


from anyio import Path
from rossum_api import ElisAPIClient

# TODO: source-org/subdir compatibility
# Ask if the org-dir already exists (show options to select)
# If yes, take the URL from the config
# If yes, ask for subdir, unless there is only one (e.g., prod-org/prod)
# The user can also select a new subdir (create that)
# ! Here the user has no choice, same org needs the second subdir and then deploy with download
# ! Otherwse, the org would get absolutely messy
# If no, ask the user if he wants to create a new org-dir + ask for a subdir (must create one)
# Keep going as usual


async def create_deploy_template(
    input_file: Path = None,
    org_path: Path = None,
    interactive: bool = False,
    source_client: ElisAPIClient = None,
    target_client: ElisAPIClient = None,
):
    if not input_file:
        input_file_content = create_deploy_file_template()
        # Without an initial input file, the user must always do the selections himself
        interactive = True
    else:
        input_file_content = await input_file.read_text()

    yaml = DeployYaml(file=input_file_content)
    deploy_file_object = yaml.data

    if not org_path:
        org_path = Path("./")

    # Source dir
    source_dir_and_subdir = deploy_file_object.get(settings.DEPLOY_KEY_SOURCE_DIR, None)
    if interactive or not source_dir_and_subdir:
        source_dir_and_subdir = await get_dir_and_subdir_from_user(
            org_path=org_path,
            type=settings.SOURCE_DIRNAME,
            default=source_dir_and_subdir,
        )
    deploy_file_object[settings.DEPLOY_KEY_SOURCE_DIR] = source_dir_and_subdir

    source_path = org_path / source_dir_and_subdir
    if not (await (source_path / "workspaces").exists()):
        display_error(
            f'Did not find "workspaces" directory in the "{source_dir_and_subdir}" directory.'
        )
        return

    # Target dir/subdir
    target_dir_and_subdir = deploy_file_object.get(settings.DEPLOY_KEY_TARGET_DIR, None)
    if interactive or not target_dir_and_subdir:
        target_dir_and_subdir = await get_dir_and_subdir_from_user(
            org_path=org_path,
            type=settings.TARGET_DIRNAME,
            default=target_dir_and_subdir,
        )
    deploy_file_object[settings.DEPLOY_KEY_TARGET_DIR] = target_dir_and_subdir

    # Source URL
    # Try to find it in the config, but do not require it from the user
    source_url = deploy_file_object.get(settings.DEPLOY_KEY_SOURCE_URL, "")
    if not source_url:
        source_url = await get_api_url_from_config(
            base_path=org_path, org_name=source_dir_and_subdir.split("/")[0]
        )
    deploy_file_object[settings.DEPLOY_KEY_SOURCE_URL] = source_url

    # TODO: consts keys for all object names (workspaces, queues, ...)
    # TODO: allow queues without WS if they have an ID

    # TODO: specify hook_template URL for hook in the deploy file

    # Target URL
    # Target URL can be in the deploy file already, in a config file, or inputted by the user
    target_url = deploy_file_object.get(settings.DEPLOY_KEY_TARGET_URL, "")
    if not target_url and target_dir_and_subdir:
        target_url = await get_api_url_from_config(
            base_path=org_path, org_name=target_dir_and_subdir.split("/")[0]
        )
    if interactive or not target_url:
        target_url = await get_api_url_from_user(
            type=settings.TARGET_DIRNAME, default=target_url
        )
    deploy_file_object[settings.DEPLOY_KEY_TARGET_URL] = target_url

    # Hook token owner
    token_owner = deploy_file_object.get(settings.DEPLOY_KEY_TOKEN_OWNER, "")
    if interactive or not token_owner:
        token_owner = await get_token_owner_from_user(default=token_owner)
    deploy_file_object[settings.DEPLOY_KEY_TOKEN_OWNER] = token_owner

    # Workspaces
    workspaces = deploy_file_object.get("workspaces", [])
    deploy_file_workspaces, selected_ws_paths = await get_workspaces_from_user(
        previous_deploy_file_workspaces=workspaces,
        source_path=source_path,
        interactive=interactive,
    )
    deploy_file_object["workspaces"] = deploy_file_workspaces

    # Queues
    queues = deploy_file_object.get("queues", [])
    deploy_file_queues, selected_queues = await get_queues_from_user(
        previous_deploy_file_queues=queues,
        deploy_ws_paths=[ws.parent for ws in selected_ws_paths],
        interactive=interactive,
    )
    deploy_file_object["queues"] = deploy_file_queues

    # Hooks
    hooks = deploy_file_object.get("hooks", [])
    unselected_hook_ids = deploy_file_object.get(
        settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS, []
    )
    selected_hooks, unselected_hooks = await get_hooks_from_user(
        previous_deploy_file_hooks=hooks,
        unselected_hook_ids=unselected_hook_ids,
        source_path=source_path,
        queues=selected_queues,
        interactive=interactive,
    )
    deploy_file_object["hooks"] = selected_hooks
    deploy_file_object[settings.DEPLOY_KEY_UNSELECTED_HOOK_IDS] = unselected_hooks

    if interactive:
        overrides = await get_attribute_overrides_from_user()
        for override in overrides:
            add_override_to_deploy_file_objects(override, deploy_file_object)

    if interactive:
        source_subdir_name = source_dir_and_subdir.split("/")[1]
        target_subdir_name = target_dir_and_subdir.split("/")
        default_deploy_name = f"/{source_subdir_name}_{target_subdir_name[1] if len(target_subdir_name) > 1 else "NA"}.yaml"
        deploy_filepath = await get_filepath_from_user(
            org_path,
            default=(
                str(input_file)
                if input_file
                else settings.DEFAULT_DEPLOY_PARENT + default_deploy_name
            ),
        )
    else:
        deploy_filepath = input_file

    await yaml.save_to_file(deploy_filepath)
