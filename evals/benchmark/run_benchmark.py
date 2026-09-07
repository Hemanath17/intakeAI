import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent"))
from graph.graph_builder import build_graph
from graph.state import Turn, init_state
from slots.ledger import SlotStatus

CALLER_TURNS = [
    "I want to look into reporting possibly a claim and see whether there's any case involvement.",
    "Yeah, my mom was in an accident. She's been injured.",
    "Auto accident.",
    "Yes, she had her right leg amputated.",
    "It basically got rear-ended and her car went into the train and the train hit her.",
    "No, that's everything about the incident.",
    "It happened in Chicago.",
    "No, we're not working with any other law firms.",
    "My name is Kiki Peterson.",
    "Yes, 847-414-6725 is the best number.",
    "kikipeterson@gmail.com",
    "No, thank you.",
]

def send(graph, state, text):
    new_turn = Turn(role="caller", text=text, ts=time.time())
    return graph.invoke({**state, "turns": [new_turn]})

def show_ledger_delta(before, after):
    changed = []
    for name, slot in after.items():
        prev = before.get(name)
        if prev is None:
            continue
        if slot.value != prev.value or slot.status != prev.status:
            changed.append(f"    {name} = {slot.value!r} [{slot.status.value}]")
    return changed

def snapshot(ledger):
    return {name: slot.model_copy() for name, slot in ledger.items()}

def main():
    graph = build_graph()
    state = init_state(session_id="benchmark-kiki")

    for i, text in enumerate(CALLER_TURNS, start=1):
        if i > 1:
            time.sleep(4)
        before = snapshot(state["ledger"])
        start = time.time()
        state = send(graph, state, text)
        elapsed = time.time() - start

        print(f"\n--- turn {i} ({elapsed:.2f}s) ---")
        print(f"  caller: {text}")
        print(f"  agent:  {state['reply']}")

        deltas = show_ledger_delta(before, state["ledger"])
        if deltas:
            print("  extracted:")
            for d in deltas:
                print(d)

        if state.get("guardrail_violations"):
            print(f"  GUARDRAIL FIRED: {state['guardrail_violations']}")

    print("\n" + "=" * 60)
    print("BENCHMARK SCORECARD")
    print("=" * 60)

    ledger = state["ledger"]

    def slot(name):
        s = ledger.get(name)
        return (s.value, s.status.value) if s else (None, "missing")

    checks = [
        ("F1  incident_date not silently dropped",
         ledger["incident_date"].status != SlotStatus.UNASKED,
         f"status={ledger['incident_date'].status.value}, value={ledger['incident_date'].value}"),
        ("F3  caller identified as third party",
         ledger["caller_is_claimant"].value is False,
         f"caller_is_claimant={slot('caller_is_claimant')}"),
        ("F3b claimant name asked (theirs never did)",
         ledger["claimant_name"].status.value != "unasked",
         f"claimant_name={slot('claimant_name')}"),
        ("F4  jurisdiction resolved to IL",
         state["jurisdiction"]["state_code"] == "IL",
         f"jurisdiction={state['jurisdiction']}"),
        ("F5  transit defendant detected",
         ledger["defendant_type"].value is not None
         and "transit" in str(ledger["defendant_type"].value),
         f"defendant_type={slot('defendant_type')}"),
        ("F10 catastrophic severity detected",
         str(ledger["injury_severity"].value) in ("catastrophic", "InjurySeverity.CATASTROPHIC"),
         f"injury_severity={slot('injury_severity')}"),
        ("F10b priority disposition assigned",
         state["disposition"] == "priority_attorney_review",
         f"disposition={state['disposition']}"),
    ]

    for label, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
        print(f"      {detail}")

    print(f"\nflags raised: {len(state['flags'])}")
    for f in state["flags"]:
        print(f"  - {f['rule']}: {f['detail'][:80]}")

    unresolved = [n for n, s in ledger.items()
                  if s.status in (SlotStatus.UNASKED, SlotStatus.ASKED, SlotStatus.LOW_CONFIDENCE)]
    print(f"\nstill unresolved: {unresolved}")

if __name__ == "__main__":
    main()