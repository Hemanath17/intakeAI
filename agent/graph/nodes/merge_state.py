from graph.state import IntakeState, ledger_to_record
from slots.ledger import SlotStatus, record_answer, sync_relevance


def _derive_caller_is_claimant(ledger) -> None:
    pivot = ledger["caller_is_claimant"]
    if pivot.value is not None:
        return
    implies_third_party = (
        ledger["authority_basis"].value is not None
        or ledger["claimant_name"].value is not None
        or ledger["claimant_condition"].value is not None
    )
    if implies_third_party:
        record_answer(ledger, "caller_is_claimant", False, 0.9)


THIRD_PARTY_MARKERS = [
    "my mom", "my mother", "my dad", "my father", "my wife", "my husband",
    "my son", "my daughter", "my spouse", "my brother", "my sister",
    "on her behalf", "on his behalf", "on their behalf", "for my",
]


def _detect_third_party(state, ledger) -> None:
    if ledger["caller_is_claimant"].value is not None:
        return
    for turn in state["turns"]:
        if turn["role"] != "caller":
            continue
        lowered = turn["text"].lower()
        if any(marker in lowered for marker in THIRD_PARTY_MARKERS):
            record_answer(ledger, "caller_is_claimant", False, 0.9)
            return


NARRATIVE_MIN_WORDS = 12


def _assemble_narrative(state, ledger) -> None:
    if ledger["narrative"].value is not None:
        return
    if ledger["incident_type"].value is None:
        return
    caller_turns = [t["text"] for t in state["turns"] if t["role"] == "caller"]
    longest = max(caller_turns, key=lambda t: len(t.split()), default="")
    if len(longest.split()) >= NARRATIVE_MIN_WORDS:
        record_answer(ledger, "narrative", longest, 0.85)


def merge_state(state: IntakeState) -> dict:
    ledger = state["ledger"]

    for item in state["pending_extraction"]:
        if ledger.get(item.slot_name) is None:
            continue
        record_answer(ledger, item.slot_name, item.value, item.confidence)

    _detect_third_party(state, ledger)
    _derive_caller_is_claimant(ledger)
    _assemble_narrative(state, ledger)

    current_values = ledger_to_record(ledger)
    sync_relevance(ledger, current_values)

    return {
        "ledger": ledger,
        "pending_extraction": [],
    }
