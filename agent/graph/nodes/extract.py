from graph.state import IntakeState
class ExtractedValue:
    def __init__(self, slot_name: str, value, confidence: float):
        self.slot_name = slot_name
        self.value = value
        self.confidence = confidence

def extract_stub(state: IntakeState, forced_result: list[ExtractedValue] = None) -> list[ExtractedValue]:
    if forced_result is not None:
        return forced_result
    return []

def extract(state: IntakeState) -> dict:
    latest_text = state["turns"][-1]["text"]
    extracted = extract_stub(state)
    return {"pending_extraction": extracted}