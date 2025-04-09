if is_set(field.rebate):
    val = default_to(field.rebate, 0)
else:
    val = default_to(field.rebate_from_lines, 0)

-abs(val)