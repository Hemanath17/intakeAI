from datetime import date, datetime
from graph.state import IntakeState
from llm.groq_client import generate_json
from llm.prompts.extract_prompt import EXTRACT_SYSTEM_PROMPT, build_extract_prompt
from slots.schema import SLOT_REGISTRY, DefendantType, IncidentType, InjurySeverity

CONFIDENCE_STATED = 0.9
CONFIDENCE_INFERRED = 0.75

CONFIRM_REQUIRED_SLOTS = {"incident_date", "incident_state", "caller_is_claimant"}

VALID_SLOT_NAMES = {slot.name for slot in SLOT_REGISTRY}

ENUM_FIELDS = {
    "incident_type": IncidentType,
    "injury_severity": InjurySeverity,
}

SKIP_EXTRACTION_ACTIONS = {"request_consent"}

class ExtractedValue:
    def __init__(self, slot_name: str, value, confidence: float):
        self.slot_name = slot_name
        self.value = value
        self.confidence = confidence

def _validate_value(slot_name: str, value):
    if value is None:
        return None

    if slot_name == "defendant_type":
        values = value if isinstance(value, list) else [value]
        valid = []
        for v in values:
            try:
                valid.append(DefendantType(v))
            except ValueError:
                continue
        return valid or None

    if slot_name in ENUM_FIELDS:
        enum_class = ENUM_FIELDS[slot_name]
        try:
            return enum_class(value)
        except ValueError:
            return None

    if slot_name in ("incident_date", "claimant_dob"):
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

    return value

def _build_history(state: IntakeState) -> str:
    recent = state["turns"][-5:-1]
    return "\n".join(f'{t["role"]}: {t["text"]}' for t in recent)

def extract(state: IntakeState) -> dict:
    if state.get("next_action") in SKIP_EXTRACTION_ACTIONS:
        return {"pending_extraction": []}

    latest_text = state["turns"][-1]["text"]
    history = _build_history(state)
    today = date.today().isoformat()

    prompt = build_extract_prompt(latest_text, history, today)

    try:
        result = generate_json(prompt, system=EXTRACT_SYSTEM_PROMPT)
    except Exception:
        return {"pending_extraction": []}

    extracted = []
    for slot_name, payload in (result.get("fields") or {}).items():
        if slot_name not in VALID_SLOT_NAMES:
            continue
        if not isinstance(payload, dict):
            continue

        value = _validate_value(slot_name, payload.get("value"))
        if value is None:
            continue

        source = payload.get("source", "inferred")
        if source == "stated":
            confidence = CONFIDENCE_STATED
        elif slot_name in CONFIRM_REQUIRED_SLOTS:
            confidence = 0.5
        else:
            confidence = CONFIDENCE_INFERRED
        extracted.append(ExtractedValue(slot_name, value, confidence))

    update = {"pending_extraction": extracted}

    mention = result.get("jurisdiction_mention")
    if mention and not state["jurisdiction"]["confirmed"]:
        update["jurisdiction"] = {**state["jurisdiction"], "raw_mention": mention}

    evidence = result.get("severity_evidence") or []
    severity_value = next((e.value for e in extracted if e.slot_name == "injury_severity"), None)
    if severity_value:
        update["severity_signal"] = {
            "tier": severity_value,
            "evidence": evidence,
            "new_this_turn": True,
        }

    return update