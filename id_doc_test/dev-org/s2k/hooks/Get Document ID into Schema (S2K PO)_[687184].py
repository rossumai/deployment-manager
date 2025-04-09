from txscript import TxScript, default_to, substitute

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)

    t.field.original_document_id = payload['document']['id']

    return t.hook_response()