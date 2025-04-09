if is_set(field.retention_tax):
    default_to(field.retention_tax, 0)
else:
    default_to(field.retention_tax_from_lines, 0)