import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState("employee");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [deviceType, setDeviceType] = useState("");
  const [operatingSystem, setOperatingSystem] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const session = await signup({
        username,
        password,
        full_name: fullName,
        role,
        department: department || null,
        device_type: role === "employee" ? deviceType || null : null,
        operating_system: role === "employee" ? operatingSystem || null : null,
      });
      navigate(session.role === "it" ? "/it" : "/employee", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="eyebrow">
          <span className="dot" />
          IT Support Portal
        </div>
        <h1>Create an account</h1>

        <div className="role-toggle">
          <button
            type="button"
            className={role === "employee" ? "active" : ""}
            onClick={() => setRole("employee")}
          >
            Employee
          </button>
          <button type="button" className={role === "it" ? "active" : ""} onClick={() => setRole("it")}>
            IT Staff
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label>Full name</label>
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />

          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />

          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />

          <label>Department</label>
          <input value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="e.g. Marketing" />

          {role === "employee" && (
            <>
              <label>Device type</label>
              <input value={deviceType} onChange={(e) => setDeviceType(e.target.value)} placeholder="e.g. Laptop" />

              <label>Operating system</label>
              <input
                value={operatingSystem}
                onChange={(e) => setOperatingSystem(e.target.value)}
                placeholder="e.g. Windows 11"
              />
            </>
          )}

          {error && <div className="error-banner">{error}</div>}
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <div className="demo-hint">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
