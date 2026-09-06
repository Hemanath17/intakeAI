from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from rules_engine.tables.sol_table import get_government_defendant_rule, get_limitation_years
from slots.schema import IncidentType, InjurySeverity

DEADLINE_URGENT_DAYS = 90
FIRM_PRACTICE_AREAS = {
    IncidentType.CAR_ACCIDENT, IncidentType.SLIP_AND_FALL, IncidentType.MEDICAL_MALPRACTICE,
    IncidentType.DOG_BITE, IncidentType.PRODUCT_LIABILITY, IncidentType.WORKPLACE_INJURY,
    IncidentType.WRONGFUL_DEATH,
}
FIRM_COVERAGE_STATES: Optional[set[str]] = None
class Disposition:
    PRIORITY_ATTORNEY_REVIEW = "priority_attorney_review"
    DEADLINE_REVIEW_REQUIRED = "deadline_review_required"
    CONFLICT_REVIEW_REQUIRED = "conflict_review_required"
    EXISTING_REPRESENTATION = "existing_representation"
    POSSIBLE_REFERRAL = "possible_referral"
    OUTSIDE_FIRM_CRITERIA = "outside_firm_criteria"
    MISSING_INFORMATION = "missing_information"
    STANDARD_INTAKE_REVIEW = "standard_intake_review"

DISPOSITION_PRIORITY = [
    Disposition.PRIORITY_ATTORNEY_REVIEW,
    Disposition.DEADLINE_REVIEW_REQUIRED,
    Disposition.CONFLICT_REVIEW_REQUIRED,
    Disposition.EXISTING_REPRESENTATION,
    Disposition.POSSIBLE_REFERRAL,
    Disposition.OUTSIDE_FIRM_CRITERIA,
    Disposition.MISSING_INFORMATION,
    Disposition.STANDARD_INTAKE_REVIEW,
]

class Flag(BaseModel):
    rule: str
    detail: str
    severity: str
    requires_attorney: bool
    disposition_hint: Optional[str] = None

class RuleResult(BaseModel):
    flags: list[Flag]
    disposition: str

def _parse_date(value) -> Optional[date]:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

def _days_elapsed(start: date, today: date) -> int:
    return (today - start).days

def _rule_severity(record: dict) -> list[Flag]:
    flags = []
    severity = record.get("injury_severity")
    if severity in (InjurySeverity.SEVERE, InjurySeverity.CATASTROPHIC, InjurySeverity.FATAL):
        flags.append(Flag(
            rule="catastrophic_severity",
            detail=f"Reported severity is {severity}; immediate attorney attention warranted",
            severity="high", requires_attorney=True,
            disposition_hint=Disposition.PRIORITY_ATTORNEY_REVIEW,
        ))
    if record.get("currently_hospitalised") is True:
        flags.append(Flag(
            rule="claimant_hospitalised",
            detail="Claimant reported as currently hospitalised",
            severity="high", requires_attorney=True,
            disposition_hint=Disposition.PRIORITY_ATTORNEY_REVIEW,
        ))
    if severity == InjurySeverity.FATAL and record.get("incident_type") != IncidentType.WRONGFUL_DEATH:
        flags.append(Flag(
            rule="possible_wrongful_death",
            detail="Fatal outcome reported but matter not classified as wrongful death; "
                   "reclassification and date-of-death capture needed",
            severity="high", requires_attorney=True,
            disposition_hint=Disposition.PRIORITY_ATTORNEY_REVIEW,
        ))
    return flags

def _rule_limitations(record: dict, today: date) -> list[Flag]:
    state = record.get("incident_state")
    incident_type = record.get("incident_type")
    raw_date = record.get("incident_date")
    if not state or not incident_type or not raw_date:
        return []
    incident_date = _parse_date(raw_date)
    if incident_date is None:
        return [Flag(rule="limitations_window", detail="Incident date could not be parsed; verify with caller",
                     severity="medium", requires_attorney=True,
                     disposition_hint=Disposition.MISSING_INFORMATION)]
    if incident_date > today:
        return [Flag(rule="limitations_window", detail="Incident date is in the future; likely capture error",
                     severity="medium", requires_attorney=False,
                     disposition_hint=Disposition.MISSING_INFORMATION)]
    years = get_limitation_years(state, incident_type)
    if years is None:
        return [Flag(rule="limitations_window", detail=f"No limitations reference for state {state}; manual review",
                     severity="medium", requires_attorney=True,
                     disposition_hint=Disposition.DEADLINE_REVIEW_REQUIRED)]
    window_days = int(years * 365.25)
    anchor_note = ""
    if incident_type == IncidentType.WRONGFUL_DEATH:
        anchor_note = " (clock runs from date of death, which may differ from incident date)"
    elif incident_type == IncidentType.MEDICAL_MALPRACTICE:
        anchor_note = " (discovery rule may shift the start date)"
    gov_rule = None
    if record.get("defendant_type") in ("transit_authority", "government_entity"):
        gov_rule = get_government_defendant_rule(state)
        if gov_rule and gov_rule["entity_years"]:
            window_days = min(window_days, int(gov_rule["entity_years"] * 365.25))
    elapsed = _days_elapsed(incident_date, today)
    remaining = window_days - elapsed
    flags = []
    if remaining < 0:
        flags.append(Flag(
            rule="limitations_window",
            detail=f"Standard window of {years} years in {state} may have closed{anchor_note}; "
                   "tolling or discovery exceptions may apply — attorney must verify",
            severity="high", requires_attorney=True,
            disposition_hint=Disposition.DEADLINE_REVIEW_REQUIRED,
        ))
    elif remaining <= DEADLINE_URGENT_DAYS:
        flags.append(Flag(
            rule="limitations_window",
            detail=f"Approximately {remaining} days remain in the {state} filing window{anchor_note}; urgent",
            severity="high", requires_attorney=True,
            disposition_hint=Disposition.DEADLINE_REVIEW_REQUIRED,
        ))
    if gov_rule and gov_rule["notice_days"]:
        notice_remaining = gov_rule["notice_days"] - elapsed
        if notice_remaining < 0:
            detail = (f"Pre-suit government claim window ({gov_rule['notice_days']} days) in {state} "
                      "may have passed; attorney must verify exceptions")
        else:
            detail = (f"Government defendant: pre-suit claim must be presented within "
                      f"{gov_rule['notice_days']} days in {state}; about {notice_remaining} days remain")
        flags.append(Flag(rule="government_notice", detail=detail, severity="high",
                          requires_attorney=True, disposition_hint=Disposition.DEADLINE_REVIEW_REQUIRED))
    if record.get("claimant_is_minor") is True:
        flags.append(Flag(
            rule="minor_tolling",
            detail="Claimant is a minor; limitations period is likely tolled — deadline math above is not reliable",
            severity="medium", requires_attorney=True,
            disposition_hint=Disposition.DEADLINE_REVIEW_REQUIRED,
        ))
    return flags

def _rule_screening(record: dict) -> list[Flag]:
    flags = []
    incident_type = record.get("incident_type")
    if incident_type == IncidentType.OTHER:
        flags.append(Flag(
            rule="unclassified_matter",
            detail="Matter type could not be classified; human review needed before any routing decision",
            severity="medium", requires_attorney=False,
            disposition_hint=Disposition.STANDARD_INTAKE_REVIEW,
        ))
    elif incident_type and incident_type not in FIRM_PRACTICE_AREAS:
        flags.append(Flag(
            rule="practice_area_match", detail=f"{incident_type} is outside the firm's practice areas",
            severity="medium", requires_attorney=False,
            disposition_hint=Disposition.OUTSIDE_FIRM_CRITERIA,
        ))
    if incident_type == IncidentType.WORKPLACE_INJURY:
        flags.append(Flag(
            rule="workers_comp_overlap",
            detail="Workplace injury may route through workers' compensation with separate deadlines; "
                   "attorney must determine the correct track",
            severity="medium", requires_attorney=True,
            disposition_hint=Disposition.STANDARD_INTAKE_REVIEW,
        ))
    state = record.get("incident_state")
    if state and FIRM_COVERAGE_STATES is not None and state not in FIRM_COVERAGE_STATES:
        flags.append(Flag(
            rule="jurisdiction_coverage", detail=f"Incident state {state} is outside firm coverage",
            severity="medium", requires_attorney=False,
            disposition_hint=Disposition.POSSIBLE_REFERRAL,
        ))
    if record.get("existing_representation") is True:
        flags.append(Flag(
            rule="existing_representation",
            detail="Caller reports existing counsel on this matter; confirm whether seeking substitute counsel",
            severity="medium", requires_attorney=False,
            disposition_hint=Disposition.EXISTING_REPRESENTATION,
        ))
    if record.get("conflict_parties"):
        flags.append(Flag(
            rule="conflict_review", detail="Adverse party names captured; run conflict search before engagement",
            severity="info", requires_attorney=True,
            disposition_hint=Disposition.CONFLICT_REVIEW_REQUIRED,
        ))
    if record.get("injury_occurred") is False and record.get("medical_treatment") is False:
        flags.append(Flag(
            rule="no_injury_no_treatment",
            detail="No injury or treatment reported; damages basis unclear — human review, not auto-decline",
            severity="medium", requires_attorney=True,
            disposition_hint=Disposition.STANDARD_INTAKE_REVIEW,
        ))
    return flags
def _rule_completeness(unresolved_slots: Optional[list[str]]) -> list[Flag]:
    if not unresolved_slots:
        return []
    return [Flag(
        rule="record_completeness",
        detail=f"Required fields unresolved: {', '.join(unresolved_slots)}",
        severity="medium", requires_attorney=False,
        disposition_hint=Disposition.MISSING_INFORMATION,
    )]

def evaluate(record: dict, unresolved_slots: Optional[list[str]] = None,
             today: Optional[date] = None) -> RuleResult:
    today = today or date.today()
    flags = []
    flags.extend(_rule_severity(record))
    flags.extend(_rule_limitations(record, today))
    flags.extend(_rule_screening(record))
    flags.extend(_rule_completeness(unresolved_slots))
    hints = {f.disposition_hint for f in flags if f.disposition_hint}
    disposition = next((d for d in DISPOSITION_PRIORITY if d in hints),
                       Disposition.STANDARD_INTAKE_REVIEW)
    return RuleResult(flags=flags, disposition=disposition)