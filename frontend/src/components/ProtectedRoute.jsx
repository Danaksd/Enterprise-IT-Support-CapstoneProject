import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute({ role, children }) {
  const { auth } = useAuth();

  if (!auth) {
    return <Navigate to="/login" replace />;
  }

  if (role && auth.role !== role) {
    // Logged in, but wrong role for this page — send them to their own dashboard.
    return <Navigate to={auth.role === "it" ? "/it" : "/employee"} replace />;
  }

  return children;
}
