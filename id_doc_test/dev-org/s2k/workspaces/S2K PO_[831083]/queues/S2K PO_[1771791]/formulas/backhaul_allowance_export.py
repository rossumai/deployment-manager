if is_set(field.backhaul_allowance):
    val = default_to(field.backhaul_allowance, 0)
else:
    val = default_to(field.backhaul_allowance_from_lines, 0)
    
-abs(val)