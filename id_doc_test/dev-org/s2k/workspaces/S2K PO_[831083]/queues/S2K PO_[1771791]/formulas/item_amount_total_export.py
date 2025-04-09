# Convert export quantity string to float, default to 0 if empty or invalid
quantity = float(str(default_to(field.item_quantity_export, '0')).replace(',', '')) if not is_empty(field.item_quantity_export) else 0

# Convert export unit price string to float, default to 0 if empty or invalid
unit_price = float(str(default_to(field.item_amount_export, '0')).replace(',', '')) if not is_empty(field.item_amount_export) else 0

# For non-inventory lines, there might not be quantity and unit price
if is_empty(field.item_order_match):
    field.item_amount_total
else:
    round(quantity * unit_price, 2)