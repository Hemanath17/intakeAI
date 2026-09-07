import re

AGREE_PHRASES = [
    "yes", "yeah", "yep", "correct", "that's right", "sure",
    "that's fine", "go ahead", "okay", "ok", "no problem", "right",
]

REFUSE_PHRASES = [
    "no", "nope", "that's wrong", "incorrect", "not right",
    "i don't want", "i do not want", "i'd rather not", "not comfortable",
    "prefer not", "don't record",
]


def matches_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in phrases)


def parse_yes_no(text: str) -> str:
    if matches_any(text, AGREE_PHRASES):
        return "yes"
    if matches_any(text, REFUSE_PHRASES):
        return "no"
    return "unclear"
