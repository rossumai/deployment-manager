import datetime
import json
import re
from anyio import Path
from rich import print
from rich.panel import Panel
from rossum_api.api_client import Resource

import click

from project_rossum_deploy.common.determine_path import determine_object_type_from_path
from project_rossum_deploy.common.read_write import (
    find_formula_fields_in_schema,
    read_json,
)
from project_rossum_deploy.utils.consts import display_error, settings
from project_rossum_deploy.utils.functions import coro

HTML_TEMPLATE_PATH = Path(__file__).parent.parent / "dummy_visualization.html"
HTML_TEMPLATE_REPLACE_TAG = "DUMMY_DATA"


@click.command(
    name=settings.VISUALIZE_COMMAND_NAME,
    help="""
Creates flowcharts in Markdown that can be displayed using [Mermaid](https://mermaid.js.org/syntax/flowchart.html).
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
    if not base_path:
        base_path = Path(".")

    visualization_path = (
        base_path
        / f"{path.name}{"_" + datetime.datetime.now() if with_timestamp else ""}.html"
    )

    object_type = determine_object_type_from_path(path)

    match object_type:
        case Resource.Schema:
            # flow_chart_str = await visualize_schema(path)
            flow_chart_json = await create_graph_json(path)
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


async def create_graph_json(schema_path: Path):
    schema = await read_json(schema_path)

    graph = {
        "directed": True,
        "graph": [],
        "multigraph": False,
        "nodes": [],
        "links": [],
    }

    add_nodes(schema["content"], graph["nodes"])
    add_formula_links(schema["content"], graph["links"])
    add_nonexisting_nodes(graph)
    mark_orphans(graph)

    return graph


def add_nodes(tree: list, nodes: list):
    for node in tree:
        if node["category"] == "section" or node["category"] == "tuple":
            if "children" in node:
                add_nodes(node["children"], nodes)

        elif node["category"] == "datapoint":
            nodes.append(create_new_node(node))

        elif node["category"] == "multivalue":
            add_nodes([node["children"]], nodes)


def create_new_node(node: dict):
    graph_node = {
        "id": node["id"],
        "name": node["label"],
        "is_orphan": False,
        "is_hidden": node.get("hidden", False),
        "field_type": "default",
    }

    if node.get("formula", None):
        graph_node["field_type"] = "formula"
    elif node.get("ui_configuration", {}).get("type", "captured") == "manual":
        graph_node["field_type"] = "manual"
    elif (
        node.get("ui_configuration", {}).get("type", "captured") == "data"
        and node["type"] == "enum"
    ):
        graph_node["field_type"] = "data_matching"

    return graph_node


def add_formula_links(schema: list, links: list):
    formulas = find_formula_fields_in_schema(schema)

    for field_id, code in formulas:
        referenced_fields = find_referenced_fields_in_formula(code)

        for referenced_field in referenced_fields:
            links.append({"source": referenced_field, "target": field_id})


def add_nonexisting_nodes(graph: dict):
    node_ids = [node["id"] for node in graph["nodes"]]
    for link in graph["links"]:
        if link["source"] not in node_ids:
            graph["nodes"].append(
                create_new_node({"id": link["source"], "label": link["source"]})
            )
        if link["target"] not in node_ids:
            graph["nodes"].append(
                create_new_node({"id": link["target"], "label": link["target"]})
            )


def mark_orphans(graph: dict):
    sources_targets = set()
    for link in graph["links"]:
        sources_targets.add(link["source"])
        sources_targets.add(link["target"])

    for node in graph["nodes"]:
        if node["id"] not in sources_targets:
            node["is_orphan"] = True


def find_graph_node(nodes, node_id: str):
    for node in nodes:
        if node["id"] == node_id:
            return node
    return None


async def visualize_schema(schema_path: Path):
    schema = await read_json(schema_path)

    # Use the same value in memory, a simple string would get copied around
    flow_chart_str = {
        "value": '%%{init: {"flowchart": {"htmlLabels": false}} }%%\nflowchart LR;\n'
    }

    walk_schema_tree(schema["content"], flow_chart_str)
    add_formula_dependencies(schema["content"], flow_chart_str)
    add_classes(flow_chart_str)

    return flow_chart_str["value"]


def walk_schema_tree(tree: list, flow_chart_str: dict, section_name: str = ""):
    for node in tree:
        if node["category"] == "section" or node["category"] == "tuple":
            if "children" in node:
                walk_schema_tree(node["children"], flow_chart_str, node["label"])

        #         elif node["category"] == "tuple":
        #             flow_chart_str["value"] += f"""subgraph {node['id']} [{node['label']}]
        #             direction TB
        # """

        #             if "children" in node:
        #                 walk_schema_tree(node["children"], flow_chart_str)

        #             flow_chart_str["value"] += "end\n\n"

        elif node["category"] == "datapoint":
            flow_chart_str["value"] += f"""{node['id']}(\"`--{section_name}--
            **{node['label']}**\n({node['type']})`\"){':::formula_field' if node.get('ui_configuration', {}).get('type', '') == 'formula' else ''}\n"""

        elif node["category"] == "multivalue":
            # flow_chart_str["value"] += f"""subgraph {node['id']} [{node['label']}]
            # direction LR

            # """

            walk_schema_tree([node["children"]], flow_chart_str, node["label"])

            # flow_chart_str["value"] += "end\n\n"


def add_formula_dependencies(schema: list, flow_chart_str: dict):
    formulas = find_formula_fields_in_schema(schema)

    for field_id, code in formulas:
        referenced_fields = find_referenced_fields_in_formula(code)

        for referenced_field in referenced_fields:
            flow_chart_str["value"] += f"{referenced_field}-->{field_id}\n"

    flow_chart_str["value"] += "\n"


def add_classes(flow_chart_str: dict):
    flow_chart_str["value"] += """classDef formula_field fill:lime\n"""


# TODO: differentiate which line item field is referenced (not just the whole subgraph)
def find_referenced_fields_in_formula(code: str):
    field_pattern = re.compile(r"field\.(\w+)")

    return set(field_pattern.findall(code))
