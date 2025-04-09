from decimal import Decimal, ROUND_HALF_UP

def to_decimal(value):
    return Decimal(str(value))

discount = to_decimal(default_to(field.vendor_discount_size, 0))

if not is_empty(field.amount_due_export) and not is_empty(discount):
    (to_decimal(field.amount_due_export) * (discount)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)