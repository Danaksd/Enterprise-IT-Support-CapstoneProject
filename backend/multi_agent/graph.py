"""
Graph Wiring
============
Builds the LangGraph StateGraph.
All 7 agents are wired. Verification routes conditionally: resolved ->
END, not resolved -> escalation -> END.
"""

from multi_agent.agents.escalation import escalation_agent
from multi_agent.agents.issue_classification import issue_classification_agent
from multi_agent.agents.priority_assessment import priority_assessment_agent
from multi_agent.agents.ticket_intake import ticket_intake_agent
from multi_agent.agents.troubleshooting import troubleshooting_agent
from multi_agent.agents.verification import verification_agent
from multi_agent.agent_state import SharedState


def build_graph():
    """Builds and compiles the LangGraph StateGraph."""
    from langgraph.graph import END, StateGraph

    graph = StateGraph(SharedState)

    graph.add_node("ticket_intake", ticket_intake_agent)
    graph.add_node("issue_classification", issue_classification_agent)
    graph.add_node("priority_assessment", priority_assessment_agent)
    graph.add_node("troubleshooting", troubleshooting_agent)
    graph.add_node("verification", verification_agent)
    graph.add_node("escalation", escalation_agent)

    graph.set_entry_point("ticket_intake")
    graph.add_edge("ticket_intake", "issue_classification")
    graph.add_edge("issue_classification", "priority_assessment")
    graph.add_edge("priority_assessment", "troubleshooting")
    graph.add_edge("troubleshooting", "verification")

    graph.add_conditional_edges(
        "verification",
        lambda state: "resolved" if state.get("is_resolved") else "not_resolved",
        {"resolved": END, "not_resolved": "escalation"},
    )

    graph.add_edge("escalation", END)

    return graph.compile()
