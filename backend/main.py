import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import (
    User, Ticket, LoginRequest, LoginResponse, SignupRequest,
    TicketCreate, VerifyRequest, TicketOut,
)
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from agent_stub import run_pipeline, run_verification

Base.metadata.create_all(bind=engine)

app = FastAPI(title="IT Support Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Seed a couple of demo accounts on startup (idempotent)
# ------------------------------------------------------------------
@app.on_event("startup")
def seed_demo_users():
    db = next(get_db())
    demo_users = [
        {"username": "employee1", "full_name": "Sara Al-Otaibi", "department": "Marketing", "role": "employee",
         "device_type": "Laptop", "operating_system": "Windows 11", "password": "password123"},
        {"username": "employee2", "full_name": "Omar Al-Harbi", "department": "Finance", "role": "employee",
         "device_type": "Desktop", "operating_system": "Windows 10", "password": "password123"},
        {"username": "it1", "full_name": "Fahad Al-Qahtani", "department": "IT", "role": "it",
         "device_type": None, "operating_system": None, "password": "password123"},
    ]
    for u in demo_users:
        if not db.query(User).filter(User.username == u["username"]).first():
            db.add(
                User(
                    username=u["username"],
                    full_name=u["full_name"],
                    department=u["department"],
                    device_type=u["device_type"],
                    operating_system=u["operating_system"],
                    role=u["role"],
                    hashed_password=hash_password(u["password"]),
                )
            )
    db.commit()


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------
@app.post("/auth/signup", response_model=LoginResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if req.role not in ("employee", "it"):
        raise HTTPException(status_code=400, detail="role must be 'employee' or 'it'")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=req.username,
        full_name=req.full_name,
        department=req.department,
        device_type=req.device_type if req.role == "employee" else None,
        operating_system=req.operating_system if req.role == "employee" else None,
        role=req.role,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()

    token = create_access_token(user.username, user.role)
    return LoginResponse(access_token=token, role=user.role, full_name=user.full_name)


@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.username, user.role)
    return LoginResponse(access_token=token, role=user.role, full_name=user.full_name)


@app.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"username": user.username, "full_name": user.full_name, "department": user.department, "role": user.role}


# ------------------------------------------------------------------
# Tickets — Employee
# ------------------------------------------------------------------
@app.post("/tickets", response_model=TicketOut)
def create_ticket(req: TicketCreate, user: User = Depends(require_role("employee")), db: Session = Depends(get_db)):
    ticket = Ticket(
        employee_username=user.username,
        employee_name=user.full_name,
        department=user.department or "Unassigned",
        device_type=user.device_type,
        operating_system=user.operating_system,
        issue_description=req.issue_description,
        status="awaiting_verification",
        conversation_history=[
            {"sender": "employee", "message": req.issue_description, "timestamp": datetime.datetime.utcnow().isoformat()}
        ],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # ---- runs Ticket Intake -> Issue Classification -> Priority Assessment -> Troubleshooting ----
    state = run_pipeline(req.issue_description, user.device_type, user.operating_system, user.department)

    ticket.category = state.get("category")
    ticket.priority = state.get("priority")
    ticket.troubleshooting_steps = state.get("troubleshooting_steps") or []
    ticket.agent_state = state  # snapshot so /verify can resume without re-running agents 1-4

    new_entries = [
        {"sender": "system", "message": line, "timestamp": datetime.datetime.utcnow().isoformat()}
        for line in (state.get("conversation_history") or [])
    ]
    ticket.conversation_history = ticket.conversation_history + new_entries

    db.commit()
    db.refresh(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/verify", response_model=TicketOut)
def verify_ticket(ticket_id: int, req: VerifyRequest, user: User = Depends(require_role("employee")), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.employee_username != user.username:
        raise HTTPException(status_code=403, detail="Not your ticket")
    if ticket.status != "awaiting_verification":
        raise HTTPException(status_code=400, detail="This ticket already has a verification decision")

    # ---- resumes from the saved SharedState, runs Verification (+ Escalation if not resolved) ----
    state = run_verification(ticket.agent_state or {}, req.resolved)
    ticket.agent_state = state

    if req.resolved:
        ticket.status = "resolved"
        ticket.resolved_at = datetime.datetime.utcnow()
        ticket.conversation_history = ticket.conversation_history + [
            {"sender": "employee", "message": "Confirmed: issue resolved.", "timestamp": datetime.datetime.utcnow().isoformat()}
        ]
    else:
        ticket.status = "escalated"
        ticket.escalated_at = datetime.datetime.utcnow()
        ticket.conversation_history = ticket.conversation_history + [
            {"sender": "employee", "message": "Reported: issue not resolved.", "timestamp": datetime.datetime.utcnow().isoformat()},
            {"sender": "system", "message": state.get("escalation_summary", ""), "timestamp": datetime.datetime.utcnow().isoformat()},
        ]

    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/tickets/mine", response_model=list[TicketOut])
def my_tickets(user: User = Depends(require_role("employee")), db: Session = Depends(get_db)):
    return db.query(Ticket).filter(Ticket.employee_username == user.username).order_by(Ticket.created_at.desc()).all()


# ------------------------------------------------------------------
# Tickets — IT
# ------------------------------------------------------------------
@app.get("/tickets", response_model=list[TicketOut])
def all_tickets(view: str = "unclaimed", user: User = Depends(require_role("it")), db: Session = Depends(get_db)):
    query = db.query(Ticket)

    if view == "unclaimed":
        query = query.filter(Ticket.status == "escalated", Ticket.claimed_by.is_(None))
    elif view == "mine":
        query = query.filter(Ticket.claimed_by == user.full_name)
    elif view == "resolved":
        query = query.filter(Ticket.status == "resolved")
    elif view == "closed":
        query = query.filter(Ticket.status == "closed")
    # view == "all" -> no filter

    return query.order_by(Ticket.created_at.desc()).all()


@app.patch("/tickets/{ticket_id}/claim", response_model=TicketOut)
def claim_ticket(ticket_id: int, user: User = Depends(require_role("it")), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.status != "escalated":
        raise HTTPException(status_code=400, detail="Only escalated tickets can be claimed")
    if ticket.claimed_by:
        raise HTTPException(status_code=400, detail=f"Already claimed by {ticket.claimed_by}")

    ticket.claimed_by = user.full_name
    db.commit()
    db.refresh(ticket)
    return ticket


@app.patch("/tickets/{ticket_id}/close", response_model=TicketOut)
def close_ticket(ticket_id: int, user: User = Depends(require_role("it")), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = "closed"
    ticket.closed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


# ------------------------------------------------------------------
# Tickets — shared (either role, but employee can only see their own)
# ------------------------------------------------------------------
@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if user.role == "employee" and ticket.employee_username != user.username:
        raise HTTPException(status_code=403, detail="Not your ticket")
    return ticket


@app.get("/health")
def health():
    return {"status": "ok"}