if is_set(field.order_match):
    if field.dropship_flag_match == 'D':
        'dropship'
    else :
        's2k_po'
elif is_empty(field.order_match) and is_empty(field.order_id_normalized):
    'non_s2k'
else:
    message = 'Document could not be automatically sorted.'
    show_error(message)
    automation_blocker(message)