import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent"))

from graph.graph_builder import build_graph
from graph.nodes.extract import ExtractedValue
from graph.state import Turn, init_state
from slots.ledger import SlotStatus
from slots.schema import IncidentType

def _send(graph, state, text):
    new_turn = Turn(role="caller", text=text, ts=time.time())
    return graph.invoke({**state, "turns": [new_turn]})


def test_repeated_reask_when_extraction_finds_nothing():
    graph = build_graph()
    state = init_state(session_id="demo-1")

    state = _send(graph, state, "Hi, I want to report a possible claim.")
    assert state["next_action"] == "ask_slot"
    assert state["pending_slot"] == "incident_type"
    assert state["ledger"]["incident_type"].asked_count == 1

    state = _send(graph, state, "My mom was in a car accident and she's hurt.")
    assert state["next_action"] == "reask"
    assert state["pending_slot"] == "incident_type"
    assert state["ledger"]["incident_type"].asked_count == 2

    state = _send(graph, state, "It happened in Phoenix.")
    assert state["next_action"] == "reask"
    assert state["pending_slot"] == "incident_type"
    assert state["ledger"]["incident_type"].asked_count == 3
    assert state["ledger"]["incident_type"].status == SlotStatus.ASKED


def test_graph_advances_once_extraction_succeeds():
    graph = build_graph()
    state = init_state(session_id="demo-2")

    state = _send(graph, state, "Hi, I want to report a possible claim.")
    state = _send(graph, state, "My mom was in a car accident and she's hurt.")

    forced = [ExtractedValue("incident_type", IncidentType.CAR_ACCIDENT, 0.95)]
    with patch("graph.nodes.extract.extract_stub", return_value=forced):
        state = _send(graph, state, "It was a car accident.")

    assert state["ledger"]["incident_type"].status == SlotStatus.ANSWERED
    assert state["ledger"]["incident_type"].value == IncidentType.CAR_ACCIDENT
    assert state["next_action"] == "ask_slot"
    assert state["pending_slot"] == "incident_date"