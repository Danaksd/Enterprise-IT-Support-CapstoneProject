import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { apiFetch } from "../api.js";

export default function TicketDetail() {
  const { id } = useParams();
  const { auth } = useAuth();
  const showToast = useToast();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState("");
  const [verifying, setVerifying] = useState(false);

  async function load() {
    try {
      const data = await apiFetch(`/tickets/${id}`, auth.token);
      setTicket(data);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleVerify(resolved) {
    setVerifying(true);
    try {
      await apiFetch(`/tickets/${id}/verify`, auth.token, {
        method: "POST",
        body: JSON.stringify({ resolved }),
      });
      showToast(resolved ? "Great — ticket marked as resolved." : "Escalated to the IT team.");
      await load();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setVerifying(false);
    }
  }

  async function handleClaim() {
    try {
      await apiFetch(`/tickets/${id}/claim`, auth.token, { method: "PATCH" });
      showToast("Ticket assigned to you.");
      await load();
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  async function handleClose() {
    try {
      await apiFetch(`/tickets/${id}/close`, auth.token, { method: "PATCH" });
      showToast("Ticket closed.");
      await load();
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  if (error) return <div className="page"><div className="error-banner">{error}</div></div>;
  if (!ticket) return <div className="page"><p className="subtitle">Loading...</p></div>;

  const isOwner = auth.role === "employee" && ticket.employee_username;
  const canVerify = isOwner && ticket.status === "awaiting_verification";

  return (
    <div className="page">
      <button className="btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 24 }}>
        ← Back
      </button>

      <div className="eyebrow">
        <span className="dot" />
        Ticket #{ticket.id}
      </div>
      <h1>{ticket.category || "Uncategorized"} issue</h1>

      <div className="detail-grid">
        <div className="detail-item">
          <span className="detail-label">Employee</span>
          <span>{ticket.employee_name}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Department</span>
          <span>{ticket.department}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Device</span>
          <span>{ticket.device_type || "-"} {ticket.operating_system ? `(${ticket.operating_system})` : ""}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Priority</span>
          <span>{ticket.priority || "-"}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Status</span>
          <span className={`status-badge status-${ticket.status}`}>{ticket.status}</span>
        </div>
        {ticket.claimed_by && (
          <div className="detail-item">
            <span className="detail-label">Claimed by</span>
            <span>{ticket.claimed_by}</span>
          </div>
        )}
      </div>

      <div className="section">
        <div className="section-head">
          <h2>Issue Description</h2>
        </div>
        <div className="report-card">{ticket.issue_description}</div>
      </div>

      {ticket.troubleshooting_steps?.length > 0 && (
        <div className="section">
          <div className="section-head">
            <h2>Suggested Troubleshooting Steps</h2>
          </div>
          <div className="report-card">
            <ul>
              {ticket.troubleshooting_steps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {canVerify && (
        <div className="section">
          <div className="section-head">
            <h2>Did this solve your issue?</h2>
          </div>
          <div className="verify-buttons">
            <button className="btn-primary" disabled={verifying} onClick={() => handleVerify(true)}>
              ✅ Resolved
            </button>
            <button className="btn-secondary" disabled={verifying} onClick={() => handleVerify(false)}>
              ❌ Not Resolved
            </button>
          </div>
        </div>
      )}

      <div className="section">
        <div className="section-head">
          <h2>Conversation History</h2>
        </div>
        <div className="logs-card">
          {ticket.conversation_history.map((c, i) => (
            <div className="log-row" key={i}>
              <span className={`agent-tag agent-${c.sender}`}>{c.sender}</span>
              <span>{c.message}</span>
            </div>
          ))}
        </div>
      </div>

      {auth.role === "it" && ticket.status === "escalated" && !ticket.claimed_by && (
        <button className="btn-primary" style={{ marginTop: 24 }} onClick={handleClaim}>
          Take this ticket
        </button>
      )}

      {auth.role === "it" && ticket.claimed_by === auth.fullName && ticket.status !== "closed" && (
        <button className="btn-primary" style={{ marginTop: 24 }} onClick={handleClose}>
          Mark as Closed
        </button>
      )}
    </div>
  );
}
