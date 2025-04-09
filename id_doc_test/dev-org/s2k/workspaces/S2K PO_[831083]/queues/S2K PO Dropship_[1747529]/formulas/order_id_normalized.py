if is_set(field.order_id_manual):
    order_id = field.order_id_manual
else:
    order_id = field.order_id
    
substitute(r"[^0-9]", r"", order_id)[:7]