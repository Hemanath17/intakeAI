ADVISORY_PATTERNS = [
    "you should", "you shouldn't", "you ought to", "you need to",
    "i'd recommend", "i would recommend", "i recommend", "my advice",
    "you'd be better off", "you have a strong case", "you have a good case",
    "you have a valid claim", "your case is strong", "you definitely have",
]

VALUE_PATTERNS = [
    "you're entitled to", "you are entitled to", "entitled to compensation",
    "you'll win", "you will win", "you'll get", "you will receive",
    "worth about", "worth around", "settlement of", "payout of",
    r"\$\d",
]

PROMISE_PATTERNS = [
    "we'll take your case", "we will take your case", "we'll represent you",
    "we will represent you", "we can take this case", "we're taking your case",
    "you're now a client", "we've accepted", "we accept your case",
    "guarantee", "guaranteed",
]

MAX_QUESTIONS = 1
MAX_SENTENCES = 3
MAX_CHARACTERS = 400

SAFE_FALLBACKS = {
    "caller_name": "May I have your name, please?",
    "caller_phone": "What's the best phone number to reach you?",
    "caller_email": "What's your email address?",
    "caller_state": "What state are you calling from?",
    "caller_is_claimant": "Are you the person who was injured, or are you calling for someone else?",
    "claimant_name": "What's the injured person's name?",
    "claimant_condition": "How is she doing now?",
    "authority_basis": "What's your relationship to them?",
    "incident_type": "What kind of incident was it?",
    "incident_date": "When did that happen?",
    "incident_city": "What city did it happen in?",
    "incident_state": "What state did it happen in?",
    "narrative": "Could you tell me what happened?",
    "injury_occurred": "Was anyone injured?",
    "injury_description": "Could you describe the injuries?",
    "injury_severity": "How serious were the injuries?",
    "medical_treatment": "Did you receive any medical treatment?",
    "treatment_ongoing": "Is the treatment still ongoing?",
    "currently_hospitalised": "Is she still in the hospital?",
    "police_report": "Was a police report filed?",
    "other_party_identified": "Do you know who the other party was?",
    "defendant_type": "What kind of vehicle or party was involved?",
    "fault_narrative": "Who do you believe was at fault?",
    "existing_representation": "Do you already have a lawyer for this?",
    "conflict_parties": "Could you give me the names of anyone else involved?",
    "marketing_source": "How did you hear about our firm?",
    "insurance_contacted": "Has an insurance adjuster contacted you?",
    "gave_recorded_statement": "Did you give them a recorded statement?",
}

GENERIC_FALLBACK = "Thank you for sharing that. Could you tell me a bit more?"