# TODO: differentiate which line item field is referenced (not just the whole subgraph)
def create_node(node: dict):
    graph_node = {
        "id": node["id"],
        "name": node["label"],
        "is_orphan": False,
        "is_hidden": node.get("hidden", False),
        "field_type": "default",
        "tooltip_content": "",
    }

    if node.get("formula", None):
        graph_node["field_type"] = "formula"
        graph_node["tooltip_content"] = f"<pre>{node['formula']}</pre>"
    elif node.get("ui_configuration", {}).get("type", "captured") == "manual":
        graph_node["field_type"] = "manual"
        graph_node["tooltip_content"] = "Manual field"
    elif (
        node.get("ui_configuration", {}).get("type", "captured") == "data"
        and node["type"] == "enum"
    ):
        graph_node["field_type"] = "data_matching"
    elif node.get("ui_configuration", {}).get("type", "captured") == "data":
        graph_node["field_type"] = "data"
        # TODO: extension type in tooltip
    else:
        graph_node["field_type"] = "captured"
        graph_node["tooltip_content"] = "Captured field"

    return graph_node


def create_link(source: str, target: str):
    return {"source": source, "target": target}


def find_node(node_id: str, graph: dict):
    for node in graph["nodes"]:
        if node["id"] == node_id:
            return node
    return None
