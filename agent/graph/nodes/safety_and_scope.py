from graph.state import IntakeState, Phase
EMERGENCY_PHRASES = [
    "not breathing", "can't breathe", "unconscious", "unresponsive",
    "seizing", "seizure", "chest pain", "bleeding heavily",
    "can't wake", "turning blue", "call 911", "not moving",
]
def _is_emergency(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in EMERGENCY_PHRASES)

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