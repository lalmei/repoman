def is_int(s: str) -> bool:
    """Check if a string is an integer."""
    try:
        int(s)
        return True
    except ValueError:
        return False
