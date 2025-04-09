"""
This custom serverless function example demonstrates showing messages to the
user on the validation screen, updating values of specific fields, and
executing actions on the annotation.

See https://elis.rossum.ai/api/docs/#rossum-transaction-scripts for more examples.
"""

from txscript import TxScript, default_to, substitute, is_empty
from rossum.lib.api_client import RossumClient, RossumException

def rossum_hook_request_handler(payload: dict) -> dict:
    rossum_client = get_rossum_client(payload)

    metadata = payload['annotation'].get('metadata', {})
    content = payload['annotation']['content']
 
    operations = []
    for schema_id, field_data in metadata.get('bounding_boxes', {}).items():
        try:
            datapoint = find_by_schema_id(content, schema_id)[0]
            operation = create_replace_operation(datapoint, field_data['content'], field_data['validation_sources'])
            operations.append(operation)
        except Exception as e:
            print(f'Could not find schema_id {schema_id} in annotation, skipping patching its bounding box.')

    return {"messages": [], "operations": operations}
    
def get_rossum_client(payload: dict) -> RossumClient:
    rossum_client = RossumClient(None, payload["base_url"] + "/api/v1")
    rossum_client.token = get_auth_token_from_payload(payload)
    return rossum_client


def get_auth_token_from_payload(payload: dict) -> str:
    auth_token = payload.get("rossum_authorization_token")
    if not auth_token:
        raise HookConfigurationError(
            f"Authorization token not found in the payload. Configure Rossum API access at {payload['hook']}."
        )
    return auth_token
    
    
def create_replace_operation(datapoint: dict, content: dict, validation_sources: list):
    return {
        "op": "replace",
        "id": datapoint['id'],
        "value": {
            "content": content,
            "validation_sources": validation_sources
        },
    }
    
def find_by_schema_id(content, schema_id: str):
    accumulator = []
    for node in content:
        if node["schema_id"] == schema_id:
            accumulator.append(node)
        elif "children" in node:
            accumulator.extend(find_by_schema_id(node["children"], schema_id))

    return accumulator