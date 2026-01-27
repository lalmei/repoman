"""Integer utility functions."""


def is_int(s: str) -> bool:
    """Check if a string is an integer."""
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True
