"""
============================================================
REAL multi-agent pipeline bridge.
============================================================
This file adapts the team's SharedState-based agent functions
(backend/multi_agent/...) to the two moments the FastAPI backend
needs them:

1. run_pipeline() — at ticket submission. Runs:
     Ticket Intake -> Issue Classification -> Priority Assessment
     -> Troubleshooting
   Verification is human-driven (two buttons in the UI), so this
   does NOT decide resolved/not-resolved — it stops after generating
   troubleshooting steps and returns the full SharedState so it can
   be persisted (Ticket.agent_state) and resumed later.

2. run_verification() — at POST /tickets/{id}/verify. Takes the
   employee's Resolved/Not Resolved click, resumes from the saved
   state, runs Verification and (if not resolved) Escalation.
============================================================
"""

from multi_agent.agents.ticket_intake import ticket_intake_agent
from multi_agent.agents.issue_classification import issue_classification_agent
from multi_agent.agents.priority_assessment import priority_assessment_agent
from multi_agent.agents.troubleshooting import troubleshooting_agent
from multi_agent.agents.verification import verification_agent
from multi_agent.agents.escalation import escalation_agent


def run_pipeline(issue_description: str, device_type: str | None, operating_system: str | None, department: str | None) -> dict:
    """Runs Agents 1-4. Returns the full SharedState dict."""
    state: dict = {"raw_ticket_text": issue_description, "department": department}

    state.update(ticket_intake_agent(state))

    # The Ticket Intake Agent extracts device/OS from the ticket text if
    # mentioned; fall back to the employee's profile values when it didn't.
    if not state.get("device") and device_type:
        state["device"] = device_type
    if not state.get("operating_system") and operating_system:
        state["operating_system"] = operating_system

    state.update(issue_classification_agent(state))
    state.update(priority_assessment_agent(state))
    state.update(troubleshooting_agent(state))

    return state


def run_verification(state: dict, resolved: bool) -> dict:
    """Runs Agent 6 (+ Agent 7 if not resolved). Returns the updated SharedState dict."""
    state = dict(state)  # don't mutate the caller's copy
    state["is_resolved"] = resolved

    state.update(verification_agent(state))
    if not resolved:
        state.update(escalation_agent(state))

    return state
