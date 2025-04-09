if is_set(field.freight) and field.order_dropship_flag_match == "D":
    default_to(field.freight, 0)
else:
    default_to(field.dropship_freight_from_lines, 0)