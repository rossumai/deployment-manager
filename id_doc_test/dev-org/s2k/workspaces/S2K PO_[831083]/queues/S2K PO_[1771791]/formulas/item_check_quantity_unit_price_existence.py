if is_empty(field.item_amount):
    show_warning('Missing invoice unit price', field.item_amount)

if is_empty(field.item_quantity):
    show_warning('Missing invoice quantity', field.item_quantity)