import click
import questionary
from anyio import Path
from rossum_api import ElisAPIClient
from ruamel.yaml import YAML, comments


from project_rossum_deploy.commands.template.helpers import prepare_choices
from project_rossum_deploy.common.read_write import read_json
from project_rossum_deploy.utils.consts import (
    display_error,
    display_warning,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
    extract_id_from_url,
    find_all_hook_paths_in_destination,
    find_all_schema_paths_in_destination,
    find_object_by_id,
)

CS = comments.CommentedSeq


@click.command(
    name=settings.TEMPLATE_COMMAND_NAME,
    help="""""",
)
@coro
async def create_deploy_template_wrapper():
    await create_deploy_template_file()


async def create_deploy_template_file(
    org_path: Path = None,
    source_client: ElisAPIClient = None,
    target_client: ElisAPIClient = None,
):
    if not org_path:
        org_path = Path("./")
    dir_candidates = [
        dir_path
        async for dir_path in org_path.iterdir()
        if await dir_path.is_dir() and str(dir_path) not in settings.DEPLOY_IGNORED_DIRS
    ]

    source_choices = [
        questionary.Choice(title=str(source_path)) for source_path in dir_candidates
    ]
    source_dir = await questionary.select(
        "Which folder is the source?", choices=source_choices
    ).ask_async()
    source_path = org_path / source_dir

    # TODO: ask if org should be updated

    # TODO: validate the dir has the expected subdirs (e.g., WS)

    if not (await (source_path / "workspaces").exists()):
        display_error(
            f'Did not find "workspaces" directory in the "{source_dir}" directory.'
        )
        return

    # TODO: validate URL
    target_org_url = await questionary.text(
        "What is the target organization API URL? (e.g., https://my-org.rossum.app/api/v1 ):"
    ).ask_async()

    # This is done to control the order of the keys
    deploy_file_template = f"""\
# The API URL where changes should be deployed (e.g., https://my-org.rossum.app/api/v1)
# The organization's ID is determined automatically based on the token / user credentials.
{settings.DEPLOY_TARGET_URL_KEY}: {target_org_url}
# Which local folder is considered to be the source
{settings.DEPLOY_SOURCE_DIR_KEY}: {source_dir}

workspaces: []

queues: []

hooks: []

schemas: []
"""

    yaml = YAML()
    # Used also by auto-formatting in VSCode
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True
    deploy_file_object = yaml.load(deploy_file_template)

    ws_paths = [
        workspace_path
        async for workspace_path in (source_path / "workspaces").iterdir()
        if await workspace_path.is_dir()
    ]
    ws_choices = await prepare_choices(
        [ws_path / "workspace.json" for ws_path in ws_paths]
    )
    workspaces = await questionary.checkbox(
        "Select WS:", choices=ws_choices
    ).ask_async()

    # TODO: select extra queues
    # TODO: select extra hooks
    # TODO: select extra schemas

    # TODO: patching one org with another

    # TODO: name regex for attribute override
    # TODO: attr override helper

    deploy_ws_objects = prepare_deploy_file_objects(workspaces)
    deploy_file_object["workspaces"] = deploy_ws_objects

    queue_paths = await find_queue_paths_for_workspaces(
        [ws["path"].parent for ws in workspaces]
    )
    if not queue_paths:
        display_warning("No queues in the selected workspaces.")
        return

    queue_choices = await prepare_choices(queue_paths, preselect=True)
    queues = await questionary.checkbox(
        "Unselect some of the queues or just continue:", choices=queue_choices
    ).ask_async()
    deploy_queue_objects = prepare_deploy_file_objects(queues)
    deploy_file_object["queues"] = deploy_queue_objects

    hooks = await find_hooks_for_queues(source_path=source_path, queues=queues)
    deploy_hook_objects = prepare_deploy_file_objects(hooks)
    deploy_file_object["hooks"] = deploy_hook_objects

    schemas = await find_schemas_for_queues(source_path=source_path, queues=queues)
    deploy_schema_objects = prepare_deploy_file_objects(schemas)
    deploy_file_object["schemas"] = deploy_schema_objects

    # TODO: let user unselect hooks
    # ! Should this be allowed given the common ignore: true bugs caused by missing hooks

    # TODO: let user select extra queues not in the WS already selected

    # TODO: deploy schemas (??? how to know if they already exist?)
    # TODO: deploy hooks (??? how to know if they already exist?)
    # Must be able to select extra hooks (scheduled hooks are not necessarily related to queues)

    deploy_filepath = await get_deploy_filename(org_path)

    # yaml = YAML()
    # yaml.indent(mapping=2, sequence=4, offset=2)
    # yaml_data = yaml.load(json.dumps(deploy_file_object))
    # yaml_data = yaml.load("")

    # hooks = CS([deploy_file_object["hooks"]])
    # hooks.yaml_set_comment_before_after_key(1, after="\n")

    # TODO: names as comments and not attributes in YAML

    # TODO: Remove path from file, use the source_dir

    # !!!
    # TODO: input file with unselected hooks etc.
    # variables, attributes override, user token owner

    with open(deploy_filepath, "w") as wf:
        yaml.dump(deploy_file_object, wf)


def prepare_deploy_file_objects(objects: list[dict]):
    deploy_objects = []
    for object in objects:
        deploy_representation = {
            "id": object["id"],
            "name": object["name"],
            "path": str(object["path"]),
            "targets": [{"id": None}],
        }
        deploy_objects.append(deploy_representation)
    return deploy_objects


async def find_queue_paths_for_workspaces(ws_paths: list[Path]):
    queue_paths = []
    for ws_path in ws_paths:
        if not (await (ws_path / "queues").exists()):
            continue
        ws_queue_paths = [
            queue_path async for queue_path in (ws_path / "queues").iterdir()
        ]
        for ws_queue_path in ws_queue_paths:
            queue_path_to_file = ws_queue_path / "queue.json"
            if await queue_path_to_file.exists():
                queue_paths.append(queue_path_to_file)

    return queue_paths


async def find_hooks_for_queues(source_path: Path, queues: list[dict]):
    hook_paths = await find_all_hook_paths_in_destination(source_path)
    all_hooks = [
        {**await read_json(hook_path), "path": hook_path} for hook_path in hook_paths
    ]
    found_hook_ids = set()
    found_hooks = []

    for queue in queues:
        hook_urls = queue.get("hooks", [])
        queue_hook_ids = [extract_id_from_url(hook_url) for hook_url in hook_urls]
        for hook_id in queue_hook_ids:
            hook = find_object_by_id(hook_id, all_hooks)
            if hook and hook["id"] not in found_hook_ids:
                found_hook_ids.add(hook["id"])
                found_hooks.append(hook)

    return found_hooks


async def find_schemas_for_queues(source_path: Path, queues: list[dict]):
    schema_paths = await find_all_schema_paths_in_destination(source_path)
    all_schemas = [
        {**await read_json(schema_path), "path": schema_path}
        for schema_path in schema_paths
    ]

    found_schema_ids = set()
    found_schemas = []

    for queue in queues:
        schema_url = queue.get("schema", None)
        schema_id = extract_id_from_url(schema_url)
        schema = find_object_by_id(schema_id, all_schemas)
        if schema and schema["id"] not in found_schema_ids:
            found_schema_ids.add(schema["id"])
            found_schemas.append(schema)

    return found_schemas


async def get_deploy_filename(org_path: Path):
    deploy_filename: str = await questionary.text(
        "Name for the deploy file:", default=settings.DEFAULT_DEPLOY_FILENAME
    ).ask_async()
    deploy_filepath = org_path / deploy_filename

    if await deploy_filepath.exists():
        overwrite = await questionary.confirm(
            f'File "{deploy_filepath}" already exists. Overwrite?', default=False
        ).ask_async()
        if not overwrite:
            return await get_deploy_filename(org_path)

    return deploy_filepath
