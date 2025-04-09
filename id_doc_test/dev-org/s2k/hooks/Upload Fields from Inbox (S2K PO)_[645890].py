"""
This custom serverless function example demonstrates showing messages to the
user on the validation screen, updating values of specific fields, and
executing actions on the annotation.

See https://elis.rossum.ai/api/docs/#rossum-transaction-scripts for more examples.
"""

from rossum.lib.api_client import RossumClient, RossumException
from rossum_api import ElisAPIClientSync


def rossum_hook_request_handler(payload: dict) -> dict:
    if payload['event'] != 'annotation_status' or payload['action'] != 'changed' or payload['annotation']['status'] != 'confirmed':
        return {}
    
    rossum_client = get_rossum_client(payload)
    annotation = rossum_client.retrieve_annotation(
        payload["annotation"]["id"], sideloads=["content"]
    )
    
    annotation_content= annotation.content
    order_id_manual = find_by_schema_id(annotation_content, 'order_id_manual')[0].get('content', {}).get('value', None)
    notes = find_by_schema_id(annotation_content, 'notes')[0].get('content', {}).get('value', None)


    annotation_content= annotation.content

    bounding_boxes = {
        "order_id": find_by_schema_id(annotation_content, "order_id")[0]
    }
    res = rossum_client.update_part_annotation(
        payload["annotation"]["id"],
        data={
            "metadata": {
                **payload["annotation"].get("metadata", {}),
               "bounding_boxes": bounding_boxes,
                "order_id_manual": order_id_manual,
                "notes": notes,
            }
        },
    )

    return {}


def get_rossum_client(payload: dict):
    rossum_client = ElisAPIClientSync(
        token=get_auth_token_from_payload(payload),
        base_url=payload["base_url"] + "/api/v1",
    )
    return rossum_client


def get_auth_token_from_payload(payload: dict) -> str:
    auth_token = payload.get("rossum_authorization_token")
    if not auth_token:
        raise HookConfigurationError(
            f"Authorization token not found in the payload. Configure Rossum API access at {payload['hook']}."
        )
    return auth_token


def find_by_schema_id(content, schema_id: str):
    accumulator = []
    for node in content:
        if node["schema_id"] == schema_id:
            accumulator.append(node)
        elif "children" in node:
            accumulator.extend(find_by_schema_id(node["children"], schema_id))

    return accumulator