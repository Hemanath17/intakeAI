import time
from graph.state import IntakeState, Turn

def emit(state: IntakeState) -> dict:
    reply_text = state["reply"]

    agent_turn = Turn(role="agent", text=reply_text, ts=time.time())

    return {
        "turns": [agent_turn],
        "disposition": state["disposition"],
        "flags": state["flags"],
    }