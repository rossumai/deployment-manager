# if is_set(field.receipts_flag_match) or is_set(field.receipts_flag_extension) and field.receipts_flag_extension == 'true':
if is_set(field.receipts_flag_extension) and field.receipts_flag_extension == 'true':
    'Received'
else:
    'No Receipts'