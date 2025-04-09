import decimal

subtotal = decimal.Decimal(str(default_to(field.subtotal, 0))) 
calculated_total =  decimal.Decimal(str(default_to(field.amount_due_export, 0))) 
header_total = decimal.Decimal(str(default_to(field.amount_due, 0)))
if abs(calculated_total - header_total) > decimal.Decimal('0.01'):
    message = f'Sum of inventory items + non-inventory items ({subtotal} + {calculated_total-subtotal} = {calculated_total}) does not equal the amount due on document ({header_total})'
    show_warning(message, field.amount_due_export)
    automation_blocker(message)