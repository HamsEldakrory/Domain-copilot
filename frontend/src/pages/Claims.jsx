import { Link } from "react-router-dom";
import { useClaims } from "../hooks/useClaims";
import { useCurrentUser } from "../hooks/useAuth";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";

export default function Claims() {
  const { data: claims, isLoading, isError, error } = useClaims();
  useCurrentUser(true);

  return (
    <AppShell title="Claims">
      <div className="page-header">
        <div>
          <div className="page-title">Claims</div>
          <div className="page-subtitle">All claims in your scope</div>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Client</th>
              <th>Policy</th>
              <th>Adjuster</th>
              <th>Claim Date</th>
              <th>Status</th>
              <th>Final Payout</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr className="loading-row">
                <td colSpan={9}>
                  <span className="spinner" /> Loading claims…
                </td>
              </tr>
            )}

            {isError && (
              <tr>
                <td colSpan={9}>
                  <div className="alert alert-error">
                    {error?.response?.data?.error ?? "Failed to load claims."}
                  </div>
                </td>
              </tr>
            )}

            {!isLoading && !isError && claims?.length === 0 && (
              <tr>
                <td colSpan={9}>
                  <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <div className="empty-state-title">No claims found</div>
                    <div className="empty-state-sub">
                      Claims assigned to you will appear here.
                    </div>
                  </div>
                </td>
              </tr>
            )}

            {claims?.map((claim) => (
              <tr key={claim.id}>
                <td>
                  <span className="font-mono text-xs">
                    {claim.id.slice(0, 8)}…
                  </span>
                </td>
                <td className="font-semibold">{claim.client_name || "—"}</td>
                <td>
                  {claim.policy_number ? (
                    <span>
                      {claim.policy_number}{" "}
                      <span className="text-muted text-xs">({claim.policy_version || "v1"})</span>
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="text-sm">{claim.adjuster_name || "—"}</td>
                <td>{claim.claim_date}</td>
                <td>
                  <StatusBadge status={claim.status} />
                </td>
                <td className="font-mono text-sm">
                  {claim.final_payout != null
                    ? `$${Number(claim.final_payout).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                    : "—"}
                </td>
                <td className="text-muted text-sm">
                  {new Date(claim.created_at).toLocaleDateString()}
                </td>
                <td>
                  <Link
                    to={`/claims/${claim.id}`}
                    className="btn btn-outline btn-sm"
                  >
                    Open →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
