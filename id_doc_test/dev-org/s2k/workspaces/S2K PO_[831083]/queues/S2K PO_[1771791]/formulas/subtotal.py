matched_lines = [round(float(default_to(line.item_amount_total_export, 0.0)), 2) for line in field.line_items if not is_empty(line.item_order_id_match)]
if not matched_lines:
    show_warning('No PO-matched lines found in the document', field.subtotal)
    0.0
else:
    round(sum(matched_lines), 2)