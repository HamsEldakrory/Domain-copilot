import { Link } from "react-router-dom";
import { useSelector } from "react-redux";
import { useClaims } from "../hooks/useClaims";
import { useCurrentUser } from "../hooks/useAuth";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";

function StatCard({ label, value, sub, variant = "" }) {
  return (
    <div className={`stat-card ${variant}`}>
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value">{value}</div>
      {sub && <div className="stat-card-sub">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const { data: claims, isLoading, isError } = useClaims();
  useCurrentUser(true); // ensure user is in Redux store

  // Derive stats entirely from backend data — no fabrication
  const total   = claims?.length ?? 0;
  const pending = claims?.filter((c) => c.status === "submitted" || c.status === "pending").length ?? 0;
  const approved = claims?.filter((c) => c.status === "approved").length ?? 0;
  const recent  = claims?.slice(0, 5) ?? [];

  return (
    <AppShell title="Dashboard">
      <div className="page-header">
        <div>
          <div className="page-title">Dashboard</div>
          <div className="page-subtitle">Overview of your claims activity</div>
        </div>
      </div>

      {/* Stats */}
      {isLoading ? (
        <div className="stat-cards">
          {[1, 2, 3].map((i) => (
            <div key={i} className="stat-card">
              <div className="stat-card-label">Loading…</div>
              <div className="stat-card-value">—</div>
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="alert alert-error mb-24">
          Failed to load dashboard data.
        </div>
      ) : (
        <div className="stat-cards">
          <StatCard
            label="Total Claims"
            value={total}
            sub="in your scope"
            variant="brand"
          />
          <StatCard
            label="Pending / Submitted"
            value={pending}
            sub="awaiting review"
            variant="warning"
          />
          <StatCard
            label="Approved"
            value={approved}
            sub="completed"
            variant="success"
          />
        </div>
      )}

      {/* Recent Claims */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Claims</span>
          <Link to="/claims" className="btn btn-outline btn-sm">
            View all
          </Link>
        </div>

        {isLoading ? (
          <div className="card-body" style={{ textAlign: "center", padding: 40 }}>
            <span className="spinner" />
          </div>
        ) : isError ? (
          <div className="card-body">
            <div className="alert alert-error">Could not load claims.</div>
          </div>
        ) : recent.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📋</div>
            <div className="empty-state-title">No claims yet</div>
            <div className="empty-state-sub">
              Claims assigned to you will appear here.
            </div>
          </div>
        ) : (
          <div className="table-container" style={{ border: "none", borderRadius: 0, boxShadow: "none" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Claim ID</th>
                  <th>Client</th>
                  <th>Policy</th>
                  <th>Claim Date</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recent.map((claim) => (
                  <tr key={claim.id}>
                    <td>
                      <span className="font-mono text-xs">
                        {claim.id.slice(0, 8)}…
                      </span>
                    </td>
                    <td className="font-semibold">{claim.client_name || "—"}</td>
                    <td className="text-sm">{claim.policy_number ? `${claim.policy_number} (${claim.policy_version || 'v1'})` : "—"}</td>
                    <td>{claim.claim_date}</td>
                    <td>
                      <StatusBadge status={claim.status} />
                    </td>
                    <td className="text-muted text-sm">
                      {new Date(claim.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <Link to={`/claims/${claim.id}`} className="btn btn-ghost btn-sm">
                        Open →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
