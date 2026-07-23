"""
Agent 3: Priority Assessment Agent
===================================
Determines ticket urgency (Low / Medium / High / Critical) using the
intake fields and the classification result already present in state.
"""

import json

from pydantic import BaseModel, ValidationError

from multi_agent.llm_client import call_llm, extract_json
from multi_agent.agent_state import SharedState, VALID_PRIORITIES


class PriorityResult(BaseModel):
    priority: str
    reason: str


def priority_assessment_agent(state: SharedState) -> dict:
    """
    LangGraph-compatible node: (state: SharedState) -> dict of updates.
    """
    system_prompt = (
        "You are the Priority Assessment Agent for an enterprise IT support system. "
        "Determine the urgency of the ticket, choosing EXACTLY ONE of: "
        f"{', '.join(VALID_PRIORITIES)}. "
        "Consider: business impact, number of affected users (infer if not stated), "
        "security implications, whether a core business service is unavailable, and any "
        "urgency expressed by the user. "
        "Respond with ONLY a valid JSON object, no markdown fences, no extra commentary, "
        "matching this exact schema:\n"
        "{\n"
        '  "priority": string (must be one of the listed priorities),\n'
        '  "reason": string (short explanation)\n'
        "}"
    )

    context = {
        "issue_summary": state.get("issue_summary"),
        "affected_system": state.get("affected_system"),
        "department": state.get("department"),
        "location": state.get("location"),
        "error_message": state.get("error_message"),
        "category": state.get("category"),
        "classification_reason": state.get("classification_reason"),
        "raw_ticket_text": state.get("raw_ticket_text"),
    }
    user_prompt = f"Ticket data so far:\n{json.dumps(context, indent=2)}"

    raw_output = call_llm(system_prompt, user_prompt)

    try:
        parsed = extract_json(raw_output)
        result = PriorityResult(**parsed)
        if result.priority not in VALID_PRIORITIES:
            raise ValueError(f"Unrecognized priority returned: {result.priority}")
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        result = PriorityResult(
            priority="Medium",  # safe middle-ground fallback
            reason=f"Priority assessment failed, defaulted. Error: {exc}",
        )
        print(f"[priority_assessment_agent] Failed to parse LLM output: {exc}\nRaw: {raw_output}")

    return {
        "priority": result.priority,
        "priority_reason": result.reason,
    }
