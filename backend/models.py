import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, DateTime, JSON
from pydantic import BaseModel

from database import Base


# ------------------------------------------------------------------
# ORM models
# ------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    department = Column(String, nullable=True)
    device_type = Column(String, nullable=True)       # employee-only, helps Troubleshooting Agent
    operating_system = Column(String, nullable=True)  # employee-only
    hashed_password = Column(String)
    role = Column(String)  # "employee" | "it"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    employee_username = Column(String, index=True)
    employee_name = Column(String)
    department = Column(String)
    device_type = Column(String, nullable=True)
    operating_system = Column(String, nullable=True)

    issue_description = Column(String)

    category = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    troubleshooting_steps = Column(JSON, default=list)
    conversation_history = Column(JSON, default=list)
    agent_state = Column(JSON, default=dict)  # full SharedState snapshot, used to resume at verify

    status = Column(String, default="awaiting_verification")
    # awaiting_verification -> resolved
    #                       -> escalated -> (claimed_by set) -> closed

    claimed_by = Column(String, nullable=True)  # IT staff full_name once they take the ticket

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    escalated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)


# ------------------------------------------------------------------
# Pydantic schemas (API request/response shapes)
# ------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    role: str
    full_name: str


class SignupRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: str  # "employee" | "it"
    department: Optional[str] = None
    device_type: Optional[str] = None
    operating_system: Optional[str] = None


class UserOut(BaseModel):
    username: str
    full_name: str
    department: Optional[str] = None
    role: str


class TicketCreate(BaseModel):
    issue_description: str


class VerifyRequest(BaseModel):
    resolved: bool


class ConversationEntry(BaseModel):
    sender: str  # "employee" | "system" | "it"
    message: str
    timestamp: str


class TicketOut(BaseModel):
    id: int
    employee_username: str
    employee_name: str
    department: str
    device_type: Optional[str]
    operating_system: Optional[str]
    issue_description: str
    category: Optional[str]
    priority: Optional[str]
    troubleshooting_steps: List[str]
    conversation_history: List[dict]
    status: str
    claimed_by: Optional[str]
    created_at: datetime.datetime
    escalated_at: Optional[datetime.datetime]
    resolved_at: Optional[datetime.datetime]
    closed_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True
