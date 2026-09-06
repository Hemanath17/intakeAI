from graph.state import IntakeState
from slots.ledger import mark_asked
FIXED_REPLIES = {
    "request_consent": (
        "Before we continue, I want to let you know this call is being transcribed by an AI assistant. Is that alright with you?"
    ),
    "consent_refused_close": (
        "I understand. Since we're not able to continue without your consent to be transcribed, "
        "I'd recommend calling our office directly so a team member can assist you. Thank you for calling."
    ),
}

def compose_reply_stub(next_action: str, pending_slot: str = None) -> str:
    if next_action in ("ask_slot", "reask"):
        return f"Could you tell me about {pending_slot}?"
    if next_action == "confirm_jurisdiction":
        return "Got it — just to confirm, that's the state I have on file, correct?"
    if next_action == "readback":
        return "Let me read back what I have so far to make sure it's correct."
    if next_action == "close":
        return "Thank you for sharing all of that. Our team will follow up with you shortly."
    return "Could you tell me more about that?"

def compose_reply(state: IntakeState) -> dict:
    next_action = state["next_action"]
    pending_slot = state["pending_slot"]

    if next_action in FIXED_REPLIES:
        return {"reply": FIXED_REPLIES[next_action]}

    reply_text = compose_reply_stub(next_action, pending_slot)

    ledger = state["ledger"]
    if next_action in ("ask_slot", "reask") and pending_slot:
        mark_asked(ledger, pending_slot, state["turn_count"])

    return {"reply": reply_text, "ledger": ledger}