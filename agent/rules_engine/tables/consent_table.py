from __future__ import annotations
ALL_PARTY_STATES = {
    "CA", "DE", "FL", "IL", "MD", "MA", "MT", "NH", "PA", "WA", "CT",
}
REVIEW_REQUIRED_STATES = {
    "NV": "Statute reads one-party, but state case law has applied a reasonable-expectation-of-privacy test",
    "OR": "All-party for in-person conversations; one-party for phone/electronic under statute, but frequently listed as all-party",
    "VT": "No governing statute; consent requirement is unsettled",
}

def get_consent_requirement(state: str) -> dict:
    state = state.upper()
    if state in ALL_PARTY_STATES:
        return {"requires_all_party_consent": True, "confidence": "high", "note": None}
    if state in REVIEW_REQUIRED_STATES:
        return {
            "requires_all_party_consent": True,
            "confidence": "review_required",
            "note": REVIEW_REQUIRED_STATES[state],
        }
    return {"requires_all_party_consent": False, "confidence": "high", "note": None}