# For discount, freight, and similar lines: ignore
if is_empty(field.item_amount) and is_empty(field.item_quantity):
    ''
else:
    calculated_total = default_to(field.item_amount_export, 0) * default_to(field.item_quantity_export, 0)
    captured_total = default_to(field.item_amount_total_export, 0)

    if abs(calculated_total - captured_total) > 0.01:
        show_warning(f'Line total discrepancy detected: Q * Unit price ({calculated_total:.2f}) != Total ({captured_total:.2f})', field.item_amount_total)