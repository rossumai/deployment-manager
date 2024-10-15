import questionary
from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.commands.deploy.subcommands.template.helpers import (
    create_deploy_file_template,
    find_schemas_for_queues,
    get_filename_from_user,
    get_hooks_from_user,
    get_queues_from_user,
    get_source_dir_from_user,
    get_target_url_from_user,
    get_workspaces_from_user,
    prepare_deploy_file_objects,
)
from project_rossum_deploy.utils.consts import display_error, settings


from anyio import Path
from rossum_api import ElisAPIClient


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
    source_dir = deploy_file_object.get(settings.DEPLOY_SOURCE_DIR_KEY, None)
    if interactive or not source_dir:
        source_dir = await get_source_dir_from_user(
            org_path=org_path, default=source_dir
        )
    deploy_file_object[settings.DEPLOY_SOURCE_DIR_KEY] = source_dir

    source_path = Path(source_dir)
    if not (await (source_path / "workspaces").exists()):
        display_error(
            f'Did not find "workspaces" directory in the "{source_dir}" directory.'
        )
        return

    # Target URL
    target_url = deploy_file_object.get(settings.DEPLOY_TARGET_URL_KEY, "")
    if interactive or not target_url:
        target_url = await get_target_url_from_user(default=target_url)
    deploy_file_object[settings.DEPLOY_TARGET_URL_KEY] = target_url

    # TODO: sort choices better

    # Workspaces
    workspaces = deploy_file_object.get("workspaces", [])
    deploy_file_workspaces = await get_workspaces_from_user(
        deploy_file_workspaces=workspaces,
        source_path=source_path,
        interactive=interactive,
    )
    deploy_file_object["workspaces"] = prepare_deploy_file_objects(
        deploy_file_workspaces
    )

    # Queues
    queues = deploy_file_object.get("queues", [])
    deploy_file_queues = await get_queues_from_user(
        deploy_file_queues=queues,
        deploy_ws_paths=[ws["path"].parent for ws in deploy_file_workspaces],
        interactive=interactive,
    )
    deploy_file_object["queues"] = prepare_deploy_file_objects(
        deploy_file_queues, include_path=True
    )

    # Hooks
    hooks = deploy_file_object.get("hooks", [])
    unselected_hook_ids = deploy_file_object.get("unselected_hooks", [])
    selected_hooks, unselected_hooks = await get_hooks_from_user(
        deploy_file_hooks=hooks,
        unselected_hook_ids=unselected_hook_ids,
        source_path=source_path,
        queues=deploy_file_queues,
        interactive=interactive,
    )
    deploy_file_object["hooks"] = selected_hooks
    deploy_file_object["unselected_hooks"] = unselected_hooks

    # Schemas
    schemas = await find_schemas_for_queues(
        source_path=source_path, queues=deploy_file_queues
    )
    deploy_schema_objects = prepare_deploy_file_objects(schemas)
    deploy_file_object["schemas"] = deploy_schema_objects

    # Patch target org
    if interactive:
        patch_target_org = await questionary.confirm(
            "Patch target org?", default=True
        ).ask_async()
        deploy_file_object[settings.DEPLOY_PATCH_TARGET_ORG_KEY] = patch_target_org

    # TODO: attribute override specification in input file

    # TODO: name regex for attribute override
    # TODO: attr override helper

    deploy_filepath = await get_filename_from_user(
        org_path,
        default=str(input_file) if input_file else settings.DEFAULT_DEPLOY_FILENAME,
    )

    yaml.save_to_file(deploy_filepath)
