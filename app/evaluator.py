"""Pure evaluation helpers."""


def normalize_answer(text: str) -> str:
    """Normalize answer formatting for deterministic comparison."""
    return " ".join(text.split()).casefold()


def answers_match(actual: str, expected: str) -> bool:
    """Return whether two answers match after formatting normalization."""
    return normalize_answer(actual) == normalize_answer(expected)
