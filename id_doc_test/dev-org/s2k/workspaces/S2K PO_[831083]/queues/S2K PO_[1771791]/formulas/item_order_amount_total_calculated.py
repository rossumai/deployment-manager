if is_empty(field.item_quantity) or is_empty(field.item_amount_base_match):
    0
else:
    item_amount_base_match = default_to(field.item_amount_base_match,"0")
    default_to(field.item_quantity, 0) * float(item_amount_base_match.replace(",","."))