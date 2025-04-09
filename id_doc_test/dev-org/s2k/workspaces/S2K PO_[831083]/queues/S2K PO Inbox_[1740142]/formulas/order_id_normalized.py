import re

if is_set(field.order_id_manual):
    order_id = field.order_id_manual
else:
    order_id = field.order_id


''.join(re.findall(r'\d', order_id))[-7:] if re.findall(r'\d', order_id) else ''