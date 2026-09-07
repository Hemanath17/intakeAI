import re

from guardrails.blocklist import (
    ADVISORY_PATTERNS, GENERIC_FALLBACK, MAX_CHARACTERS, MAX_QUESTIONS,
    MAX_SENTENCES, PROMISE_PATTERNS, SAFE_FALLBACKS, VALUE_PATTERNS,
)


class ValidationResult:
    def __init__(self, passed: bool, violations: list[str], safe_text: str = None):
        self.passed = passed
        self.violations = violations
        self.safe_text = safe_text


def _contains_pattern(text: str, patterns: list[str]) -> list[str]:
    lowered = text.lower()
    found = []
    for pattern in patterns:
        if pattern.startswith("\\"):
            if re.search(pattern, lowered):
                found.append(pattern)
        elif re.search(rf"\b{re.escape(pattern)}\b", lowered):
            found.append(pattern)
    return found


def _count_questions(text: str) -> int:
    return text.count("?")


def _count_sentences(text: str) -> int:
    parts = [p for p in re.split(r"[.!?]+", text) if p.strip()]
    return len(parts)


def validate(text: str, pending_slot: str = None) -> ValidationResult:
    violations = []

    if _count_questions(text) > MAX_QUESTIONS:
        violations.append("multiple_questions")
    if _count_sentences(text) > MAX_SENTENCES:
        violations.append("too_many_sentences")
    if len(text) > MAX_CHARACTERS:
        violations.append("too_long")

    if _contains_pattern(text, ADVISORY_PATTERNS):
        violations.append("advisory_language")
    if _contains_pattern(text, VALUE_PATTERNS):
        violations.append("value_prediction")
    if _contains_pattern(text, PROMISE_PATTERNS):
        violations.append("representation_promise")

    if not violations:
        return ValidationResult(passed=True, violations=[])

    safe_text = SAFE_FALLBACKS.get(pending_slot, GENERIC_FALLBACK)
    return ValidationResult(passed=False, violations=violations, safe_text=safe_text)