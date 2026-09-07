from graph.nodes.reply_parser import parse_yes_no
from graph.state import IntakeState


def jurisdiction_confirm(state: IntakeState) -> dict:
    jurisdiction = state["jurisdiction"]

    if not jurisdiction.get("needs_confirmation"):
        return {}

    if state.get("next_action") != "confirm_jurisdiction":
        return {}

    latest_text = state["turns"][-1]["text"]
    reply = parse_yes_no(latest_text)

    new_mention = any(
        item.slot_name in ("incident_city", "incident_state")
        for item in state.get("pending_extraction", [])
    )
    rejects_jurisdiction = reply == "no" and new_mention

    if rejects_jurisdiction:
        return {"jurisdiction": {
            "raw_mention": None, "state_code": None,
            "confirmed": False, "needs_confirmation": False,
        }}

    return {"jurisdiction": {**jurisdiction, "confirmed": True, "needs_confirmation": False}}
