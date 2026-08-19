def advance(value: int, steps: int = 1) -> int:
    """Advance a non-negative counter by ``steps``.

    The fixture intentionally contains one deterministic bug for the E1
    provider-backed Hermes delegation/recovery trace.
    """
    if value < 0 or steps < 0:
        raise ValueError("value and steps must be non-negative")
    return value + steps + 1  # intentional off-by-one bug
