import { Link } from "react-router-dom";

export default function Forbidden() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg)",
      }}
    >
      <div style={{ textAlign: "center", maxWidth: 400 }}>
        <div style={{ fontSize: 56, marginBottom: 16 }}>🔒</div>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
          Access Denied
        </h1>
        <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 14 }}>
          You don't have permission to view this page. This may be because you
          are not assigned to this claim, or your role does not allow this
          action.
        </p>
        <Link to="/dashboard" className="btn btn-primary">
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
