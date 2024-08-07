# TODO: differentiate which line item field is referenced (not just the whole subgraph)
def create_node(node: dict):
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
    elif node.get("ui_configuration", {}).get("type", "captured") == "data":
        graph_node["field_type"] = "data"
    else:
        graph_node["field_type"] = "captured"

    return graph_node


def create_link(source: str, target: str):
    return {"source": source, "target": target}
