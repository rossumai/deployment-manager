from datetime import datetime, timedelta

if is_empty(field.date_issue):
    ''
elif is_set(field.vendor_discount_day_of_month) and field.vendor_discount_day_of_month  not in ['0', '00', '000']:
    day_of_month = int(default_to(field.vendor_discount_day_of_month, '1'))
    discount_beginning_month = default_to(field.vendor_discount_beginning_month, 'C')
    current_date = field.date_issue
    if discount_beginning_month == 'C':
        datetime(current_date.year, current_date.month, min(day_of_month, (datetime(current_date.year, current_date.month + 1 if current_date.month < 12 else 1, 1) - timedelta(days=1)).day)).date()
    else:
        next_month = current_date.month + 1
        next_year = current_date.year + (next_month > 12)
        next_month = next_month if next_month <= 12 else 1
        datetime(next_year, next_month, min(day_of_month, (datetime(next_year, next_month + 1 if next_month < 12 else 1, 1) - timedelta(days=1)).day)).date()
else:
    field.date_issue + timedelta(days=int(default_to(field.vendor_discount_period, '0')))