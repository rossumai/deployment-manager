from txscript import TxScript, default_to, substitute, is_set
from copy import deepcopy
import dataclasses

DISCOUNT_VIRTUAL_LINE_TYPE = "discount"

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)

    total_discount = 0
    existing_row_index = None
    for row in t.field.line_items:
        # Line has a discount column
        if is_set(row.item_amount_discount):
            total_discount += abs(row.item_amount_discount)
        # The discount line was already added previously -> update
        if is_set(row.flag_virtual_discount_line) and row.flag_virtual_discount_line == DISCOUNT_VIRTUAL_LINE_TYPE:
            existing_row_index = row._index
            
    if existing_row_index is not None:
        t.field.line_items.pop(existing_row_index)
            
    if total_discount == 0:
        return t.hook_response()
    
    discount_row = {}
    # Assumption: all lines should be from the same PO = same location = same branch
    branches = t.field.item_branch_id_normalized.all_values
    discount_row["item_branch_id_extension"] = branches[0] if len(branches) else ""
    discount_row["item_gl_code_extension"] = '510000'
    discount_row["item_dept_extension"] = '00'
    discount_row["item_amount_total"]= -total_discount
    discount_row["flag_virtual_discount_line"]= DISCOUNT_VIRTUAL_LINE_TYPE
    
    t.field.line_items.append(discount_row)
    response = t.hook_response()
    
     # Does not work because of formula fields being populated
    schema_ids_to_keep = list(discount_row.keys())
    add_operation_index = 0 if existing_row_index is None else 1
    response['operations'][add_operation_index]['value'] = [op for op in response['operations'][add_operation_index]['value'] if op['schema_id'] in schema_ids_to_keep]
    
    return response