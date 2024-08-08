import json
import re
from rossum_api import ElisAPIClient

from project_rossum_deploy.commands.visualize.utils import create_link, find_node
from project_rossum_deploy.utils.consts import display_error


async def enrich_graph_with_hook_information(
    hook_url: str, client: ElisAPIClient, graph: dict
):
    try:
        hook = await client.request_json(method="GET", url=hook_url)

        if recognize_master_data_hub_hook(hook):
            enrich_graph_with_data_matching_information(hook, graph)

    except Exception as e:
        display_error(f'Error while enriching visualization with hook "{hook_url}"', e)


def recognize_master_data_hub_hook(hook: dict) -> bool:
    configurations = hook.get("settings", {}).get("configurations", [])

    if not len(configurations):
        return False

    # If the MDH hook has no configurations, we can consider the hook as non-MDH (no information to gather anyway...)
    if configurations[0].get("source", {}).get("dataset", ""):
        return True


def enrich_graph_with_data_matching_information(hook: dict, graph: dict):
    for configuration in hook["settings"]["configurations"]:
        dataset_name = configuration["source"].get("dataset", "")

        target_schema_ids = [
            configuration["mapping"]["target_schema_id"],
            *[
                ad_mapping["target_schema_id"]
                for ad_mapping in configuration.get("additional_mappings", [])
            ],
        ]

        for query in configuration["source"]["queries"]:
            # TODO: url query
            if query.get("url", ""):
                continue

            mongo_pipeline = query.get("aggregate", query.get("find", []))

            schema_id_pattern = re.compile(r'"\{(\w+)\}"')
            for match in schema_id_pattern.findall(json.dumps(mongo_pipeline)):
                for target_schema_id in target_schema_ids:
                    graph["links"].append(
                        create_link(source=match, target=target_schema_id)
                    )

        for target_schema_id in target_schema_ids:
            node = find_node(target_schema_id, graph)
            if node:
                node["tooltip_content"] = f"Dataset: {dataset_name}"
