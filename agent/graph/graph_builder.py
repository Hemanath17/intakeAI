from langgraph.graph import END, StateGraph
from graph.nodes.compose_reply import compose_reply
from graph.nodes.consent_gate import consent_gate
from graph.nodes.emit import emit
from graph.nodes.emotional_policy import emotional_policy
from graph.nodes.evaluate_rules import evaluate_rules
from graph.nodes.extract import extract
from graph.nodes.ingest_turn import ingest_turn
from graph.nodes.jurisdiction_confirm import jurisdiction_confirm
from graph.nodes.jurisdiction_resolve import jurisdiction_resolve
from graph.nodes.merge_state import merge_state
from graph.nodes.safety_and_scope import safety_and_scope
from graph.nodes.select_next_action import select_next_action
from graph.state import IntakeState, Phase

def _route_after_safety(state: IntakeState) -> str:
    if state["phase"] == Phase.TERMINATED:
        return "skip_to_reply"
    return "continue"

def build_graph():
    builder = StateGraph(IntakeState)

    builder.add_node("ingest_turn", ingest_turn)
    builder.add_node("safety_and_scope", safety_and_scope)
    builder.add_node("extract", extract)
    builder.add_node("merge_state", merge_state)
    builder.add_node("jurisdiction_resolve", jurisdiction_resolve)
    builder.add_node("jurisdiction_confirm", jurisdiction_confirm)
    builder.add_node("consent_gate", consent_gate)
    builder.add_node("evaluate_rules", evaluate_rules)
    builder.add_node("emotional_policy", emotional_policy)
    builder.add_node("select_next_action", select_next_action)
    builder.add_node("compose_reply", compose_reply)
    builder.add_node("emit", emit)

    builder.set_entry_point("ingest_turn")
    builder.add_edge("ingest_turn", "safety_and_scope")

    builder.add_conditional_edges(
        "safety_and_scope",
        _route_after_safety,
        {"continue": "extract", "skip_to_reply": "compose_reply"},
    )

    builder.add_edge("extract", "jurisdiction_confirm")
    builder.add_edge("jurisdiction_confirm", "merge_state")
    builder.add_edge("merge_state", "jurisdiction_resolve")
    builder.add_edge("jurisdiction_resolve", "consent_gate")
    builder.add_edge("consent_gate", "evaluate_rules")
    builder.add_edge("evaluate_rules", "emotional_policy")
    builder.add_edge("emotional_policy", "select_next_action")
    builder.add_edge("select_next_action", "compose_reply")
    builder.add_edge("compose_reply", "emit")
    builder.add_edge("emit", END)
    return builder.compile()
