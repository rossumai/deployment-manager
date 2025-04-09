"""
This custom serverless function example demonstrates showing messages to the
user on the validation screen, updating values of specific fields, and
executing actions on the annotation.

See https://elis.rossum.ai/api/docs/#rossum-transaction-scripts for more examples.
"""

from rossum.lib.api_client import RossumClient, RossumException
from rossum_api import ElisAPIClientSync


def rossum_hook_request_handler(payload: dict) -> dict:
    rossum_client = get_rossum_client(payload)

    hook_id = payload['settings'].get('hook_id', None)
    if not hook_id:
        return {}
   
    rossum_client.request_json(method='POST', url=f"hooks/{hook_id}/invoke")

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