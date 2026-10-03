from app.evaluator import answers_match, normalize_answer


def test_normalize_answer_collapses_whitespace_and_case() -> None:
    text = "  Agent   Reliability\tHUB  "

    assert normalize_answer(text) == "agent reliability hub"


def test_normalize_answer_handles_whitespace_only() -> None:
    text = "   \t\n  "

    assert normalize_answer(text) == ""


def test_normalize_answer_uses_unicode_casefolding() -> None:
    assert normalize_answer("STRASSE") == "strasse"
    assert normalize_answer("Straße") == "strasse"


def test_answers_match_ignores_formatting_differences() -> None:
    assert answers_match("  READY\t", "ready") is True


def test_answers_match_rejects_different_words() -> None:
    assert answers_match("operation succeeded", "operation worked") is False


def test_answers_match_accepts_two_empty_answers() -> None:
    assert answers_match("", "   ") is True
