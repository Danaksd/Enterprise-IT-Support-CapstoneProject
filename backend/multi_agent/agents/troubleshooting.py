"""Agent 4: Troubleshooting Agent.

Generates practical troubleshooting steps for the classified IT issue.
The agent follows the LangGraph node format:
(state: SharedState) -> dict
"""

from typing import List

from pydantic import BaseModel, Field, ValidationError

from multi_agent.llm_client import call_llm, extract_json
from multi_agent.agent_state import SharedState



class TroubleshootingResponse(BaseModel):
    """Expected JSON response from the LLM."""

    troubleshooting_steps: List[str] = Field(
        min_length=1,
        description="Ordered troubleshooting steps for the IT issue.",
    )


SYSTEM_PROMPT = """
You are the Troubleshooting Agent in an enterprise IT support workflow.

Your only job is to generate a short, safe, ordered list of troubleshooting
steps based on the ticket details, classification, and priority.

Rules:
- Return between 2 and 6 practical troubleshooting steps.
- Put the safest and least disruptive checks first.
- Do not claim that an action has already been performed.
- Do not include destructive actions.
- Do not delete user files or disable security controls.
- If information is missing, include a verification step instead of guessing.
- Keep every step concise and actionable.

Return ONLY a valid JSON object with this exact schema:
{
  "troubleshooting_steps": ["step 1", "step 2"]
}

Do not use markdown fences.
Do not include extra commentary.
""".strip()



def _build_user_prompt(state: SharedState) -> str:
    """Build the troubleshooting request from shared state."""

    return f"""
Generate troubleshooting steps for this IT support ticket.

Issue summary: {state.get("issue_summary") or "Unknown"}
Category: {state.get("category") or "Unknown"}
Priority: {state.get("priority") or "Unknown"}
Affected system: {state.get("affected_system") or "Unknown"}
Device: {state.get("device") or "Unknown"}
Operating system: {state.get("operating_system") or "Unknown"}
Error message: {state.get("error_message") or "None provided"}
Location: {state.get("location") or "Unknown"}
Missing information: {state.get("missing_information") or []}
Raw ticket: {state.get("raw_ticket_text") or "Not provided"}
""".strip()


def _append_history(
    state: SharedState,
    steps: List[str],
) -> List[str]:
    """Append the troubleshooting result without modifying the input state."""

    history = list(state.get("conversation_history") or [])

    history.append(
        "Troubleshooting Agent: " + " | ".join(steps)
    )

    return history


def troubleshooting_agent(state: SharedState) -> dict:
    """Generate troubleshooting steps for the current IT ticket."""

    fallback_steps = [
        "Confirm that the user can reproduce the issue and record the exact error message.",
        "Check the affected system's network connection and service availability.",
        "Restart the affected application or device, then test again.",
    ]

    try:
        raw_output = call_llm(
            SYSTEM_PROMPT,
            _build_user_prompt(state),
        )

        parsed_output = extract_json(raw_output)

        result = TroubleshootingResponse.model_validate(
            parsed_output
        )

        steps = [
            step.strip()
            for step in result.troubleshooting_steps
            if step.strip()
        ]

        if not steps:
            raise ValueError(
                "The LLM returned no usable troubleshooting steps."
            )

    except (ValidationError, ValueError, TypeError, KeyError) as exc:
        print(
            f"[Troubleshooting Agent] Warning: "
            f"using fallback steps: {exc}"
        )
        steps = fallback_steps

    except Exception as exc:
        print(
            f"[Troubleshooting Agent] Warning: "
            f"unexpected failure; using fallback: {exc}"
        )
        steps = fallback_steps

    return {
        "troubleshooting_steps": steps,
        "conversation_history": _append_history(state, steps),
    }

