"""
Agent 2: Issue Classification Agent
====================================
Classifies the ticket into exactly one predefined category, using the
structured fields produced by the Ticket Intake Agent.
"""

import json

from pydantic import BaseModel, ValidationError

from multi_agent.llm_client import call_llm, extract_json
from multi_agent.agent_state import SharedState, VALID_CATEGORIES


class ClassificationResult(BaseModel):
    category: str
    confidence: float
    reason: str


def issue_classification_agent(state: SharedState) -> dict:
    """
    LangGraph-compatible node: (state: SharedState) -> dict of updates.
    """
    system_prompt = (
        "You are the Issue Classification Agent for an enterprise IT support system. "
        "Classify the ticket into EXACTLY ONE of the following categories: "
        f"{', '.join(VALID_CATEGORIES)}. "
        "Base your decision on the issue summary, affected system, error message, and any "
        "other extracted fields provided. "
        "Respond with ONLY a valid JSON object, no markdown fences, no extra commentary, "
        "matching this exact schema:\n"
        "{\n"
        '  "category": string (must be one of the listed categories),\n'
        '  "confidence": number between 0 and 1,\n'
        '  "reason": string (short explanation)\n'
        "}"
    )

    # Build the input from the intake agent's structured output rather than
    # the raw text, so classification uses clean, extracted data.
    intake_context = {
        "issue_summary": state.get("issue_summary"),
        "affected_system": state.get("affected_system"),
        "device": state.get("device"),
        "operating_system": state.get("operating_system"),
        "error_message": state.get("error_message"),
        "department": state.get("department"),
        "location": state.get("location"),
    }
    user_prompt = f"Extracted ticket data:\n{json.dumps(intake_context, indent=2)}"

    raw_output = call_llm(system_prompt, user_prompt)

    try:
        parsed = extract_json(raw_output)
        result = ClassificationResult(**parsed)
        if result.category not in VALID_CATEGORIES:
            raise ValueError(f"Unrecognized category returned: {result.category}")
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        result = ClassificationResult(
            category="Software",  # safe generic fallback
            confidence=0.0,
            reason=f"Classification failed, defaulted. Error: {exc}",
        )
        print(f"[issue_classification_agent] Failed to parse LLM output: {exc}\nRaw: {raw_output}")

    return {
        "category": result.category,
        "classification_confidence": result.confidence,
        "classification_reason": result.reason,
    }
