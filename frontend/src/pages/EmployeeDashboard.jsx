import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { apiFetch } from "../api.js";

const STATUS_COLORS = {
  awaiting_verification: "status-processing",
  resolved: "status-resolved",
  escalated: "status-escalated",
  closed: "status-closed",
};

export default function EmployeeDashboard() {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();
  const [issue, setIssue] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [error, setError] = useState("");

  async function loadTickets() {
    try {
      const data = await apiFetch("/tickets/mine", auth.token);
      setTickets(data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const ticket = await apiFetch("/tickets", auth.token, {
        method: "POST",
        body: JSON.stringify({ issue_description: issue }),
      });
      setIssue("");
      navigate(`/ticket/${ticket.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <div className="topbar">
        <div className="eyebrow">
          <span className="dot" />
          Employee Portal
        </div>
        <div className="topbar-right">
          <span>{auth.fullName}</span>
          <button className="btn-secondary" onClick={logout}>
            Log out
          </button>
        </div>
      </div>

      <h1>Submit a support ticket</h1>
      <p className="subtitle">Describe your issue and we'll route it to the right place.</p>

      <form className="form-card stacked" onSubmit={handleSubmit}>
        <textarea
          value={issue}
          onChange={(e) => setIssue(e.target.value)}
          placeholder="e.g. My VPN keeps disconnecting every few minutes..."
          rows={4}
          required
        />
        <button className="btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Processing..." : "Submit Ticket"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      <div className="section">
        <div className="section-head">
          <h2>My Tickets</h2>
        </div>
        {tickets.length === 0 && <p className="subtitle">No tickets yet.</p>}
        <div className="ticket-list">
          {tickets.map((t) => (
            <div className="ticket-row" key={t.id} onClick={() => navigate(`/ticket/${t.id}`)}>
              <div className="ticket-main">
                <span className={`status-badge ${STATUS_COLORS[t.status]}`}>{t.status}</span>
                <span className="ticket-desc">{t.issue_description}</span>
              </div>
              <div className="ticket-meta">
                {t.category && <span>{t.category}</span>}
                {t.priority && <span>{t.priority}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
