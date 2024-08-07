import datetime
import json
from anyio import Path
from rich import print
from rich.panel import Panel
from rossum_api.api_client import Resource

import click

from project_rossum_deploy.commands.visualize.hooks import (
    enrich_graph_with_hook_information,
)
from project_rossum_deploy.commands.visualize.schema import (
    create_graph_json_from_schema,
    mark_orphans,
)
from project_rossum_deploy.commands.visualize.utils import create_node
from project_rossum_deploy.common.client import create_and_validate_client
from project_rossum_deploy.common.determine_path import determine_object_type_from_path
from project_rossum_deploy.common.read_write import (
    read_json,
)
from project_rossum_deploy.utils.consts import display_error, settings
from project_rossum_deploy.utils.functions import coro

HTML_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "dummy_visualization.html"
HTML_TEMPLATE_REPLACE_TAG = "DUMMY_DATA"


@click.command(
    name=settings.VISUALIZE_COMMAND_NAME,
    help="""
Creates interactive flowcharts in HTML using D3.js.
               """,
)
@click.argument("path", type=click.Path(path_type=Path))
@click.option(
    "--with-timestamp",
    "-wt",
    default=False,
    is_flag=True,
    help="Commits the pulled changes automatically.",
)
@coro
async def visualize(path: Path, with_timestamp: bool = False, base_path: Path = None):
    try:
        if not base_path:
            base_path = Path(".")

        object_type = determine_object_type_from_path(path)

        match object_type:
            case Resource.Queue:
                flow_chart_json = await create_queue_graph(path)
                visualization_path = (
                    base_path
                    / f"{path.parent.name}{"_" + datetime.datetime.now() if with_timestamp else ""}.html"
                )

            case _:
                display_error(
                    f'Invalid object type for visualization "{object_type}". The options are: {[Resource.Schema]}.'
                )
                return

        html_template = open(HTML_TEMPLATE_PATH, "r").read()

        html_template = html_template.replace(
            HTML_TEMPLATE_REPLACE_TAG, f"const data = {json.dumps(flow_chart_json)};"
        )

        with open(visualization_path, "w") as wf:
            wf.write(html_template)

        print(Panel(f'Visualization saved as "{visualization_path}".'))
    except Exception as e:
        display_error(f'Error while visualizing object with path "{path}"', e)


async def create_queue_graph(queue_path: Path):
    queue = await read_json(queue_path)

    client = await create_and_validate_client(
        settings.SOURCE_DIRNAME
        if settings.SOURCE_DIRNAME in str(queue_path)
        else settings.TARGET_DIRNAME
    )

    schema = await client.request_json(method="GET", url=queue["schema"])
    graph = await create_graph_json_from_schema(schema)

    for hook_url in queue["hooks"]:
        await enrich_graph_with_hook_information(hook_url, client, graph)

    add_nonexisting_nodes(graph)
    mark_orphans(graph)

    return graph


def add_nonexisting_nodes(graph: dict):
    node_ids = [node["id"] for node in graph["nodes"]]
    for link in graph["links"]:
        if link["source"] not in node_ids:
            graph["nodes"].append(
                create_node({"id": link["source"], "label": link["source"]})
            )
        if link["target"] not in node_ids:
            graph["nodes"].append(
                create_node({"id": link["target"], "label": link["target"]})
            )
