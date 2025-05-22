import asyncio
from codecs import ignore_errors
from collections import defaultdict
import json
import subprocess
import click
from anyio import Path
from deployment_manager.commands.document.func import find_matching_configurations

from deployment_manager.commands.deploy.subcommands.template.helpers import (
    find_hooks_for_queues,
    find_queue_paths_for_workspaces,
    find_ws_paths_for_dir,
    get_dir_and_subdir_from_user,
    get_hooks_from_user,
    get_queues_from_user,
    get_workspaces_from_user,
)

from deployment_manager.commands.document.llm_helper import LLMHelper
from deployment_manager.common.read_write import (
    read_json,
    read_prd_project_config,
    read_txt,
    write_txt,
)
from deployment_manager.utils.consts import (
    display_error,
    display_info,
    settings,
    display_warning,
)

from deployment_manager.utils.functions import (
    coro,
)


@click.command(
    name=settings.DOCUMENT_COMMAND_NAME,
    help="""Create documentation""",
)
@click.option(
    "--ignore-cache",
    "-i",
    help="Regenerate docs for all objects, even if they have a cached local documentation already.",
    is_flag=True,
    default=False,
)
@coro
async def generate_documentation_wrapper(
    project_path: Path = None, ignore_cache: bool = False
):
    await generate_documentation(project_path=project_path, ignore_cache=ignore_cache)


async def generate_documentation(project_path: Path, ignore_cache: bool):
    if not project_path:
        project_path = Path("./")

    source_dir_and_subdir = await get_dir_and_subdir_from_user(
        project_path=project_path, type="source"
    )

    source_path = project_path / source_dir_and_subdir

    deploy_file_workspaces, selected_ws_paths = await get_workspaces_from_user(
        source_path=source_path,
        interactive=True,
    )

    if not selected_ws_paths:
        return

    deploy_file_queues, selected_queues = await get_queues_from_user(
        deploy_ws_paths=[ws.parent for ws in selected_ws_paths],
        interactive=True,
    )

    if not selected_queues:
        return

    # Currently, hook selection is entirely driven by a specific queue
    # selected_hooks, unselected_hooks = await get_hooks_from_user(
    #     source_path=source_path,
    #     queues=selected_queues,
    #     interactive=True,
    # )

    documentator = DirectoryDocumentator(
        dir_subdir=source_dir_and_subdir,
        project_path=project_path,
        queues=selected_queues,
        ignore_cache=ignore_cache,
    )
    await documentator.document_queues()


class DirectoryDocumentator:
    def __init__(
        self,
        dir_subdir: str,
        queues: list[dict],
        project_path: Path,
        ignore_cache: bool,
    ):
        self.name = dir_subdir
        self.project_path = project_path
        self.model = LLMHelper()
        self.semaphore = asyncio.Semaphore(10)

        self.ignore_cache = ignore_cache

        self.hook_docs = {}
        self.schema_id_docs = defaultdict(dict)
        self.queue_docs = {}

        self.hooks: list[dict]
        self.queues: list[dict] = queues

    # TODO: naming...

    @property
    def org_path(self):
        return self.project_path / self.name

    def hook_documentations_base_path(self, queue_id: str):
        return self.org_path / "documentation" / str(queue_id) / "hooks"

    def schema_documentations_base_path(self, queue_id: str):
        return self.org_path / "documentation" / str(queue_id) / "schema"

    async def limited_run(self, func, *args, **kwargs):
        async with self.semaphore:
            return await func(*args, **kwargs)

    async def document_queues(self):
        try:
            for queue in self.queues:
                await self.document_queue_with_context(queue)

            # TODO: Allow to run only second/third stage

            await self.document_use_case()
        except RuntimeError as e:
            display_error(str(e))

    async def document_use_case(self):
        display_info(f"Documenting use case.")

        use_case_path = self.org_path / "documentation" / "use_case.txt"
        if await use_case_path.exists() and not self.ignore_cache:
            return

        use_case_template_path = Path(__file__).parent / "templates" / "use_case.txt"
        use_case_template = await read_txt(use_case_template_path)

        queue_documentations = ""
        for queue_documentation in self.queue_docs.values():
            queue_documentations += queue_documentation + "\n\n"

        use_case_documentation = await self.model.run(
            use_case_template.format(
                queue_documentations=queue_documentations,
            )
        )

        await write_txt(
            self.org_path / "documentation" / "use_case.txt",
            use_case_documentation,
        )

    async def document_queue_with_context(self, queue: dict):
        # TODO: true async IO operations
        # TODO: display progress / what is being documented
        # TODO: error handling
        # TODO: static analysis for any data schema_id
        # TODO: postprocessing to unify headlines and formatting?

        # TODO: document sorting should be included in the target queue too (not just source)

        # TODO: spot bedrock authorization error before calling run()

        display_info(
            f"Documenting queue [green]{queue.get('name', 'unkonwn-queue')}[/green] ([purple]{queue.get('id', 'unknown-id')}[/purple])"
        )

        # TODO: queue caching check

        # Document inbox's email without having to pass in the whole inbox object to the LLM
        inbox_path = queue["path"].with_stem("inbox")
        inbox = await read_json(inbox_path)
        queue["email"] = inbox["email"]

        hooks = await find_hooks_for_queues(self.org_path, queues=[queue])
        self.hooks = hooks
        await asyncio.gather(
            *[
                self.limited_run(
                    self.document_hook,
                    hook,
                    self.hook_documentations_base_path(queue["id"]),
                )
                for hook in self.hooks
            ]
        )

        # TODO:
        # await self.visualize_extensions_chain()

        schema_path = queue["path"].with_stem("schema")
        schema = await read_json(schema_path)
        await self.document_schema_ids(
            queue["id"],
            schema,
            self.schema_documentations_base_path(queue["id"]),
            self.hook_documentations_base_path(queue["id"]),
        )

        await self.document_queue(queue=queue)

    async def document_queue(self, queue: dict):
        hook_documentations = ""
        async for hook_doc_path in self.hook_documentations_base_path(
            queue["id"]
        ).iterdir():
            if not str(hook_doc_path).endswith("_fe.txt"):
                hook_documentations += await read_txt(hook_doc_path) + "\n\n"

        schema_documentations = ""
        async for schema_doc_path in self.schema_documentations_base_path(
            queue["id"]
        ).iterdir():
            if await schema_doc_path.is_file() and schema_doc_path.suffix == ".txt":
                schema_documentations += await read_txt(schema_doc_path) + "\n\n"

        data_matching_documentations_base_path = (
            self.org_path
            / "documentation"
            / str(queue["id"])
            / "schema"
            / "data_matching"
        )
        data_matching_documentations = ""
        async for (
            data_matching_doc_path
        ) in data_matching_documentations_base_path.iterdir():
            data_matching_documentations += (
                await read_txt(data_matching_doc_path) + "\n\n"
            )

        queue_template_path = Path(__file__).parent / "templates" / "queue.txt"
        queue_template = await read_txt(queue_template_path)

        queue_documentation = await self.model.run(
            queue_template.format(
                queue_json=queue,
                hook_documentations=hook_documentations,
                schema_documentations=schema_documentations,
                data_matching_documentations=data_matching_documentations,
            )
        )
        queue_documentation += (
            "\n\n ## 4. Extensions documentation\n" + hook_documentations
        )

        queue_documentation += (
            "\n\n ## 5. Data matching fields\n" + data_matching_documentations
        )

        self.queue_docs[queue["id"]] = queue_documentation
        await write_txt(
            self.org_path / "documentation" / "queue" / f"{queue['id']}.txt",
            queue_documentation,
        )

    async def document_hook(self, hook: dict, base_doc_path: Path):
        hook_path = base_doc_path / f"{hook['id']}.txt"
        if await hook_path.exists() and not self.ignore_cache:
            return

        display_info(
            f"Documenting hook [green]{hook.get('name', 'unkonwn-hook')}[/green] ([purple]{hook.get('id', 'unknown-id')}[/purple])"
        )

        run_after = self.format_run_after_section(hook)

        queue_names = self.format_queue_names_section(hook)

        template_path = Path(__file__).parent / "templates" / "generic_extension.txt"
        template_path_fe = ""
        image_url = hook.get("extension_image_url", "") or ""
        hook_config_url = hook.get("config", {}).get("url", "") or ""
        if "Document-Sorting" in image_url:
            template_path = Path(__file__).parent / "templates" / "document_sorting.txt"
        elif "Document-Splitting" in image_url:
            template_path = (
                Path(__file__).parent / "templates" / "document_splitting.txt"
            )
        elif "Master-Data-Hub" in image_url:
            template_path = Path(__file__).parent / "templates" / "mdh.txt"
        elif "Duplicate-Handling" in image_url:
            template_path = (
                Path(__file__).parent / "templates" / "duplicate_handling.txt"
            )
        elif "custom-format-templating" in hook_config_url:
            template_path = Path(__file__).parent / "templates" / "mega.txt"
        else:
            template_path_fe = (
                Path(__file__).parent / "templates" / "field_extractor.txt"
            )

        template = (
            await read_txt(template_path)
            + "\nHere are related queues and their names:\n"
            + queue_names
        )

        hook_documentation = await self.model.run(
            template.format(attributes=hook, run_after=run_after)
        )

        self.hook_docs[hook["id"]] = hook_documentation
        await write_txt(
            hook_path,
            hook_documentation,
        )
        if template_path_fe:
            template = await read_txt(template_path_fe)
            template += "\n\r" + str(hook)
            hook_documentation = await self.model.run(template)

            self.hook_docs[hook["id"]] = hook_documentation
            await write_txt(
                base_doc_path / f"{hook['id']}_fe.txt",
                hook_documentation,
            )

    def format_run_after_section(self, hook: dict):
        run_after_urls = hook.get("run_after", [])
        run_after_formatting = ""

        for url in run_after_urls:
            id = url.split("/")[-1]

            for hook in self.hooks:
                if str(hook.get("id", "")) == id:
                    run_after_formatting += (
                        f'{hook.get("name", "unkonwn")} ({hook.get('id', 'no-id')})\n'
                    )
        return run_after_formatting

    def format_queue_names_section(self, hook: dict):
        queue_urls = hook.get("queues", [])
        queue_formatting = ""

        for url in queue_urls:
            id = url.split("/")[-1]

            for queue in self.queues:
                if str(queue.get("id", "")) == id:
                    queue_formatting += (
                        f'{queue.get("name", "unkonwn")} ({queue.get('id', 'no-id')})\n'
                    )
        return queue_formatting

    async def document_schema_ids(
        self, queue_id, schema: dict, base_path: Path, docs_base_path: Path
    ):
        display_info(
            f"Documenting schema [green]{schema.get('name', 'unkonwn-schema')}[/green] ([purple]{schema.get('id', 'unknown-id')}[/purple])"
        )

        datapoints = extract_datapoints(schema)
        await asyncio.gather(
            *[
                self.limited_run(
                    self.document_schema_id,
                    queue_id,
                    datapoint,
                    base_path,
                    docs_base_path,
                )
                for datapoint in datapoints
            ]
        )

    async def visualize_extensions_chain(self):
        extensions_list_formatted = ""
        for hook in self.hooks:
            extensions_list_formatted += (
                f"id: {hook['id']}\nname: {hook['name']}\n{hook['run_after']}\n\n"
            )

        template_path = Path(__file__).parent / "templates" / "extensions_chain.txt"
        template = await read_txt(template_path)
        diagramming_code = await self.model.run(
            template.format(extensions=extensions_list_formatted)
        )

        result = subprocess.run(
            ["python3", "-"], input=diagramming_code, capture_output=True, text=True
        )

    async def document_schema_id(
        self, queue_id: str, schema_id: dict, base_path: Path, hook_docs_base_path: Path
    ):
        schema_id_path = base_path / f"{schema_id['id']}.txt"
        if await schema_id_path.exists() and not self.ignore_cache:
            return

        template, matching_configs = await self.get_template_for_schema_id(
            schema_id, hook_docs_base_path
        )
        template = template.format(schema_id=schema_id)
        if matching_configs:
            template += "\n\r" + json.dumps(matching_configs)
            schema_id_path = base_path / "data_matching" / f"{schema_id['id']}.txt"
        schema_id_documentation = await self.model.run(template)

        self.schema_id_docs[queue_id][schema_id["id"]] = schema_id_documentation
        await write_txt(
            schema_id_path,
            schema_id_documentation,
        )

    async def get_template_for_schema_id(
        self, schema_id: dict, hook_docs_base_path: Path
    ):
        type = get_datapoint_type(schema_id)
        template_path = Path(__file__).parent / "templates"
        matching_configs = []
        additional_mapping = False
        target_schema_id = ""
        input_hook_ids = []
        match type:
            case "manual":
                template_path = template_path / "generic_field.txt"
            case "captured":
                template_path = template_path / "captured_field.txt"
            case "formula":
                template_path = template_path / "formula_field.txt"
            case "data":
                schema_id_id = schema_id["id"]
                matching_configs, additional_mapping, target_schema_id = (
                    find_matching_configurations(self.hooks, schema_id_id)
                )
                # print ("ID: " + str(schema_id_id) + "\n|matching configs: " + json.dumps(matching_configs) + "\n|addmappings: " + str(additional_mapping) + "\n|target_schema_id " + str(target_schema_id))
                if matching_configs and not additional_mapping:
                    template_path = template_path / "matched_field.txt"
                elif additional_mapping:
                    template_path = template_path / "additional_mapping.txt"
                else:
                    async for hook_doc_path in hook_docs_base_path.iterdir():
                        if str(hook_doc_path).endswith("_fe.txt"):
                            hook_doc = await read_txt(hook_doc_path)
                            try:
                                hook_doc_json = json.loads(hook_doc)
                                if schema_id_id in hook_doc_json.get("OUTPUT"):
                                    input_hook_ids.append(
                                        hook_doc_json.get("Extension ID")
                                    )
                            except:
                                pass
                    template_path = template_path / "generic_field.txt"
            case _:
                template_path = template_path / "formula_field.txt"

        template = await read_txt(template_path)
        if additional_mapping and target_schema_id:
            template += target_schema_id
        if input_hook_ids:
            template += f"\n\n The following list of hook IDs {input_hook_ids} is populating this value. Make sure the source hook ID is mentioned in a separate section at the end of the description."
        return template, matching_configs


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
    return dp_type or "manual"
