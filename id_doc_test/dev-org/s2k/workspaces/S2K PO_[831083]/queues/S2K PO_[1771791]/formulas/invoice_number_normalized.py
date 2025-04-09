import re

document_id = field.document_id.replace(' ', '').replace(',', '').upper()

if is_empty(document_id) and is_empty(field.date_issue):
    show_error("If the document does not have an Invoice Number, the system requires the Invoice Date to generate one.", field.invoice_number_normalized)

if is_empty(document_id) and not is_empty(field.date_issue):
    if is_empty(field.annotation_id):
        show_error("Please re-extract the document. If it does not help contact Rossum Support.")
    ''.join([f'{field.date_issue:%m}', f'{field.date_issue:%d}', f'{field.date_issue:%Y}']) + field.annotation_id[-4:]
else:
    alphanumeric = re.sub(r'[^a-zA-Z0-9]', '', document_id)
    numbers_only = re.sub(r'[^0-9]', '', alphanumeric)
    
    if len(document_id) <= 12:
        document_id
    elif len(alphanumeric) <= 12:
        alphanumeric.upper()
    elif len(numbers_only) <= 12:
        numbers_only
    else:
        alphanumeric[-12:].upper()