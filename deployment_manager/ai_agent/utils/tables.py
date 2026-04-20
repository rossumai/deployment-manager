def format_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    string_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in string_rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    top = "┌" + "┬".join("─" * (width + 2) for width in widths) + "┐"
    mid = "├" + "┼".join("─" * (width + 2) for width in widths) + "┤"
    bottom = "└" + "┴".join("─" * (width + 2) for width in widths) + "┘"
    header_row = "│" + "│".join(
        f" {header}{' ' * (widths[index] - len(header))} " for index, header in enumerate(headers)
    ) + "│"
    body_rows = []
    for row in string_rows:
        body_rows.append(
            "│"
            + "│".join(
                f" {cell}{' ' * (widths[index] - len(cell))} " for index, cell in enumerate(row)
            )
            + "│"
        )
    return "\n".join([top, header_row, mid, *body_rows, bottom])
