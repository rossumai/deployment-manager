q = default_to(field.item_quantity_match, 0)
price = default_to(field.item_amount_base_match, "0")
float(q) * float(price.replace(",", "."))

# q = float(default_to(field.item_quantity_match, 0))
# price = float(default_to(field.item_amount_base_match, 0))
# q * price