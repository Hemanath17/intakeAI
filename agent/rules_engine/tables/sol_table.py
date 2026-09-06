from __future__ import annotations
from slots.schema import IncidentType

GENERAL_PI_YEARS: dict[str, int] = {
    "AL": 2, "AK": 2, "AZ": 2, "AR": 3, "CA": 2, "CO": 2, "CT": 2, "DE": 2,
    "FL": 2, "GA": 2, "HI": 2, "ID": 2, "IL": 2, "IN": 2, "IA": 2, "KS": 2,
    "KY": 1, "LA": 2, "ME": 6, "MD": 3, "MA": 3, "MI": 3, "MN": 6, "MS": 3,
    "MO": 5, "MT": 3, "NE": 4, "NV": 2, "NH": 3, "NJ": 2, "NM": 3, "NY": 3,
    "NC": 3, "ND": 6, "OH": 2, "OK": 2, "OR": 2, "PA": 2, "RI": 3, "SC": 3,
    "SD": 3, "TN": 1, "TX": 2, "UT": 4, "VT": 3, "VA": 2, "WA": 3, "WV": 2,
    "WI": 3, "WY": 4, "DC": 3,
}

MED_MAL_OVERRIDE_YEARS: dict[str, float] = {
    "KY": 1, "LA": 1, "TN": 1, "NY": 2.5, "MI": 2, "OH": 1,
}

WRONGFUL_DEATH_OVERRIDE_YEARS: dict[str, float] = {
    "KY": 1, "LA": 1, "TN": 1, "NY": 2, "GA": 2, "OH": 2,
}

GOVERNMENT_DEFENDANT_RULES: dict[str, dict] = {
    "IL": {"entity_years": 1, "notice_days": None},
    "CA": {"entity_years": None, "notice_days": 180},
    "NY": {"entity_years": None, "notice_days": 90},
}

def get_limitation_years(state: str, incident_type: IncidentType) -> float | None:
    state = state.upper()
    if incident_type == IncidentType.MEDICAL_MALPRACTICE and state in MED_MAL_OVERRIDE_YEARS:
        return MED_MAL_OVERRIDE_YEARS[state]
    if incident_type == IncidentType.WRONGFUL_DEATH and state in WRONGFUL_DEATH_OVERRIDE_YEARS:
        return WRONGFUL_DEATH_OVERRIDE_YEARS[state]
    return GENERAL_PI_YEARS.get(state)

def get_government_defendant_rule(state: str) -> dict | None:
    return GOVERNMENT_DEFENDANT_RULES.get(state.upper())