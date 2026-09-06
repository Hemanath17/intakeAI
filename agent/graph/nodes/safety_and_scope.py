import re

from graph.state import IntakeState, Phase

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


def _classify_scope_stub(text: str) -> dict:
    return {"out_of_scope": False, "advice_request": False}


def safety_and_scope(state: IntakeState) -> dict:
    latest_text = state["turns"][-1]["text"]

    if _is_emergency(latest_text):
        return {
            "phase": Phase.TERMINATED,
            "escalation_summary": "Caller indicated a possible medical emergency. Advised to call 911.",
        }

    scope_result = _classify_scope_stub(latest_text)

    if scope_result["out_of_scope"]:
        return {
            "phase": Phase.CLOSE,
            "escalation_summary": "Caller's matter appears outside this firm's practice areas.",
        }

    return {}