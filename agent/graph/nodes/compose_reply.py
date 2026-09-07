from graph.state import IntakeState
from guardrails.validator import validate
from llm.groq_client import generate_text
from slots.ledger import SlotStatus, mark_asked

SYSTEM_PROMPT = (
    "You are a calm, professional intake assistant for a personal injury law firm. "
    "Acknowledge what the caller just said in one short clause, then ask exactly one "
    "question. Never give legal advice, never predict case value, never promise "
    "representation. Keep your entire response to two sentences or fewer."
)

SLOT_DESCRIPTIONS = {
    "caller_name": "the caller's name",
    "caller_phone": "the best phone number to reach them",
    "caller_email": "their email address",
    "caller_state": "what state they are calling from",
    "caller_is_claimant": "whether they are the injured person, or calling on someone else's behalf",
    "claimant_name": "the injured person's name",
    "claimant_condition": "how the injured person is doing right now",
    "authority_basis": "their relationship to the injured person",
    "incident_type": "what kind of incident happened",
    "incident_date": "when the incident happened",
    "incident_city": "what city it happened in",
    "incident_state": "what state it happened in",
    "narrative": "what happened, in their own words",
    "injury_occurred": "whether anyone was injured",
    "injury_description": "a description of the injury",
    "injury_severity": "how serious the injury is",
    "medical_treatment": "whether they received medical treatment",
    "treatment_ongoing": "whether treatment is still ongoing",
    "currently_hospitalised": "whether the injured person is currently in the hospital",
    "police_report": "whether a police report was filed",
    "other_party_identified": "whether the other party has been identified",
    "defendant_type": "what kind of party was involved",
    "fault_narrative": "who they believe was at fault",
    "existing_representation": "whether they already have a lawyer for this",
    "conflict_parties": "the names of anyone else involved, for a conflict check",
    "marketing_source": "how they heard about the firm",
    "insurance_contacted": "whether an insurance adjuster has contacted them",
    "gave_recorded_statement": "whether they gave a recorded statement to an insurer",
}

FIXED_REPLIES = {
    "request_consent": (
        "Before we continue, I want to let you know this call is being processed and "
        "transcribed in real time by an AI assistant, and no audio is stored. Is that alright with you?"
    ),
    "consent_refused_close": (
        "I understand. Since we're not able to continue without your consent to be recorded, "
        "I'd recommend calling our office directly so a team member can assist you. Thank you for calling."
    ),
}

RELATION_MAP = {
    "child": "mother or father", "daughter": "mother", "son": "mother",
    "mother": "mother", "father": "father", "spouse": "spouse",
    "wife": "wife", "husband": "husband",
}


def _summarize_known_facts(ledger: dict) -> str:
    lines = []
    for name, slot_state in ledger.items():
        if slot_state.status == SlotStatus.ANSWERED and name in SLOT_DESCRIPTIONS:
            lines.append(f"{SLOT_DESCRIPTIONS[name]}: {slot_state.value}")
    return "; ".join(lines) if lines else "no details captured yet"


RELATION_SLOTS = {"claimant_name", "claimant_condition", "claimant_dob"}


def _personalise(need: str, pending_slot: str, ledger: dict) -> str:
    if pending_slot not in RELATION_SLOTS:
        return need
    relation = ledger["authority_basis"].value
    if not relation:
        return need
    relation = str(relation).lower()
    mapping = {
        "child": "mother or father",
        "daughter": "mother",
        "son": "mother",
        "mother": "mother",
        "father": "father",
        "spouse": "spouse",
        "wife": "wife",
        "husband": "husband",
    }
    person = mapping.get(relation, relation)
    if pending_slot == "claimant_name":
        return f"the name of their {person}"
    if pending_slot == "claimant_condition":
        return f"how their {person} is doing right now"
    return f"their {person}'s date of birth"


def _build_prompt(state: IntakeState, next_action: str, pending_slot: str) -> str:
    latest_text = state["turns"][-1]["text"]
    ledger = state["ledger"]

    if next_action == "empathy_pause":
        relation = ledger["authority_basis"].value
        person = RELATION_MAP.get(str(relation).lower(), "loved one") if relation else "loved one"
        tier = state["severity_signal"].get("tier")
        deceased = getattr(tier, "value", str(tier)) == "fatal"
        if deceased:
            return (
                "The caller has just described a death. Express sincere condolences in one sentence. "
                "Do not ask any question this turn. Do not ask how the person is doing."
            )
        return (
            f"The caller has just described a catastrophic injury. Acknowledge it with genuine warmth, "
            f"then ask how their {person} is doing right now. Nothing else."
        )

    if next_action in ("ask_slot", "reask"):
        need = SLOT_DESCRIPTIONS.get(pending_slot, pending_slot)
        need = _personalise(need, pending_slot, ledger)

        attempt = ledger[pending_slot].asked_count if pending_slot in ledger else 0
        if attempt >= 1:
            return (
                f'The caller just said: "{latest_text}". '
                f'You already asked about {need} and did not get it. '
                f'Briefly acknowledge what they just said, then rephrase the question differently '
                f'and more specifically. Do not repeat your previous wording.'
            )
        return f'The caller just said: "{latest_text}". You still need to find out: {need}.'

    if next_action == "confirm_jurisdiction":
        state_code = state["jurisdiction"]["state_code"]
        return f'Confirm with the caller that the state on file is {state_code}, in one short question.'

    if next_action == "readback":
        summary = _summarize_known_facts(state["ledger"])
        return f"Read back this summary to the caller and ask them to confirm it's correct: {summary}."

    if next_action == "close":
        return "Thank the caller warmly and let them know the team will follow up shortly."

    return f'The caller just said: "{latest_text}". Ask a natural follow-up question.'


def compose_reply(state: IntakeState) -> dict:
    next_action = state["next_action"]
    pending_slot = state["pending_slot"]

    if next_action in FIXED_REPLIES:
        return {"reply": FIXED_REPLIES[next_action]}

    prompt = _build_prompt(state, next_action, pending_slot)
    raw_reply = generate_text(prompt, system=SYSTEM_PROMPT)

    result = validate(raw_reply, pending_slot)
    reply_text = raw_reply if result.passed else result.safe_text
    guardrail_violations = result.violations

    ledger = state["ledger"]
    if next_action in ("ask_slot", "reask") and pending_slot:
        mark_asked(ledger, pending_slot, state["turn_count"])

    return {"reply": reply_text, "ledger": ledger, "guardrail_violations": guardrail_violations}
