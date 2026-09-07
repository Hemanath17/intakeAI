from graph.state import IntakeState

CATASTROPHIC_TIERS = {"catastrophic", "fatal"}
MAX_EMPATHY_PAUSES = 2

RELATION_MAP = {
    "child": "mother or father",
    "daughter": "mother",
    "son": "mother",
    "mother": "mother",
    "father": "father",
    "spouse": "spouse",
    "wife": "wife",
    "husband": "husband",
}


def _key(value) -> str:
    if value is None:
        return ""
    return getattr(value, "value", str(value))


def emotional_policy(state: IntakeState) -> dict:
    empathy = state["empathy"]
    severity = state["severity_signal"]

    if empathy.get("pause_active"):
        return {"empathy": {**empathy, "pause_active": False}}

    if not severity.get("new_this_turn"):
        return {}

    if empathy.get("pauses_used", 0) >= MAX_EMPATHY_PAUSES:
        return {}

    if _key(severity.get("tier")) not in CATASTROPHIC_TIERS:
        return {}

    return {
        "empathy": {
            "pause_active": True,
            "pauses_used": empathy.get("pauses_used", 0) + 1,
            "last_event_turn": state["turn_count"],
        },
        "severity_signal": {**severity, "new_this_turn": False},
    }
