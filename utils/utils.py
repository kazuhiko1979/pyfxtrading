def bool_from_str(text: str) -> bool:
    if text.lower() == 'true':
        return True
    if text.lower() == 'false':
        return False