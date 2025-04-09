if is_empty(field.item_quantity) or default_to(field.item_quantity, 0) == 0:
    0
else:
    po_qty = default_to(field.item_quantity_match, 0)
    round(float(po_qty) / default_to(field.item_quantity, 0), 2)