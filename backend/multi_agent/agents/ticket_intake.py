"""
Agent 1: Ticket Intake Agent
============================
Reads the raw employee-reported issue and extracts structured fields.
Identifies missing information and drafts follow-up questions only when
something needed for diagnosis is genuinely missing.

Note: `department` is intentionally NOT extracted here. The employee is
assumed to already be authenticated, and their department is looked up
separately from the internal user database before this agent ever runs.
"""

import json
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError

from multi_agent.llm_client import call_llm, extract_json
from multi_agent.agent_state import SharedState


class IntakeResult(BaseModel):
    issue_summary: Optional[str] = None
    affected_system: Optional[str] = None
    device: Optional[str] = None
    operating_system: Optional[str] = None
    error_message: Optional[str] = None
    location: Optional[str] = None
    missing_information: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)


def ticket_intake_agent(state: SharedState) -> dict:
    """
    LangGraph-compatible node: (state: SharedState) -> dict of updates.
    """
    system_prompt = (
        "You are the Ticket Intake Agent for an enterprise IT support system. "
        "Extract structured information from an employee's IT issue description. "
        "Fields to extract: issue_summary, affected_system, device, operating_system, "
        "error_message, location. "
        "Do NOT attempt to determine the employee's department — the employee is already "
        "authenticated and their department is looked up separately from the internal "
        "user database, not extracted from the ticket text. "
        "If a field is not mentioned or cannot be inferred, set it to null — never guess. "
        "List any fields that are missing but would help diagnose the issue in "
        "'missing_information'. Only generate 'follow_up_questions' for information that is "
        "genuinely necessary to diagnose or resolve the issue (do not ask unnecessary questions). "
        "Respond with ONLY a valid JSON object, no markdown fences, no extra commentary, "
        "matching this exact schema:\n"
        "{\n"
        '  "issue_summary": string or null,\n'
        '  "affected_system": string or null,\n'
        '  "device": string or null,\n'
        '  "operating_system": string or null,\n'
        '  "error_message": string or null,\n'
        '  "location": string or null,\n'
        '  "missing_information": [string, ...],\n'
        '  "follow_up_questions": [string, ...]\n'
        "}"
    )

    user_prompt = f"Employee ticket text:\n\"\"\"\n{state['raw_ticket_text']}\n\"\"\""

    raw_output = call_llm(system_prompt, user_prompt)

    try:
        parsed = extract_json(raw_output)
        result = IntakeResult(**parsed)
    except (json.JSONDecodeError, ValidationError) as exc:
        # Fail safe: don't crash the pipeline, surface the issue in state instead.
        result = IntakeResult(
            issue_summary=None,
            missing_information=["intake_agent_parse_error"],
            follow_up_questions=[],
        )
        print(f"[ticket_intake_agent] Failed to parse LLM output: {exc}\nRaw: {raw_output}")

    # Return only the keys this agent is responsible for; LangGraph merges
    # this partial dict into the overall SharedState.
    return result.model_dump()
