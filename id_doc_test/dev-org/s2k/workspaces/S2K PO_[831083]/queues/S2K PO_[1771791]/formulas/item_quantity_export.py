received = float(default_to(field.item_quantity_received_match, '.00'))
max_billable = float(default_to(field.item_quantity_open, '.00'))
captured = default_to(field.item_quantity, 0)

use_converted_message = False
if is_set(field.item_order_invoice_quantity_ratio_match) and field.item_use_ratio == 'true':
    ratio = float(field.item_order_invoice_quantity_ratio_match)
    if ratio != 0:
        use_converted_message = True
        show_warning(f'Quantity has been converted by order/invoice ratio of {ratio}', field.item_quantity)
        captured = captured * ratio
    

# No tolerance
tolerance = 0

if field.item_match_po_flag == 'false':
    captured
elif captured <= max_billable or abs(captured - max_billable) <= tolerance:
    captured
else:
    calculated = min(captured, max_billable)
    show_warning(f'Quantity has been {'converted and ' if use_converted_message else ''} lowered to the maximum billable quantity', field.item_quantity_export)
    if is_empty(field.notes):
        pass
        show_error(f'In the Internal Notes Section, please be sure to note the buyer who is approving this variance prior to confirming.', field.notes)
    calculated