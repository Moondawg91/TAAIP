def is_probable_header_row(row):
    # >=3 non-empty cells and >=2 alphabetic tokens
    if not row: return False
    nonempty = [c for c in row if c not in (None, '')]
    if len(nonempty) < 3: return False
    alpha_tokens = 0
    for cell in nonempty:
        try:
            s = str(cell)
        except Exception:
            continue
        if any(c.isalpha() for c in s):
            alpha_tokens += 1
    return alpha_tokens >= 2
