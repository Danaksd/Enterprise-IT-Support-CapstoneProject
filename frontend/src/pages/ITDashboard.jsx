import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { apiFetch } from "../api.js";

const VIEWS = ["unclaimed", "mine", "resolved", "closed", "all"];

export default function ITDashboard() {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [view, setView] = useState("unclaimed");
  const [error, setError] = useState("");

  async function loadTickets() {
    try {
      const data = await apiFetch(`/tickets?view=${view}`, auth.token);
      setTickets(data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view]);

  return (
    <div className="page">
      <div className="topbar">
        <div className="eyebrow">
          <span className="dot" />
          IT Support Dashboard
        </div>
        <div className="topbar-right">
          <span>{auth.fullName}</span>
          <button className="btn-secondary" onClick={logout}>
            Log out
          </button>
        </div>
      </div>

      <h1>Support Tickets</h1>

      <div className="filter-row">
        {VIEWS.map((v) => (
          <button key={v} className={`filter-chip ${view === v ? "active" : ""}`} onClick={() => setView(v)}>
            {v}
          </button>
        ))}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="ticket-table">
        <div className="ticket-table-head">
          <span>Employee</span>
          <span>Department</span>
          <span>Category</span>
          <span>Priority</span>
          <span>Status</span>
        </div>
        {tickets.length === 0 && <p className="subtitle" style={{ padding: 16 }}>No tickets found.</p>}
        {tickets.map((t) => (
          <div className="ticket-table-row" key={t.id} onClick={() => navigate(`/ticket/${t.id}`)}>
            <span>{t.employee_name}</span>
            <span>{t.department}</span>
            <span>{t.category || "-"}</span>
            <span>{t.priority || "-"}</span>
            <span className={`status-badge status-${t.status}`}>{t.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
