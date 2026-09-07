from graph.nodes.reply_parser import parse_yes_no
from graph.state import IntakeState
from rules_engine.tables.consent_table import get_consent_requirement
from slots.ledger import SlotStatus


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
        reply = parse_yes_no(latest_text)
        if reply == "yes":
            return {"consent": {"required": True, "status": "granted"}}
        if reply == "no":
            return {"consent": {"required": True, "status": "refused"}}
        return {}

    return {}
