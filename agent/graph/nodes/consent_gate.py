import re

from graph.state import IntakeState
from rules_engine.tables.consent_table import get_consent_requirement
from slots.ledger import SlotStatus

AGREE_PHRASES = ["yes", "yeah", "yep", "sure", "that's fine", "go ahead", "okay", "ok", "fine with that", "no problem"]
REFUSE_PHRASES = ["no", "nope", "i don't want", "i do not want", "i'd rather not", "not comfortable", "prefer not", "don't record"]


def _matches_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in phrases)


def _check_consent_reply(text: str) -> str:
    if _matches_any(text, AGREE_PHRASES):
        return "granted"
    if _matches_any(text, REFUSE_PHRASES):
        return "refused"
    return "unclear"


def consent_gate(state: IntakeState) -> dict:
    consent = state["consent"]
    caller_state_slot = state["ledger"]["caller_state"]

    if consent["status"] in ("granted", "not_required"):
        return {}

    if caller_state_slot.status != SlotStatus.ANSWERED:
        return {}

    if consent["required"] is None:
        rule = get_consent_requirement(caller_state_slot.value)
        if not rule["requires_all_party_consent"]:
            return {"consent": {"required": False, "status": "not_required"}}
        return {"consent": {"required": True, "status": "pending"}}

    if consent["status"] == "pending":
        latest_text = state["turns"][-1]["text"]
        reply = _check_consent_reply(latest_text)
        if reply == "granted":
            return {"consent": {"required": True, "status": "granted"}}
        if reply == "refused":
            return {"consent": {"required": True, "status": "refused"}}
        return {}

    return {}