import click
import questionary
from anyio import Path
from rossum_api import ElisAPIClient
from ruamel.yaml import YAML, comments


from project_rossum_deploy.commands.template.helpers import (
    find_hooks_for_queues,
    find_queue_paths_for_workspaces,
    find_schemas_for_queues,
    find_ws_paths_for_dir,
    get_deploy_filename,
    prepare_choices,
    prepare_deploy_file_objects,
)
from project_rossum_deploy.utils.consts import (
    display_error,
    display_warning,
    settings,
)
from project_rossum_deploy.utils.functions import (
    coro,
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

# Define anchors in the following way:
x_any_name: &anchor_name
    name: Name from Variable
    another_attr: 4
# You can then use them in the objects by adding '<<: *anchor_name'

workspaces:

queues:

hooks:

schemas:
"""

    yaml = YAML()
    # Used also by auto-formatting in VSCode
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True
    deploy_file_object = yaml.load(deploy_file_template)

    ws_paths = await find_ws_paths_for_dir(source_path)
    ws_choices = await prepare_choices(
        [ws_path / "workspace.json" for ws_path in ws_paths]
    )
    workspaces = await questionary.checkbox(
        "Select WS:", choices=ws_choices
    ).ask_async()

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
    deploy_queue_objects = prepare_deploy_file_objects(queues, include_path=True)
    deploy_file_object["queues"] = deploy_queue_objects

    hooks = await find_hooks_for_queues(source_path=source_path, queues=queues)
    deploy_hook_objects = prepare_deploy_file_objects(hooks)
    deploy_file_object["hooks"] = deploy_hook_objects

    schemas = await find_schemas_for_queues(source_path=source_path, queues=queues)
    deploy_schema_objects = prepare_deploy_file_objects(schemas)
    deploy_file_object["schemas"] = deploy_schema_objects

    # TODO: select extra hooks
    # TODO: select extra schemas

    # TODO: let user unselect hooks
    # ! Should this be allowed given the common ignore: true bugs caused by missing hooks
    # Must be able to select extra hooks (scheduled hooks are not necessarily related to queues)

    # TODO: let user select extra queues not in the WS already selected

    # TODO: patching one org with another

    # TODO: name regex for attribute override
    # TODO: attr override helper

    deploy_filepath = await get_deploy_filename(org_path)

    # !!!
    # TODO: input file with unselected hooks etc.
    # variables, attributes override, user token owner

    with open(deploy_filepath, "w") as wf:
        yaml.dump(deploy_file_object, wf)
