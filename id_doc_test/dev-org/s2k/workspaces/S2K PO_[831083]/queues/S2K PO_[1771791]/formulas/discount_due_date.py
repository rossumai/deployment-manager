# Take the same date as "due date for net" when the discount is 0
discount = default_to(field.vendor_discount_size, 0)
if float(discount) == 0:
    field.vendor_net_due_date
else:
    field.vendor_discount_due_date