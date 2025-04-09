import re

if is_set(field.order_id_manual):
    order_id = field.order_id_manual
else:
    order_id = field.order_id

if len(order_id) > 7:
    order_id = ''.join(re.findall(r'\d', order_id))[-7:] if re.findall(r'\d', order_id) else ''
    message = f'PO Number is not 7-digits long - taking the last 7 digits ({order_id})'
    show_warning(message, field.order_id_manual if is_set(field.order_id_manual) else field.order_id)
    automation_blocker(message, field.order_id_manual if is_set(field.order_id_manual) else field.order_id)

order_id