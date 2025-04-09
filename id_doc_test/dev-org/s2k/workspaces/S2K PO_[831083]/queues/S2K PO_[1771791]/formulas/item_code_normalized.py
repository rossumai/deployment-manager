code = field.item_code

substitute(r"[^-a-zA-Z0-9 \(\)]", r"", code)