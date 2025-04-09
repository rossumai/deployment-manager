from decimal import Decimal, ROUND_HALF_UP

def to_decimal(value):
    return Decimal(str(value))

discount = to_decimal(default_to(field.vendor_discount_size, 0))

if discount > 0:
    "DISCOUNT TERM"
elif is_set(field.vendor_terms_match):
    "NET TERM"
else:
  'NO TERM MATCH'