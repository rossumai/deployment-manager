from txscript import TxScript, default_to, substitute, is_set

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)

    amount_due_export = t.field.amount_due_export
    freight_export = t.field.freight_export
    
    if is_set(amount_due_export) and is_set(freight_export) and amount_due_export!=0:
        freight_percentage = round(freight_export/amount_due_export*100,2)
        t.show_info(f'Inbound Freight/Total percentage is: {freight_percentage}%', amount_due_export)
        if freight_percentage > 5 and t.field.notes == "":
            t.show_error(f'Freight % > 5 requires a note.', t.field.notes)
    
    return t.hook_response()