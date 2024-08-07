import re
from project_rossum_deploy.commands.visualize.utils import create_link, create_node
from project_rossum_deploy.common.read_write import find_formula_fields_in_schema


def add_nodes(tree: list, nodes: list):
    for node in tree:
        if node["category"] == "section" or node["category"] == "tuple":
            if "children" in node:
                add_nodes(node["children"], nodes)

        elif node["category"] == "datapoint":
            nodes.append(create_node(node))

        elif node["category"] == "multivalue":
            add_nodes([node["children"]], nodes)


def find_referenced_fields_in_formula(code: str):
    field_pattern = re.compile(r"field\.(\w+)")

    return set(field_pattern.findall(code))


def add_formula_links(schema: list, links: list):
    formulas = find_formula_fields_in_schema(schema)

    for field_id, code in formulas:
        referenced_fields = find_referenced_fields_in_formula(code)

        for referenced_field in referenced_fields:
            links.append(create_link(source=referenced_field, target=field_id))


def mark_orphans(graph: dict):
    sources_targets = set()
    for link in graph["links"]:
        sources_targets.add(link["source"])
        sources_targets.add(link["target"])

    for node in graph["nodes"]:
        if node["id"] not in sources_targets:
            node["is_orphan"] = True


async def create_graph_json_from_schema(schema: dict):
    graph = {
        "directed": True,
        "graph": [],
        "multigraph": False,
        "nodes": [],
        "links": [],
    }

    add_nodes(schema["content"], graph["nodes"])
    add_formula_links(schema["content"], graph["links"])

    return graph
