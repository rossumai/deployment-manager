po_price = float(field.item_amount_base_match.value.replace(',', '.')) if not is_empty(field.item_amount_base_match) else None
invoice_price = default_to(field.item_amount, 0)
quantity = default_to(field.item_quantity, 1)

use_converted_message = False
if is_set(field.item_order_invoice_quantity_ratio_match) and field.item_use_ratio == 'true':
    ratio = float(field.item_order_invoice_quantity_ratio_match)
    if ratio != 0:
        use_converted_message = True
        show_warning(f'Unit price has been converted by order/invoice ratio of {ratio}', field.item_amount)
        invoice_price = invoice_price * ratio

if po_price is None:
    invoice_price
else:
    price_diff = abs(invoice_price - po_price)
    total_po_amount = po_price * quantity
    total_invoice_amount = invoice_price * quantity
    total_diff = abs(total_invoice_amount - total_po_amount)
    percent_diff = (price_diff / po_price) * 100 if po_price != 0 else float('inf')
    
    if field.order_dropship_flag_match.value == 'D':
        if invoice_price <= po_price:
            invoice_price
        else:
    
            show_warning('Invoice price exceeds PO price. Using PO price.', field.item_amount_export)
            if is_empty(field.notes):
                show_error(f'In the Internal Notes Section, please be sure to note the buyer who is approving this variance prior to confirming.', field.notes)
            po_price
    elif invoice_price <= po_price or (percent_diff <= 3 and total_diff <= 250):
        invoice_price
    else:

        show_warning(f'Invoice price exceeds PO price by {percent_diff:.1f}%. Using PO price.', field.item_amount_export)
        if is_empty(field.notes):
                show_error(f'In the Internal Notes Section, please be sure to note the buyer who is approving this variance prior to confirming.', field.notes)
        po_price