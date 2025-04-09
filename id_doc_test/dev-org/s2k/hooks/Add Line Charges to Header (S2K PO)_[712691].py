from txscript import TxScript, default_to, substitute, is_set, is_empty
from copy import deepcopy
import dataclasses

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)

    charge_types = payload.get('settings', {}).get("charge_types", {})
    
    for charge_type, gl_codes in charge_types.items():
        total_charge_value = 0
        for row in t.field.line_items:
            if not check_row_gl_in_list(row, gl_codes):
                continue
            total_charge_value += default_to(row.item_amount_total_export, 0)
            
        source_field = t.field._get_field(charge_type)
        source_field.set_value(total_charge_value)
        
    return t.hook_response()
    
def check_row_gl_in_list(row, gl_codes):
    for branch, gl_code, dept in gl_codes:
        if branch and branch != row.item_branch_id_export:
            continue
        if gl_code != row.item_gl_code_export:
            continue
        if dept != row.item_dept_export:
            continue
        return True
    return False