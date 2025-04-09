from txscript import TxScript, default_to, substitute, is_set, is_empty
from copy import deepcopy
import dataclasses

def rossum_hook_request_handler(payload: dict) -> dict:
    t = TxScript.from_payload(payload)

    total_price_variance = 0
    total_quantity_variance = 0
    for row in t.field.line_items:
        max_allowed_quantity = float(default_to(row.item_quantity_open, '.00'))
        captured = default_to(row.item_quantity_export, 0)
        
        po_unit_price = float(default_to(row.item_amount_base_match.value, '0').replace(',', '.'))
        invoice_unit_price = float(default_to(row.item_amount_export, '0'))
        
        
        if is_set(row.item_order_invoice_quantity_ratio_match) and row.item_use_ratio == 'true':
            ratio = float(row.item_order_invoice_quantity_ratio_match)
            if ratio != 0:
                captured = captured * ratio    
        
        
        extra_quantity = captured - max_allowed_quantity
        if extra_quantity > 0:
            total_quantity_variance += extra_quantity * po_unit_price

    
        extra_price = invoice_unit_price - po_unit_price
        total_price_variance += captured * extra_price
            
    t.field.inventory_price_variances = round(total_price_variance, 2)
    t.field.inventory_quantity_variances = round(total_quantity_variance, 2)
        
    return t.hook_response()