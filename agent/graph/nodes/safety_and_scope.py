import re

EMERGENCY_PHRASES = [
    "not breathing", "can't breathe", "cant breathe", "unconscious", "unresponsive",
    "seizing", "seizure", "chest pain", "bleeding heavily", "bleeding a lot",
    "can't wake", "cant wake", "turning blue", "call 911", "not moving", "won't wake up",
]

IMMEDIACY_CUES = [
    "right now", "currently", "still not", "help me", "someone help",
    "need an ambulance", "call an ambulance", "call 911 now", "not breathing now",
]

PAST_DISQUALIFIERS = [
    "was ", "were ", "had ", "used to", "years ago", "months ago", "weeks ago",
    "days ago", "back then", "at the time", "at the scene", "after the accident",
    "after the crash", "since the accident", "since then", "history of", " ago",
    "before ", "in the past", "when it happened",
]

def _matches_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)

def _is_emergency(text: str) -> bool:
    lowered = text.lower()
    if _matches_any(lowered, IMMEDIACY_CUES):
        return True
    if _matches_any(lowered, EMERGENCY_PHRASES):
        return not _matches_any(lowered, PAST_DISQUALIFIERS)
    return False