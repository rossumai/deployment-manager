if is_set(field.misc_charges):
    default_to(field.misc_charges, 0)
else:
    default_to(field.misc_charges_from_lines, 0)