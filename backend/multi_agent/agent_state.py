"""
Shared State
============
Single source of truth for the state object that flows through every
agent in the graph. Every agent function reads from and writes partial
updates to this same shape, so add new fields here (not inside an
individual agent file) when a new agent needs to store something.
"""

from typing import List, Optional, TypedDict

# ------------------------------------------------------------------
# Shared constants — import these instead of retyping the lists so
# every agent (and any validation) stays in sync.
# ------------------------------------------------------------------

VALID_CATEGORIES = [
    "Email",
    "Network",
    "Hardware",
    "Software",
    "Account & Access",
    "Security",
    "Printer",
    "VPN",
]

VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]


class SharedState(TypedDict, total=False):
    # ---- input ----
    raw_ticket_text: str

    # ---- Employee profile (looked up from the internal user database,
    # not extracted from the ticket text — the employee is assumed to
    # already be authenticated when the ticket is created) ----
    department: Optional[str]

    # ---- Agent 1: Ticket Intake output ----
    issue_summary: Optional[str]
    affected_system: Optional[str]
    device: Optional[str]
    operating_system: Optional[str]
    error_message: Optional[str]
    location: Optional[str]
    missing_information: List[str]
    follow_up_questions: List[str]

    # ---- Agent 2: Issue Classification output ----
    category: Optional[str]
    classification_confidence: Optional[float]
    classification_reason: Optional[str]

    # ---- Agent 3: Priority Assessment output ----
    priority: Optional[str]
    priority_reason: Optional[str]

    # ---- Agent 4: Troubleshooting output ----
    troubleshooting_steps: List[str]

    # ---- Agent 6: Verification output ----
    is_resolved: Optional[bool]
    verification_notes: Optional[str]

    # ---- Agent 7: Escalation output ----
    escalation_summary: Optional[str]

    # ---- Shared across Agents 4-7 ----
    conversation_history: List[str]
