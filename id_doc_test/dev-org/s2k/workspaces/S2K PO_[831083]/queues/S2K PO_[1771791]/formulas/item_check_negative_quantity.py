if default_to(field.item_quantity_export, 0) < 0:
    show_error('Quantity cannot be negative', field.item_quantity_export)