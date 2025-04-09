# Get all PO line numbers and their corresponding line item positions
line_numbers_with_positions = []
for pos, line in enumerate(field.line_items):
    if is_empty(line.item_order_line_number):
        continue
    line_numbers_with_positions.append((pos + 1, line.item_order_line_number))

# Get current line's PO line number
current_line_number = field.item_order_line_number

# Find all positions (line item numbers) with the same PO line number
matching_positions = [str(pos) for pos, line_num in line_numbers_with_positions if line_num == current_line_number] if not is_empty(current_line_number) else []


# Show warning with line item numbers if duplicates exist
if len(matching_positions) > 1:
    message = f'Same PO line number found in invoice lines: {", ".join(matching_positions)}'
    show_warning(message, field.item_order_match)
    automation_blocker(message, field.item_order_match)