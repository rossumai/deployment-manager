if is_set(field.merchant_tax):
    default_to(field.merchant_tax, 0)
else:
    default_to(field.merchant_tax_from_lines, 0)