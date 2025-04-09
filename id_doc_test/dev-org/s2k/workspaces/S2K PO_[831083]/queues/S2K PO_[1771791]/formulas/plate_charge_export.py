if is_set(field.plate_charge):
    default_to(field.plate_charge, 0)
else:
    default_to(field.plate_charge_from_lines, 0)