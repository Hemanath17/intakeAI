from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from slots.schema import SLOT_REGISTRY, SlotGroup

CONFIDENCE_THRESHOLD = 0.7
MAX_ASK_ATTEMPTS = 3

GROUP_ORDER = [
    SlotGroup.MATTER,
    SlotGroup.CONTACT,
    SlotGroup.INJURY,
    SlotGroup.LIABILITY,
    SlotGroup.EVIDENCE,
    SlotGroup.PARTY,
    SlotGroup.SCREENING,
    SlotGroup.OPS,
]

class SlotStatus(str, Enum):
    UNASKED = "unasked"
    ASKED = "asked"
    ANSWERED = "answered"
    LOW_CONFIDENCE = "low_confidence"
    REFUSED = "refused"
    NOT_APPLICABLE = "not_applicable"

class SlotState(BaseModel):
    status: SlotStatus = SlotStatus.UNASKED
    value: Optional[object] = None
    confidence: float = 0.0
    asked_count: int = 0
    last_asked_turn: Optional[int] = None

def init_ledger() -> dict[str, SlotState]:
    ledger = {slot.name: SlotState() for slot in SLOT_REGISTRY}
    sync_relevance(ledger, {})
    return ledger

def sync_relevance(ledger: dict[str, SlotState], values: dict) -> None:
    for slot in SLOT_REGISTRY:
        if slot.conditional_on is None:
            continue
        state = ledger[slot.name]
        if state.status not in (SlotStatus.UNASKED, SlotStatus.NOT_APPLICABLE):
            continue
        active = slot.conditional_on(values)
        state.status = SlotStatus.UNASKED if active else SlotStatus.NOT_APPLICABLE

def get_reask_targets(ledger: dict[str, SlotState]) -> list[str]:
    return [
        name for name, state in ledger.items()
        if state.status in (SlotStatus.ASKED, SlotStatus.LOW_CONFIDENCE)
    ]

def get_next_unasked(ledger: dict[str, SlotState]) -> Optional[str]:
    by_name = {slot.name: slot for slot in SLOT_REGISTRY}
    for group in GROUP_ORDER:
        for slot in SLOT_REGISTRY:
            if slot.group != group:
                continue
            if ledger[slot.name].status == SlotStatus.UNASKED:
                return slot.name
    return None

def mark_asked(ledger: dict[str, SlotState], slot_name: str, turn: int) -> None:
    state = ledger[slot_name]
    state.asked_count += 1
    state.last_asked_turn = turn
    if state.asked_count >= MAX_ASK_ATTEMPTS:
        state.status = SlotStatus.REFUSED
    else:
        state.status = SlotStatus.ASKED


def record_answer(
    ledger: dict[str, SlotState],
    slot_name: str,
    value: object,
    confidence: float,
) -> None:
    state = ledger[slot_name]
    state.value = value
    state.confidence = confidence

    if confidence < CONFIDENCE_THRESHOLD:
        if state.asked_count >= MAX_ASK_ATTEMPTS:
            state.status = SlotStatus.REFUSED
        else:
            state.status = SlotStatus.LOW_CONFIDENCE
        return

    state.status = SlotStatus.ANSWERED

def is_complete(ledger: dict[str, SlotState]) -> bool:
    by_name = {slot.name: slot for slot in SLOT_REGISTRY}
    for name, state in ledger.items():
        slot = by_name[name]
        if not slot.required:
            continue
        if state.status in (SlotStatus.ANSWERED, SlotStatus.NOT_APPLICABLE, SlotStatus.REFUSED):
            continue
        return False
    return True