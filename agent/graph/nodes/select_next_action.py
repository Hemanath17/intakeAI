from graph.state import IntakeState, Phase
from slots.ledger import get_next_unasked, get_reask_targets, is_complete


def select_next_action(state: IntakeState) -> dict:
    consent = state["consent"]
    jurisdiction = state["jurisdiction"]
    ledger = state["ledger"]

    if consent["status"] == "pending":
        return {"next_action": "request_consent", "pending_slot": None}

    if consent["status"] == "refused":
        return {"next_action": "consent_refused_close", "phase": Phase.CLOSE, "pending_slot": None}

    if jurisdiction["needs_confirmation"]:
        return {"next_action": "confirm_jurisdiction", "pending_slot": None}

    reask_targets = get_reask_targets(ledger)
    if reask_targets:
        return {"next_action": "reask", "pending_slot": reask_targets[0]}

    next_unasked = get_next_unasked(ledger)
    if next_unasked:
        return {"next_action": "ask_slot", "pending_slot": next_unasked}

    if is_complete(ledger):
        if state["phase"] != Phase.READBACK:
            return {"next_action": "readback", "phase": Phase.READBACK, "pending_slot": None}
        return {"next_action": "close", "phase": Phase.CLOSE, "pending_slot": None}

    return {"next_action": "ask_slot", "pending_slot": None}