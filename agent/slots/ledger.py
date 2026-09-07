from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from slots.schema import SLOT_REGISTRY, SlotGroup

CONFIDENCE_THRESHOLD = 0.7
MAX_ASK_ATTEMPTS = 3
MAX_LOW_CONFIDENCE_REASKS = 1

SEVERITY_RANK = {
    "none": 0, "minor": 1, "moderate": 2,
    "severe": 3, "catastrophic": 4, "fatal": 5,
}

GROUP_ORDER = [
    SlotGroup.MATTER,
    SlotGroup.PARTY,
    SlotGroup.INJURY,
    SlotGroup.CONTACT,
    SlotGroup.LIABILITY,
    SlotGroup.EVIDENCE,
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
    targets = []
    for name, state in ledger.items():
        if state.status == SlotStatus.ASKED:
            targets.append(name)
        elif state.status == SlotStatus.LOW_CONFIDENCE and state.asked_count < MAX_LOW_CONFIDENCE_REASKS:
            targets.append(name)
    return targets


def get_next_unasked(ledger: dict[str, SlotState]) -> Optional[str]:
    for group in GROUP_ORDER:
        for slot in SLOT_REGISTRY:
            if slot.group != group:
                continue
            if ledger[slot.name].status == SlotStatus.UNASKED:
                return slot.name
    return None


def mark_asked(ledger: dict[str, SlotState], slot_name: str, turn: int) -> None:
    state = ledger[slot_name]
    if state.status in (SlotStatus.ANSWERED, SlotStatus.NOT_APPLICABLE, SlotStatus.REFUSED):
        return
    state.asked_count += 1
    state.last_asked_turn = turn
    if state.asked_count >= MAX_ASK_ATTEMPTS and state.value is None:
        state.status = SlotStatus.REFUSED
    elif state.value is not None:
        state.status = SlotStatus.ANSWERED
    else:
        state.status = SlotStatus.ASKED


def _severity_key(value) -> str:
    if value is None:
        return ""
    return getattr(value, "value", str(value))


def _severity_regression(slot_name: str, existing, incoming) -> bool:
    if slot_name != "injury_severity" or existing is None:
        return False
    return SEVERITY_RANK.get(_severity_key(incoming), 0) < SEVERITY_RANK.get(_severity_key(existing), 0)


def record_answer(ledger: dict[str, SlotState], slot_name: str, value: object, confidence: float) -> None:
    state = ledger[slot_name]

    if _severity_regression(slot_name, state.value, value):
        return

    state.value = value
    state.confidence = confidence

    if confidence >= CONFIDENCE_THRESHOLD:
        state.status = SlotStatus.ANSWERED
    elif state.asked_count >= MAX_LOW_CONFIDENCE_REASKS:
        state.status = SlotStatus.ANSWERED
    else:
        state.status = SlotStatus.LOW_CONFIDENCE


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