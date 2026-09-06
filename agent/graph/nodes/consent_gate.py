from graph.state import IntakeState
from rules_engine.tables.consent_table import get_consent_requirement
AGREE_PHRASES = ["yes", "yeah", "sure", "that's fine", "go ahead", "okay", "ok", "fine with that"]
REFUSE_PHRASES = ["no", "i don't want", "i do not want", "i'd rather not", "not comfortable", "prefer not"]

def _check_consent_reply(text: str) -> str:
    lowered = text.lower()
    if any(phrase in lowered for phrase in REFUSE_PHRASES):
        return "refused"
    if any(phrase in lowered for phrase in AGREE_PHRASES):
        return "granted"
    return "unclear"

def consent_gate(state: IntakeState) -> dict:
    consent = state["consent"]
    jurisdiction = state["jurisdiction"]

    if consent["status"] in ("granted", "not_required"):
        return {}

    if not jurisdiction["confirmed"]:
        return {}

    if consent["required"] is None:
        rule = get_consent_requirement(jurisdiction["state_code"])
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