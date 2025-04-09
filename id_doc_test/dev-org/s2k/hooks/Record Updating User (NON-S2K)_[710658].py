"""
This custom serverless function example demonstrates showing messages to the
user on the validation screen, updating values of specific fields, and
executing actions on the annotation.

See https://elis.rossum.ai/api/docs/#rossum-transaction-scripts for more examples.
"""
from rossum.lib.api_client import RossumClient
from txscript import TxScript, default_to, substitute

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)
    annotation_content = payload['annotation']['content']
    client = get_rossum_client(payload)
    ignored_user_ids = payload.get('settings', {}).get('ignored_user_ids', [])
    
    modified_by_url = payload['annotation']['modified_by']
    modified_by_id = modified_by_url.split('/')[-1]
    
    print(modified_by_url)
    print(modified_by_id)
    
    if modified_by_id in ignored_user_ids:
        return t.hook_response()
        
    try:
        user = client.get_user(modified_by_id)
    except RossumException as e:
        return t.hook_response()
    
    response =  t.hook_response()
    
    for datapoint_id in payload['updated_datapoints']:
        # datapoint = find_by_datapoint_id(annotation_content, datapoint_id)
        parent_datapoints = find_parent_by_datapoint_id(annotation_content, datapoint_id)
        
        # Ignore non-line items
        if not len(parent_datapoints) or parent_datapoints[0]['schema_id'] != 'gl_codes_tuple':
            continue
        

        email_schema_id = find_by_schema_id(parent_datapoints, 'item_last_modified_by_email')[0]
        op = create_replace_operation(email_schema_id, user.get('email', modified_by_url))
        response['operations'].append(op)
        
        # TODO: check if  human-touched datapoint?
        
    
    return response
    
    
def find_by_datapoint_id(content, datapoint_id: str):
    accumulator = []
    for node in content:
        if node["id"] == datapoint_id:
            accumulator.append(node)
        elif "children" in node:
            accumulator.extend(find_by_datapoint_id(node["children"], datapoint_id))

    return accumulator
    
def find_parent_by_datapoint_id(content, datapoint_id: str, parent = None):
    accumulator = []
    for node in content:
        if node["id"] == datapoint_id:
            accumulator.append(parent)
        elif "children" in node:
            accumulator.extend(find_parent_by_datapoint_id(node["children"], datapoint_id, node))

    return accumulator
    
def find_by_schema_id(content, schema_id: str):
    accumulator = []
    for node in content:
        if node["schema_id"] == schema_id:
            accumulator.append(node)
        elif "children" in node:
            accumulator.extend(find_by_schema_id(node["children"], schema_id))

    return accumulator
    
    
def create_replace_operation(datapoint, new_value):
    """
    Create and operation to replace the value of the datapoint with a new value.
    :param datapoint: content of the datapoint
    :param new_value: new value of the datapoint
    :return: dict with replace operation definition (see https://api.elis.rossum.ai/docs/#annotation-content-event-response-format)
    """
    return {
        "op": "replace",
        "id": datapoint["id"],
        "value": {
            "content": {
                "value": new_value,
            }
        },
    }
    
def get_rossum_client(payload: dict) -> RossumClient:
    rossum_client = RossumClient(None, payload["base_url"] + "/api/v1")
    rossum_client.token = get_auth_token_from_payload(payload)
    return rossum_client


def get_auth_token_from_payload(payload: dict) -> str:
    auth_token = payload.get("rossum_authorization_token")
    if not auth_token:
        raise Exception(
            f"Authorization token not found in the payload. Configure Rossum API access at {payload['hook']}."
        )
    return auth_token