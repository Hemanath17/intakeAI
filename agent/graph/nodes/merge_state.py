from graph.state import IntakeState, ledger_to_record
from slots.ledger import SlotState, record_answer, sync_relevance
def merge_state(state: IntakeState) -> dict:
    ledger = state["ledger"]
    for item in state["pending_extraction"]:
        if ledger.get(item.slot_name) is None:
            continue
        record_answer(ledger, item.slot_name, item.value, item.confidence)
    current_values = ledger_to_record(ledger)
    sync_relevance(ledger, current_values)
    return {
        "ledger": ledger,
        "pending_extraction": [],
    }