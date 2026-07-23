"""
Agent 7: Escalation Agent
=========================
Runs only when the Verification Agent reports the issue is NOT resolved.
Produces a concise summary for the IT team, covering: issue summary,
category, priority, troubleshooting steps attempted, and conversation
history — matching the original spec.
"""

import json

from pydantic import BaseModel, ValidationError

from multi_agent.llm_client import call_llm, extract_json
from multi_agent.agent_state import SharedState


class EscalationResult(BaseModel):
    escalation_summary: str


def escalation_agent(state: SharedState) -> dict:
    """
    LangGraph-compatible node: (state: SharedState) -> dict of updates.
    """
    system_prompt = (
        "You are the Escalation Agent for an enterprise IT support system. "
        "The automated troubleshooting steps did NOT resolve the employee's issue, "
        "so this ticket needs to be handed off to a human IT team member. "
        "Write a concise, professional escalation summary that includes: "
        "the issue, the category, the priority, the troubleshooting steps already "
        "attempted, and any relevant conversation history. "
        "Do not invent details that aren't in the provided data. "
        "Respond with ONLY a valid JSON object, no markdown fences, no extra commentary, "
        "matching this exact schema:\n"
        "{\n"
        '  "escalation_summary": string\n'
        "}"
    )

    context = {
        "issue_summary": state.get("issue_summary"),
        "category": state.get("category"),
        "priority": state.get("priority"),
        "troubleshooting_steps": state.get("troubleshooting_steps"),
        "verification_notes": state.get("verification_notes"),
        "conversation_history": state.get("conversation_history"),
        "raw_ticket_text": state.get("raw_ticket_text"),
    }
    user_prompt = f"Ticket data:\n{json.dumps(context, indent=2)}"

    raw_output = call_llm(system_prompt, user_prompt)

    try:
        parsed = extract_json(raw_output)
        result = EscalationResult(**parsed)
    except (json.JSONDecodeError, ValidationError) as exc:
        # Fallback: assemble a plain-text summary directly from state so a
        # parsing failure never blocks a ticket from reaching the IT team.
        steps = "; ".join(state.get("troubleshooting_steps") or [])
        result = EscalationResult(
            escalation_summary=(
                f"[Auto-generated fallback] Issue: {state.get('issue_summary')}. "
                f"Category: {state.get('category')}, Priority: {state.get('priority')}. "
                f"Steps attempted: {steps}. (Escalation Agent parse error: {exc})"
            )
        )
        print(f"[escalation_agent] Failed to parse LLM output: {exc}\nRaw: {raw_output}")

    history = list(state.get("conversation_history") or [])
    history.append(f"Escalation Agent: {result.escalation_summary}")

    return {
        "escalation_summary": result.escalation_summary,
        "conversation_history": history,
    }
