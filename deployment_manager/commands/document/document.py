import asyncio
import click
from anyio import Path

from deployment_manager.commands.deploy.subcommands.template.helpers import (
    find_hooks_for_queues,
    find_queue_paths_for_workspaces,
    find_ws_paths_for_dir,
    get_schema_for_queue,
)

from deployment_manager.commands.document.llm_helper import LLMHelper
from deployment_manager.common.read_write import (
    read_json,
    read_prd_project_config,
    read_txt,
    write_txt,
)
from deployment_manager.utils.consts import display_info, settings, display_warning

from deployment_manager.utils.functions import (
    coro,
    find_all_hook_paths_in_destination,
)


@click.command(
    name=settings.DOCUMENT_COMMAND_NAME,
    help="""Create documentation""",
)
@click.argument(
    "destinations",
    nargs=-1,
    type=click.Path(path_type=Path),
)
@coro
async def generate_documentation_wrapper(
    destinations: tuple[Path],
    project_path: Path = None,
):
    await generate_documentation(destinations=destinations, project_path=project_path)


async def generate_documentation(destinations: tuple[Path], project_path: Path):
    if not destinations:
        display_warning(
            f"No destinations specified to {settings.DOWNLOAD_COMMAND_NAME}."
        )
        return

    if not project_path:
        project_path = Path("./")

    for destination in destinations:
        if not await (project_path / destination).exists():
            display_warning(
                f"Directory {project_path / destination} does not exist - skipping."
            )
            continue

        documentator = DirectoryDocumentator(
            dir_subdir=str(destination), project_path=project_path
        )
        await documentator.document_organization()


class DirectoryDocumentator:
    def __init__(self, dir_subdir: str, project_path: Path):
        self.name = dir_subdir
        self.project_path = project_path
        self.model = LLMHelper()
        self.semaphore = asyncio.Semaphore(10)

        self.hook_docs = {}
        self.schema_id_docs = {}
        self.queue_docs = {}

    @property
    def org_path(self):
        return self.project_path / self.name

    async def limited_run(self, func, *args, **kwargs):
        async with self.semaphore:
            return await func(*args, **kwargs)

    async def document_organization(self):
        # Collect objects
        queues = await self.gather_queues()

        # TODO: allow multiple subdirs

        for queue in queues:
            await self.document_queue(queue)

        # Check if the doc for an object is not already created
        # (Allow to run only second/third stage)

        # Run for individual objects
        # Decide which template to use
        # Populate field
        # helper = LLMHelper()

        # Merge for each queue

    async def gather_queues(self):
        project_config = await read_prd_project_config(self.project_path)

        # org = project_config.get("directories", {}).get(self.name)
        # subdirs = org.get("subdirectories", {})

        # workspace_paths = []
        # for subdir in subdirs:
        # subdir_workspaces = await find_ws_paths_for_dir(self.org_path / subdir)
        # workspace_paths.extend(subdir_workspaces)

        workspace_paths = await find_ws_paths_for_dir(self.org_path)
        queue_paths = await find_queue_paths_for_workspaces(workspace_paths)
        queues = []

        for queue_path in queue_paths:
            queue = await read_json(queue_path)
            queue["path"] = queue_path
            queues.append(queue)

        return queues

    async def document_queue(self, queue: dict):
        # TODO: skip what is cached in local folder
        # TODO: true async IO operations
        # TODO: display progress / what is being documented
        # TODO: error handling
        # TODO: cache objects by queue ID

        display_info(
            f"Documenting queue [green]{queue.get('name', 'unkonwn-queue')}[/green] ([purple]{queue.get('id', 'unknown-id')}[/purple])"
        )

        inbox_path = queue["path"].with_stem("inbox")
        inbox = await read_json(inbox_path)
        queue["email"] = inbox["email"]

        hook_documentations_base_path = (
            self.org_path / "documentation" / str(queue["id"]) / "hooks"
        )
        hooks = await find_hooks_for_queues(self.org_path, queues=[queue])
        await asyncio.gather(
            *[
                self.limited_run(
                    self.document_hook, hook, hook_documentations_base_path
                )
                for hook in hooks
            ]
        )

        schema_documentations_base_path = (
            self.org_path / "documentation" / str(queue["id"]) / "schema"
        )
        schema_path = queue["path"].with_stem("schema")
        schema = await read_json(schema_path)
        await self.document_schema_ids(schema, schema_documentations_base_path)

        template_path = Path(__file__).parent / "templates" / "queue.txt"
        template = await read_txt(template_path)

        hook_documentations = ""
        async for hook_doc_path in hook_documentations_base_path.iterdir():
            hook_documentations += await read_txt(hook_doc_path) + "\n\n"

        schema_documentations = ""
        async for schema_doc_path in schema_documentations_base_path.iterdir():
            schema_documentations += await read_txt(schema_doc_path) + "\n\n"

        queue_documentation = await self.model.run(
            template.format(
                queue_json=queue,
                hook_documentations=hook_documentations,
                schema_documentations=schema_documentations,
            )
        )
        queue_documentation += (
            "\n\n ## 4. Extensions documentation" + hook_documentations
        )

        self.queue_docs[queue["id"]] = queue_documentation
        await write_txt(
            self.org_path / "documentation" / "queue" / f"{queue['id']}.txt",
            queue_documentation,
        )

    async def document_hook(self, hook: dict, base_path: Path):
        # TODO: what hook is it? choose template...

        # TODO: run after

        hook_path = base_path / f"{hook['id']}.txt"
        if await hook_path.exists():
            return

        template_path = Path(__file__).parent / "templates" / "generic_extension.txt"
        template = await read_txt(template_path)

        hook_documentation = await self.model.run(
            template.format(attributes=hook, run_after=[])
        )

        self.hook_docs[hook["id"]] = hook_documentation
        await write_txt(
            hook_path,
            hook_documentation,
        )

    async def document_schema_ids(self, schema: dict, base_path: Path):
        datapoints = extract_datapoints(schema)
        await asyncio.gather(
            *[
                self.limited_run(self.document_schema_id, datapoint, base_path)
                for datapoint in datapoints
            ]
        )

    async def document_schema_id(self, schema_id: dict, base_path: Path):
        schema_id_path = base_path / f"{schema_id['id']}.txt"

        if await schema_id_path.exists():
            return

        # TODO: data-matching field recognize
        template = await self.get_template_for_schema_id(schema_id)

        schema_id_documentation = await self.model.run(
            template.format(schema_id=schema_id)
        )

        self.schema_id_docs[schema_id["id"]] = schema_id_documentation
        await write_txt(
            schema_id_path,
            schema_id_documentation,
        )

    async def get_template_for_schema_id(self, schema_id: dict):
        type = get_datapoint_type(schema_id)

        template_path = Path(__file__).parent / "templates"
        match type:
            case "manual":
                template_path = template_path / "generic_field.txt"
            case "captured":
                template_path = template_path / "captured_field.txt"
            case "formula":
                template_path = template_path / "formula_field.txt"
            case _:
                template_path = template_path / "formula_field.txt"

        return await read_txt(template_path)


def extract_datapoints(obj):
    """Recursively yield all dicts with category='datapoint'."""
    if isinstance(obj, dict):
        if obj.get("category") == "datapoint":
            yield obj
        for value in obj.values():
            yield from extract_datapoints(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from extract_datapoints(item)


def get_datapoint_type(datapoint: dict):
    if datapoint.get("category") != "datapoint":
        return None
    ui_cfg = datapoint.get("ui_configuration", {})
    dp_type = ui_cfg.get("type")

    if dp_type == "data_matching":
        return None
    return dp_type or "manual"
