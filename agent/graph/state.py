from __future__ import annotations
import operator
from enum import Enum
from typing import Annotated, Optional, TypedDict
from slots.ledger import SlotState, SlotStatus, init_ledger
from slots.schema import SLOT_REGISTRY

class Phase(str, Enum):
    GREETING = "greeting"
    CONSENT = "consent"
    SCOPE = "scope"
    INTERVIEW = "interview"
    READBACK = "readback"
    CLOSE = "close"
    ESCALATE = "escalate"
    TERMINATED = "terminated"

class Turn(TypedDict):
    role: str
    text: str
    ts: float

class IntakeState(TypedDict):
    session_id: str
    turns: Annotated[list[Turn], operator.add]
    phase: Phase
    disclosure_done: bool
    consent: dict
    jurisdiction: dict
    party: dict
    ledger: dict[str, SlotState]
    narrative: str
    entities: dict
    severity_signal: dict
    empathy: dict
    flags: list[dict]
    disposition: Optional[str]
    pending_slot: Optional[str]
    escalation_summary: Optional[str]
    pending_extraction: list
    next_action: Optional[str]
    reply: Optional[str]
    turn_count: int

def init_state(session_id: str) -> IntakeState:
    return IntakeState(
        session_id=session_id,
        turns=[],
        phase=Phase.GREETING,
        disclosure_done=False,
        consent={"required": None, "status": "unknown"},
        jurisdiction={"raw_mention": None, "state_code": None, "confirmed": False, "needs_confirmation": False},
        party={"caller_is_claimant": None, "relationship": None, "authority_basis": None},
        ledger=init_ledger(),
        narrative="",
        entities={"defendant_types": []},
        severity_signal={"tier": "none", "evidence": [], "new_this_turn": False},
        empathy={"pause_active": False, "pauses_used": 0, "last_event_turn": None},
        flags=[],
        disposition=None,
        pending_slot=None,
        escalation_summary=None,
        pending_extraction=[],
        next_action=None,
        reply=None,
        turn_count=0,
    )

def ledger_to_record(ledger: dict[str, SlotState]) -> dict:
    return {name: slot_state.value for name, slot_state in ledger.items()}

def get_unresolved_required(ledger: dict[str, SlotState]) -> list[str]:
    resolved = (SlotStatus.ANSWERED, SlotStatus.NOT_APPLICABLE, SlotStatus.REFUSED)
    unresolved = []
    for slot in SLOT_REGISTRY:
        if not slot.required:
            continue
        if ledger[slot.name].status not in resolved:
            unresolved.append(slot.name)
    return unresolved

