from graph.state import IntakeState


def ingest_turn(state: IntakeState) -> dict:
    return {"turn_count": state["turn_count"] + 1}
