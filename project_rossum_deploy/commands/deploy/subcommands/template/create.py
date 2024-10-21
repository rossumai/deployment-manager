from project_rossum_deploy.commands.deploy.subcommands.run.helpers import DeployYaml
from project_rossum_deploy.commands.deploy.subcommands.template.helpers import (
    add_override_to_deploy_file_objects,
    create_deploy_file_template,
    find_schemas_for_queues,
    get_attribute_overrides_from_user,
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
    source_dir = deploy_file_object.get(settings.DEPLOY_KEY_SOURCE_DIR, None)
    if interactive or not source_dir:
        source_dir = await get_source_dir_from_user(
            org_path=org_path, default=source_dir
        )
    deploy_file_object[settings.DEPLOY_KEY_SOURCE_DIR] = source_dir

    source_path = Path(source_dir)
    if not (await (source_path / "workspaces").exists()):
        display_error(
            f'Did not find "workspaces" directory in the "{source_dir}" directory.'
        )
        return

    # Target URL
    target_url = deploy_file_object.get(settings.DEPLOY_KEY_TARGET_URL, "")
    if interactive or not target_url:
        target_url = await get_target_url_from_user(default=target_url)
    deploy_file_object[settings.DEPLOY_KEY_TARGET_URL] = target_url

    # TODO: sort choices better
    # TODO: consts keys for all object names (workspaces, queues, ...)
    # TODO: allow queues without WS if they have an ID

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

    # Schemas
    # No point letting the user select a schema, each queue should just get its schema

    # The schemas can be an 'explicit' None in the YAML and the default [] would not get used
    previous_schemas = deploy_file_object.get("schemas", [])
    if previous_schemas is None:
        previous_schemas = []
    new_schemas = await find_schemas_for_queues(
        source_path=source_path, queues=selected_queues
    )
    deploy_schema_objects = prepare_deploy_file_objects(
        objects=new_schemas, objects_in_previous_file=previous_schemas
    )
    deploy_file_object["schemas"] = deploy_schema_objects

    if interactive:
        overrides = await get_attribute_overrides_from_user()
        for override in overrides:
            add_override_to_deploy_file_objects(override, deploy_file_object)

    if interactive:
        deploy_filepath = await get_filename_from_user(
            org_path,
            default=str(input_file) if input_file else settings.DEFAULT_DEPLOY_FILENAME,
        )
    else:
        deploy_filepath = input_file

    yaml.save_to_file(deploy_filepath)
