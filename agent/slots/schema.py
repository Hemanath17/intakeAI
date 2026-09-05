from __future__ import annotations
from enum import Enum
from typing import Callable, Optional
from pydantic import BaseModel

class SlotGroup(str, Enum):
    CONTACT = "contact"
    PARTY = "party"
    MATTER = "matter"
    INJURY = "injury"
    EVIDENCE = "evidence"
    LIABILITY = "liability"
    SCREENING = "screening"
    OPS = "ops"

class IncidentType(str, Enum):
    CAR_ACCIDENT = "car_accident"
    SLIP_AND_FALL = "slip_and_fall"
    MEDICAL_MALPRACTICE = "medical_malpractice"
    DOG_BITE = "dog_bite"
    PRODUCT_LIABILITY = "product_liability"
    WORKPLACE_INJURY = "workplace_injury"
    WRONGFUL_DEATH = "wrongful_death"
    OTHER = "other"

class InjurySeverity(str, Enum):
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"
    FATAL = "fatal"

class DefendantType(str, Enum):
    PRIVATE_INDIVIDUAL = "private_individual"
    COMMERCIAL_VEHICLE = "commercial_vehicle"
    TRANSIT_AUTHORITY = "transit_authority"
    GOVERNMENT_ENTITY = "government_entity"
    PROPERTY_OWNER = "property_owner"
    EMPLOYER = "employer"
    MEDICAL_PROVIDER = "medical_provider"
    MANUFACTURER = "manufacturer"
    UNKNOWN = "unknown"

class SlotDefinition(BaseModel):
    name: str
    group: SlotGroup
    required: bool
    conditional_on: Optional[Callable[[dict], bool]] = None

    class Config:
        arbitrary_types_allowed = True

SLOT_REGISTRY: list[SlotDefinition] = [
    SlotDefinition(name="caller_name", group=SlotGroup.CONTACT, required=True),
    SlotDefinition(name="caller_phone", group=SlotGroup.CONTACT, required=True),
    SlotDefinition(name="caller_email", group=SlotGroup.CONTACT, required=False),

    SlotDefinition(name="caller_is_claimant", group=SlotGroup.PARTY, required=True),
    SlotDefinition(
        name="claimant_name", group=SlotGroup.PARTY, required=False,
        conditional_on=lambda s: s.get("caller_is_claimant") is False,
    ),
    SlotDefinition(
        name="claimant_condition", group=SlotGroup.PARTY, required=False,
        conditional_on=lambda s: s.get("caller_is_claimant") is False,
    ),
    SlotDefinition(
        name="authority_basis", group=SlotGroup.PARTY, required=False,
        conditional_on=lambda s: s.get("caller_is_claimant") is False,
    ),

    SlotDefinition(name="incident_type", group=SlotGroup.MATTER, required=True),
    SlotDefinition(name="incident_date", group=SlotGroup.MATTER, required=True),
    SlotDefinition(name="incident_city", group=SlotGroup.MATTER, required=False),
    SlotDefinition(name="incident_state", group=SlotGroup.MATTER, required=True),
    SlotDefinition(name="narrative", group=SlotGroup.MATTER, required=True),

    SlotDefinition(name="injury_occurred", group=SlotGroup.INJURY, required=True),
    SlotDefinition(
        name="injury_description", group=SlotGroup.INJURY, required=False,
        conditional_on=lambda s: s.get("injury_occurred") is True,
    ),
    SlotDefinition(name="injury_severity", group=SlotGroup.INJURY, required=True),
    SlotDefinition(name="medical_treatment", group=SlotGroup.INJURY, required=True),
    SlotDefinition(
        name="treatment_ongoing", group=SlotGroup.INJURY, required=False,
        conditional_on=lambda s: s.get("medical_treatment") is True,
    ),
    SlotDefinition(
        name="currently_hospitalised", group=SlotGroup.INJURY, required=False,
        conditional_on=lambda s: s.get("injury_severity") in ("severe", "catastrophic", "fatal"),
    ),

    SlotDefinition(name="police_report", group=SlotGroup.EVIDENCE, required=False),

    SlotDefinition(name="other_party_identified", group=SlotGroup.LIABILITY, required=True),
    SlotDefinition(
        name="defendant_type", group=SlotGroup.LIABILITY, required=False,
        conditional_on=lambda s: s.get("other_party_identified") is True,
    ),
    SlotDefinition(name="fault_narrative", group=SlotGroup.LIABILITY, required=False),

    SlotDefinition(name="existing_representation", group=SlotGroup.SCREENING, required=True),
    SlotDefinition(name="conflict_parties", group=SlotGroup.SCREENING, required=True),

    SlotDefinition(name="preferred_language", group=SlotGroup.OPS, required=False),
    SlotDefinition(name="best_callback_time", group=SlotGroup.OPS, required=False),
]