import sys
from datetime import date
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent"))

from rules_engine.engine import Disposition, evaluate
from slots.schema import IncidentType, InjurySeverity
TODAY = date(2026, 9, 5)

BASE_RECORD = {
    "incident_type": IncidentType.CAR_ACCIDENT,
    "incident_date": date(2026, 6, 1),
    "incident_state": "AZ",
    "injury_severity": InjurySeverity.MINOR,
    "injury_occurred": True,
    "medical_treatment": True,
    "existing_representation": False,
    "conflict_parties": [],
    "defendant_type": None,
    "currently_hospitalised": False,
    "claimant_is_minor": False,
}


def record(**overrides):
    merged = dict(BASE_RECORD)
    merged.update(overrides)
    return merged


def flag_names(result):
    return {f.rule for f in result.flags}


@pytest.mark.parametrize("overrides,expected_present,expected_absent", [
    ({}, set(), {"catastrophic_severity", "limitations_window", "unclassified_matter"}),
    ({"injury_severity": InjurySeverity.SEVERE}, {"catastrophic_severity"}, set()),
    ({"injury_severity": InjurySeverity.CATASTROPHIC}, {"catastrophic_severity"}, set()),
    ({"currently_hospitalised": True}, {"claimant_hospitalised"}, set()),
    (
        {"injury_severity": InjurySeverity.FATAL, "incident_type": IncidentType.CAR_ACCIDENT},
        {"possible_wrongful_death"},
        set(),
    ),
    (
        {"injury_severity": InjurySeverity.FATAL, "incident_type": IncidentType.WRONGFUL_DEATH},
        set(),
        {"possible_wrongful_death"},
    ),
    ({"incident_type": IncidentType.OTHER}, {"unclassified_matter"}, {"outside_firm_criteria"}),
    ({"incident_type": IncidentType.WORKPLACE_INJURY}, {"workers_comp_overlap"}, set()),
    ({"existing_representation": True}, {"existing_representation"}, set()),
    ({"conflict_parties": ["John Smith"]}, {"conflict_review"}, set()),
    (
        {"injury_occurred": False, "medical_treatment": False},
        {"no_injury_no_treatment"},
        set(),
    ),
    (
        {"injury_occurred": None, "medical_treatment": None},
        set(),
        {"no_injury_no_treatment"},
    ),
    ({"incident_date": "not a real date"}, {"limitations_window"}, set()),
    ({"incident_date": date(2027, 1, 1)}, {"limitations_window"}, set()),
    ({"incident_state": "ZZ"}, {"limitations_window"}, set()),
])
def test_flag_presence(overrides, expected_present, expected_absent):
    result = evaluate(record(**overrides), today=TODAY)
    names = flag_names(result)
    assert expected_present.issubset(names)
    assert expected_absent.isdisjoint(names)

def test_clean_case_disposition_standard():
    result = evaluate(record(), today=TODAY)
    assert result.disposition == Disposition.STANDARD_INTAKE_REVIEW
    assert result.flags == []

def test_deadline_open_no_flag():
    result = evaluate(record(incident_date=date(2026, 7, 1)), today=TODAY)
    assert "limitations_window" not in flag_names(result)


def test_deadline_urgent_window():
    result = evaluate(record(incident_date=date(2024, 9, 20), incident_state="AZ"), today=TODAY)
    detail = next(f.detail for f in result.flags if f.rule == "limitations_window")
    assert "remain" in detail
    assert "may have closed" not in detail

def test_deadline_may_have_closed():
    result = evaluate(record(incident_date=date(2020, 1, 1), incident_state="AZ"), today=TODAY)
    detail = next(f.detail for f in result.flags if f.rule == "limitations_window")
    assert "may have closed" in detail
    assert result.disposition == Disposition.DEADLINE_REVIEW_REQUIRED

def test_minor_tolling_overrides_confidence():
    result = evaluate(
        record(incident_date=date(2020, 1, 1), incident_state="AZ", claimant_is_minor=True),
        today=TODAY,
    )
    names = flag_names(result)
    assert "limitations_window" in names
    assert "minor_tolling" in names

def test_government_defendant_shortens_window():
    shortened = evaluate(
        record(incident_date=date(2025, 6, 1), incident_state="IL", defendant_type="transit_authority"),
        today=TODAY,
    )
    unshortened = evaluate(
        record(incident_date=date(2025, 6, 1), incident_state="IL", defendant_type=None),
        today=TODAY,
    )
    assert "limitations_window" in flag_names(shortened)
    assert "limitations_window" not in flag_names(unshortened)

def test_government_notice_gate_california():
    result = evaluate(
        record(incident_date=date(2026, 1, 1), incident_state="CA", defendant_type="government_entity"),
        today=TODAY,
    )
    names = flag_names(result)
    assert "government_notice" in names
    assert "limitations_window" not in names

def test_benchmark_transcript_case():
    kiki_record = record(
        incident_type=IncidentType.CAR_ACCIDENT,
        incident_state="IL",
        incident_date=None,
        injury_severity=InjurySeverity.CATASTROPHIC,
        defendant_type="transit_authority",
    )
    result = evaluate(kiki_record, unresolved_slots=["incident_date"], today=TODAY)
    names = flag_names(result)
    assert "catastrophic_severity" in names
    assert "limitations_window" not in names
    assert "record_completeness" in names
    assert result.disposition == Disposition.PRIORITY_ATTORNEY_REVIEW

def test_record_completeness_names_unresolved_slots():
    result = evaluate(record(), unresolved_slots=["caller_phone", "incident_city"], today=TODAY)
    detail = next(f.detail for f in result.flags if f.rule == "record_completeness")
    assert "caller_phone" in detail
    assert "incident_city" in detail

def test_multiple_flags_priority_order():
    combined = record(
        injury_severity=InjurySeverity.CATASTROPHIC,
        incident_date=date(2020, 1, 1),
        incident_state="AZ",
        conflict_parties=["Jane Doe"],
    )
    result = evaluate(combined, today=TODAY)
    names = flag_names(result)
    assert {"catastrophic_severity", "limitations_window", "conflict_review"}.issubset(names)
    assert result.disposition == Disposition.PRIORITY_ATTORNEY_REVIEW

def test_determinism():
    fixed_record = record(incident_date=date(2024, 3, 1), incident_state="IL")
    first = evaluate(fixed_record, today=TODAY)
    second = evaluate(fixed_record, today=TODAY)
    assert first == second
