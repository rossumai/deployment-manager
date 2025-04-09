from txscript import TxScript

def rossum_hook_request_handler(payload):
    t = TxScript.from_payload(payload)

    # Arrival date:
    t.field.document_arrived_at = payload.get("document").get("arrived_at")

    return t.hook_response()