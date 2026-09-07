from graph.state import IntakeState
from slots.ledger import record_answer

STATE_NAMES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH",
    "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC",
}

CITY_TO_STATE = {
    "phoenix": "AZ", "tucson": "AZ", "chicago": "IL", "springfield il": "IL",
    "houston": "TX", "dallas": "TX", "austin": "TX", "san antonio": "TX",
    "miami": "FL", "orlando": "FL", "tallahassee": "FL", "jacksonville": "FL",
    "seattle": "WA", "olympia": "WA", "denver": "CO", "atlanta": "GA",
    "boston": "MA", "new york city": "NY", "albany": "NY", "buffalo": "NY",
    "los angeles": "CA", "san francisco": "CA", "sacramento": "CA", "san diego": "CA",
    "las vegas": "NV", "carson city": "NV", "portland": "OR", "salem": "OR",
    "nashville": "TN", "memphis": "TN", "detroit": "MI", "lansing": "MI",
    "minneapolis": "MN", "st paul": "MN", "cleveland": "OH", "columbus ohio": "OH",
    "philadelphia": "PA", "harrisburg": "PA", "pittsburgh": "PA",
    "raleigh": "NC", "charlotte": "NC", "indianapolis": "IN",
    "baton rouge": "LA", "new orleans": "LA", "little rock": "AR",
    "oklahoma city": "OK", "tulsa": "OK", "salt lake city": "UT",
    "richmond": "VA", "virginia beach": "VA", "trenton": "NJ", "newark": "NJ",
    "hartford": "CT", "providence": "RI", "boise": "ID", "helena": "MT",
    "cheyenne": "WY", "bismarck": "ND", "pierre": "SD", "topeka": "KS",
    "jefferson city": "MO", "st louis": "MO", "kansas city missouri": "MO",
    "des moines": "IA", "madison": "WI", "milwaukee": "WI",
    "annapolis": "MD", "baltimore": "MD", "dover": "DE", "montgomery": "AL",
    "birmingham": "AL", "jackson mississippi": "MS", "columbia sc": "SC",
    "honolulu": "HI", "juneau": "AK", "anchorage": "AK",
    "concord": "NH", "montpelier": "VT", "augusta maine": "ME",
    "washington dc": "DC",
}

AMBIGUOUS_CITIES = {
    "springfield": ["IL", "MO", "MA", "OH"],
    "columbus": ["OH", "GA"],
    "franklin": ["TN", "MA", "OH"],
    "arlington": ["VA", "TX"],
}

def jurisdiction_resolve(state: IntakeState) -> dict:
    jurisdiction = state["jurisdiction"]

    if jurisdiction["confirmed"]:
        return {}

    raw = jurisdiction["raw_mention"]
    if not raw:
        return {}

    normalized = raw.strip().lower()

    if normalized in STATE_NAMES:
        return {"jurisdiction": {
            "raw_mention": raw, "state_code": STATE_NAMES[normalized],
            "confirmed": True, "needs_confirmation": False,
        }}

    if normalized in AMBIGUOUS_CITIES:
        return {"jurisdiction": {
            "raw_mention": None, "state_code": None,
            "confirmed": False, "needs_confirmation": False,
        }}

    if normalized in CITY_TO_STATE:
        resolved = CITY_TO_STATE[normalized]
        ledger = state["ledger"]
        if ledger["incident_state"].value is None:
            record_answer(ledger, "incident_state", resolved, 0.9)
        return {
            "jurisdiction": {
                "raw_mention": raw, "state_code": resolved,
                "confirmed": False, "needs_confirmation": True,
            },
            "ledger": ledger,
        }

    return {"jurisdiction": {
        "raw_mention": None, "state_code": None,
        "confirmed": False, "needs_confirmation": False,
    }}