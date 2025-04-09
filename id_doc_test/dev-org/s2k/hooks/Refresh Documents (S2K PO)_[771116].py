from txscript import TxScript, default_to, substitute
from rossum_api import ElisAPIClient, APIClientError
import asyncio
import requests
import json

def format_pipeline(order_id):
    return  [
              {
                "$addFields": {
                  "PO Number": {
                    "$toString": "$PO Number"
                  }
                }
              },
              {
                "$match": {
                  "PO Number": order_id
                }
              }
            ]
          

def rossum_hook_request_handler(payload: dict) -> dict:
    return asyncio.run(main(payload))

async def main(payload: dict) -> dict:
    # init variables
    token = payload["rossum_authorization_token"]
    settings = payload["settings"]
    base_url = payload["base_url"]
    collection_name = settings["collection_name"]
    ds_url = f"{base_url}/svc/data-storage/api/v1"
    queue_ids= settings.get('queue_ids', [])
    
    client = get_rossum_client(payload)
    
    annotation_ids = []
    async for annotation in client.list_all_annotations(queue='1771791', status='to_review,postponed'):
        annotation_ids.append(annotation.id)
        
    for annotation_id in annotation_ids:
        annotation_content = await client.request_json(method='GET', url=f'annotations/{annotation_id}/content')
        
        receipts_flag = find_by_schema_id(annotation_content['content'], 'receipts_flag')
        #if not receipts_flag or receipts_flag[0]['content']['value'] == 'Received':
        #    continue
        
        po_number = find_by_schema_id(annotation_content['content'], 'order_id_normalized')
        if not po_number or not po_number[0]['content']['value']:
            continue
        
        res = await find_in_data_storage_collection(collection_name, format_pipeline(po_number[0]['content']['value']), token, ds_url, {})
        
        if not res.get('result', []):
            continue
        
        receipts_flag_extension = find_by_schema_id(annotation_content['content'], 'receipts_flag_extension')
        
        if not receipts_flag_extension or not receipts_flag_extension[0].get('id', None):
            continue
        
        print(receipts_flag_extension[0] )
        
        updated_content = {**receipts_flag_extension[0]['content'], "value": "true" }
        updated_operation = create_replace_operation(receipts_flag_extension[0], updated_content)
        
        annotation_content = await client.request_json(method='POST', url=f'annotations/{annotation_id}/content/operations', json={'operations': [updated_operation]})
        
    return {}
    
async def find_in_data_storage_collection(collection_name, query, token, ds_url, sort):
    payload = {"collectionName": collection_name, "pipeline": query, "sort": sort}
    header = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    try:
        req = await asyncio.to_thread(requests.post, url=f"{ds_url}/data/aggregate", json=payload, headers=header, timeout=20)
    except Exception as ex:
        return str(ex)

    return json.loads(req.text)

def create_replace_operation(datapoint: dict, content: dict, validation_sources: list = []):
    return {
        "op": "replace",
        "id": datapoint['id'],
        "value": {
            "content": content,
            "validation_sources": validation_sources
        },
    }
    
    
def get_rossum_client(payload: dict):
    rossum_client = ElisAPIClient(
        token=get_auth_token_from_payload(payload),
        base_url=payload["base_url"] + "/api/v1",
    )
    return rossum_client


def get_auth_token_from_payload(payload: dict) -> str:
    auth_token = payload.get("rossum_authorization_token")
    if not auth_token:
        raise Exception(
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