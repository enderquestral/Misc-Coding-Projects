def one_character_change_away(base_word: str, banned_word: str) -> bool:
    """Return whether exactly one insertion, deletion, or replacement is needed."""
    if abs(len(base_word) - len(banned_word)) > 1:
        return False

    base_index = 0
    banned_index = 0
    changes = 0

    while base_index < len(base_word) and banned_index < len(banned_word):
        if base_word[base_index] == banned_word[banned_index]:
            base_index += 1
            banned_index += 1
            continue

        changes += 1
        if changes > 1:
            return False

        if len(base_word) > len(banned_word):
            base_index += 1
        elif len(base_word) < len(banned_word):
            banned_index += 1
        else:
            base_index += 1
            banned_index += 1

    if base_index < len(base_word) or banned_index < len(banned_word):
        changes += 1

    return changes == 1
