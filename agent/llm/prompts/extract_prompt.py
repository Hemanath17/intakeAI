EXTRACT_SYSTEM_PROMPT = """You extract structured facts from a legal intake phone call.
Return JSON only. No prose.
Rules:
- Extract ONLY from the caller's most recent message. Earlier turns are context for understanding pronouns and references, never a source of new facts.
- Do NOT infer. If the caller did not state something, omit the field entirely.
- Mark each field "stated" if the caller said it directly, or "inferred" if you reasoned it out.
- Two exceptions where reasoning IS required: injury_severity and defendant_type. Classify these from what the caller described.
- If the caller corrects an earlier answer, extract the corrected value and set "correction": true.
- Omit any field you are unsure about. Omission is always safe. Guessing is not.
- The caller often volunteers information beyond what was asked. Extract ALL facts present in their message, not only the answer to the pending question."""
FIELD_REFERENCE = """Fields you may extract:

caller_name, caller_phone, caller_email: the caller's own contact details
caller_state: two-letter code for the state the caller is physically calling FROM
caller_is_claimant: true if the caller is the injured person, false if calling for someone else
claimant_name: the injured person's name, when it is not the caller
claimant_condition: the injured person's CURRENT status only (in hospital, recovering, at home). Do not put injury descriptions here.
claimant_dob: injured person's date of birth, YYYY-MM-DD
authority_basis: caller's relationship to the injured person

incident_type: one of car_accident, slip_and_fall, medical_malpractice, dog_bite, product_liability, workplace_injury, wrongful_death, other
incident_date: YYYY-MM-DD. For partial dates use the first of the month.
incident_date_raw: the caller's exact wording for when it happened
incident_city: city name only, never a state
narrative: what happened, in the caller's own words

injury_occurred: true or false
injury_description: description of the injuries
injury_severity: one of none, minor, moderate, severe, catastrophic, fatal
medical_treatment: true or false
treatment_ongoing: true or false
currently_hospitalised: true or false

police_report: true or false
other_party_identified: true or false
defendant_type: a LIST of every party type involved. Choose from private_individual, commercial_vehicle, transit_authority, government_entity, property_owner, employer, medical_provider, manufacturer, unknown. A crash involving both another driver and a train is ["private_individual", "transit_authority"].
fault_narrative: who the caller believes was at fault

existing_representation: true if they already have a lawyer for this matter
conflict_parties: list of names of other people involved
marketing_source: how they heard about the firm
insurance_contacted: true if an insurance adjuster has contacted them
gave_recorded_statement: true if they gave a recorded statement to an insurer

Separately, if the caller mentions any place name for where the incident happened, put the raw place name in "jurisdiction_mention"."""

OUTPUT_FORMAT = """Return JSON in exactly this shape:

{
  "fields": {
    "incident_type": {"value": "car_accident", "source": "stated"},
    "injury_severity": {"value": "catastrophic", "source": "inferred"}
  },
  "jurisdiction_mention": "Phoenix",
  "severity_evidence": ["leg was amputated"],
  "corrections": ["incident_date"]
}

Include only fields actually present in the latest message. An empty "fields" object is a valid and correct answer."""

def build_extract_prompt(latest_text: str, history: str, today: str) -> str:
    return (
        f"{FIELD_REFERENCE}\n\n{OUTPUT_FORMAT}\n\n"
        f"Today's date is {today}.\n\n"
        f"Conversation so far (context only):\n{history}\n\n"
        f"Caller's most recent message (extract from THIS only):\n\"{latest_text}\""
    )