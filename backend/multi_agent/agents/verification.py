"""
Agent 6: Verification Agent
============================
Records whether the employee confirmed the issue is resolved.

This agent is intentionally NOT an LLM call. The decision comes from a
human (the employee, via two buttons in the UI: "Resolved" / "Not
Resolved"), not from the model inferring it. This node's only job is to
normalize that human input into the shared state shape so the
conditional edge in graph.py can route on it.

Expected input: state["is_resolved"] must already be set to True/False
by whoever is driving the graph (the web backend, or a test harness)
BEFORE this node runs — this agent does not ask any questions itself.
"""

from multi_agent.agent_state import SharedState


def verification_agent(state: SharedState) -> dict:
    """
    LangGraph-compatible node: (state: SharedState) -> dict of updates.
    """
    resolved = state.get("is_resolved")

    if resolved is None:
        # Defensive default: if nothing was provided, treat as unresolved
        # so the ticket escalates to a human rather than silently closing.
        resolved = False
        notes = "No verification input received — defaulting to not resolved."
    elif resolved:
        notes = "Employee confirmed the issue is resolved."
    else:
        notes = "Employee reported the issue is not resolved."

    history = list(state.get("conversation_history") or [])
    history.append(f"Verification Agent: {notes}")

    return {
        "is_resolved": resolved,
        "verification_notes": notes,
        "conversation_history": history,
    }
