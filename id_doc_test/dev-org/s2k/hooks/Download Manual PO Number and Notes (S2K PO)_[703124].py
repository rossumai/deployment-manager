from txscript import TxScript, default_to, substitute, is_empty
from rossum.lib.api_client import RossumClient, RossumException

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)

    metadata = payload['annotation'].get('metadata', {})
   
    order_id_manual = metadata.get('order_id_manual', "")
    notes = metadata.get('notes', "")
    
    t.field.order_id_manual = order_id_manual
    t.field.notes = notes

    return t.hook_response()