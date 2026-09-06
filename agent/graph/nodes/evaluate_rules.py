from graph.state import IntakeState, get_unresolved_required, ledger_to_record
from rules_engine.engine import evaluate


def evaluate_rules(state: IntakeState) -> dict:
    ledger = state["ledger"]
    record = ledger_to_record(ledger)
    unresolved = get_unresolved_required(ledger)

    result = evaluate(record, unresolved_slots=unresolved)

    return {
        "flags": [flag.model_dump() for flag in result.flags],
        "disposition": result.disposition,
    }
