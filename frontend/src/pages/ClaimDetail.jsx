import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useSelector } from "react-redux";
import { useForm } from "react-hook-form";
import { useClaim } from "../hooks/useClaims";
import {
  useAsk,
  useAdjudicate,
  useApprovalDecision,
  useTrace,
  useJobStatus,
  useCancelJob,
} from "../hooks/useAdjudication";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";
import EditApproveDialog from "../components/EditApproveDialog";

// ── SSE stream entry types ────────────────────────────
const AGENT_EVENT_TYPES = ["agent_started", "agent_progress", "agent_complete"];

function getStreamEntryClass(type) {
  if (type === "token")            return "stream-entry-token";
  if (type === "status")           return "stream-entry-status";
  if (type === "done")             return "stream-entry-done";
  if (type === "error" || type === "timeout") return "stream-entry-error";
  if (AGENT_EVENT_TYPES.includes(type)) return "stream-entry-agent";
  return "stream-entry-default";
}

// ── AI token buffer renderer ──────────────────────────
function TokenStream({ events, isStreaming }) {
  const tokens = events
    .filter((e) => e.type === "token")
    .map((e) => e.data.token ?? "")
    .join("");

  if (!tokens && !isStreaming) return null;

  return (
    <div style={{ marginTop: 12 }}>
      <div className="detail-field-label" style={{ marginBottom: 6 }}>
        AI Output
      </div>
      <div className="ai-output">
        {tokens}
        {isStreaming && <span className="ai-cursor" />}
      </div>
    </div>
  );
}

// ── Payout result card ────────────────────────────────
function PayoutCard({ events }) {
  const payoutEvent = [...events].reverse().find((e) => e.type === "payout");
  if (!payoutEvent) return null;

  const { payout, claimed_amount, deductible_applied, policy_limit, capped_by_limit, anomaly_flags = [] } =
    payoutEvent.data;

  const fmt = (n) =>
    n != null
      ? `$${Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      : "—";

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        border: "1px solid rgba(99,102,241,0.35)",
        borderRadius: "var(--radius)",
        padding: "20px 24px",
        marginTop: 16,
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 13, color: "var(--accent)", marginBottom: 14, letterSpacing: 1, textTransform: "uppercase" }}>
        💰 Payout Calculation
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 24px" }}>
        {[
          { label: "Claimed Amount", value: fmt(claimed_amount) },
          { label: "Deductible Applied", value: fmt(deductible_applied), muted: true },
          { label: "Policy Limit", value: fmt(policy_limit), muted: true },
          { label: "Capped by Limit", value: capped_by_limit ? "Yes" : "No", muted: true },
        ].map(({ label, value, muted }) => (
          <div key={label}>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>{label}</div>
            <div style={{ fontSize: 14, color: muted ? "var(--text-secondary)" : "var(--text-primary)", fontWeight: muted ? 400 : 600 }}>
              {value}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          marginTop: 16,
          borderTop: "1px solid rgba(255,255,255,0.07)",
          paddingTop: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Recommended Payout</div>
        <div
          style={{
            fontSize: 28,
            fontWeight: 800,
            color: payout > 0 ? "#34d399" : "#f87171",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {fmt(payout)}
        </div>
      </div>

      {anomaly_flags.length > 0 && (
        <div style={{ marginTop: 10, padding: "8px 12px", background: "rgba(245,158,11,0.1)", borderRadius: 6, border: "1px solid rgba(245,158,11,0.3)" }}>
          <span style={{ fontSize: 12, color: "#f59e0b" }}>
            ⚠ Flags: {anomaly_flags.join(", ")}
          </span>
        </div>
      )}
    </div>
  );
}

// ── Ask results renderer ──────────────────────────────
function AskResult({ result }) {
  if (!result) return null;
  if (result.refused) {
    return (
      <div className="alert alert-warning mt-12">
        <strong>Refused:</strong> {result.reason}
      </div>
    );
  }
  if (!result.citations?.length) {
    return (
      <div className="alert alert-info mt-12">No relevant policy clauses found.</div>
    );
  }
  return (
    <div style={{ marginTop: 12 }}>
      <div className="detail-field-label mb-8">Citations</div>
      {result.citations.map((c, i) => (
        <div
          key={i}
          style={{
            padding: "10px 14px",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)",
            marginBottom: 8,
            fontSize: 13,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>
            {c.document} — {c.section}
          </div>
          <div style={{ color: "var(--text-secondary)" }}>{c.excerpt}</div>
        </div>
      ))}
    </div>
  );
}

export default function ClaimDetail() {
  const { claimId } = useParams();
  const { data: claim, isLoading: claimLoading, isError: claimError } =
    useClaim(claimId);

  const askForm = useForm();
  const runForm = useForm();
  const ask = useAsk();
  const adjudicate = useAdjudicate();

  const [askResult, setAskResult] = useState(null);
  const [jobId, setJobId]         = useState(null);
  const [events, setEvents]       = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTab, setActiveTab]    = useState("overview");
  const [approveDialog, setApproveDialog] = useState(null); // {decision, label}
  const [cancelDialog, setCancelDialog]   = useState(false);
  const esRef     = useRef(null);
  const streamRef = useRef(null);

  const access    = useSelector((state) => state.auth.access);
  const approval  = useApprovalDecision(jobId);
  const cancelMut = useCancelJob(jobId);
  const { data: trace, refetch: refetchTrace } = useTrace(jobId, false);
  const { data: jobStatusData } = useJobStatus(jobId, Boolean(jobId) && !isStreaming);

  // Close SSE on unmount
  useEffect(() => {
    return () => esRef.current?.close();
  }, []);

  // ── Auto-detect a WAITING_APPROVAL or RUNNING job from the claim ─────────
  // This makes the approval panel visible even when the user navigates to the
  // page fresh (jobId is null by default because it's only set when the user
  // submits a new adjudication in this session).
  useEffect(() => {
    if (!claim?.jobs?.length || jobId || isStreaming) return;
    const pending = claim.jobs.find(
      (j) => j.status === "WAITING_APPROVAL" || j.status === "RUNNING"
    );
    if (pending) setJobId(pending.id);
  }, [claim, jobId, isStreaming]);

  const liveStatus = isStreaming
    ? events.findLast?.((e) => e.type === "status")?.data?.status
    : (jobStatusData?.status ?? null);

  const isWaitingApproval = liveStatus === "WAITING_APPROVAL";
  const isTerminal = ["COMPLETED","FAILED","CANCELLED"].includes(liveStatus);

  // ── Ask handler ───────────────────────────────────
  const onAsk = (data) => {
    ask.mutate(
      { claimId, query: data.query },
      {
        onSuccess: setAskResult,
        onError: (err) => {
          setAskResult({ refused: true, reason: err?.response?.data?.error ?? "Request failed." });
        },
      }
    );
  };

  // ── Adjudication + SSE ────────────────────────────
  const onRun = (data) => {
    adjudicate.mutate(
      {
        claimId,
        claimedAmount: data.claimedAmount,
        deductibleOverride: data.deductibleOverride || undefined,
      },
      {
        onSuccess: (response) => {
          const newJobId = response.job_id;
          setJobId(newJobId);
          setEvents([]);
          setIsStreaming(true);
          esRef.current?.close();

          // Connect to SSE — auth via query param (EventSource limitation)
          const url = `${import.meta.env.VITE_API_BASE_URL}/jobs/${newJobId}/stream/?access=${access}`;
          const es = new EventSource(url);
          esRef.current = es;

          const ALL_TYPES = [
            "status","agent_started","agent_progress","token",
            "agent_complete","done","timeout","error",
          ];

          ALL_TYPES.forEach((type) => {
            es.addEventListener(type, (event) => {
              let parsed;
              try { parsed = JSON.parse(event.data); } catch { parsed = event.data; }
              setEvents((prev) => [...prev, { type, data: parsed }]);
              if (type === "done" || type === "timeout" || type === "error") {
                setIsStreaming(false);
                es.close();
              }
              // Also stop on terminal status events
              if (type === "status") {
                const s = parsed?.status;
                if (
                  s === "COMPLETED" || s === "FAILED" ||
                  s === "CANCELLED" || s === "WAITING_APPROVAL"
                ) {
                  setIsStreaming(false);
                  if (s !== "WAITING_APPROVAL") es.close();
                }
              }
            });
          });

          es.onerror = () => {
            setIsStreaming(false);
            setEvents((prev) => [
              ...prev,
              { type: "error", data: { message: "SSE connection lost." } },
            ]);
            es.close();
          };

          streamRef.current = es;
          setActiveTab("adjudication");
        },
      }
    );
  };

  // ── Approval ──────────────────────────────────────
  const handleApprovalConfirm = (finalPayout = null, editRationale = null) => {
    if (!approveDialog) return;
    const isEdit = approveDialog.decision === "edit";
    
    // Construct original_recommendation
    const payoutEvent = [...events].reverse().find(e => e.type === "payout");
    const original_recommendation = {
      payout: payoutEvent?.data?.payout,
      rationale: events.filter(e => e.type === "token").map(e => e.data.token ?? "").join("")
    };

    approval.mutate(
      {
        decision: approveDialog.decision,
        outcome:  approveDialog.decision === "reject" ? "rejected" : "approved",
        rationale: (isEdit && editRationale) ? editRationale : "Reviewed via UI",
        final_payout: isEdit ? finalPayout : null,
        original_recommendation: isEdit ? original_recommendation : null,
      },
      {
        onSuccess: () => {
          setApproveDialog(null);
          refetchTrace();
          setActiveTab("trace");
        },
        onError: () => setApproveDialog(null),
      }
    );
  };

  // ── Cancel ────────────────────────────────────────
  const handleCancelConfirm = () => {
    cancelMut.mutate(undefined, {
      onSuccess: () => {
        setCancelDialog(false);
        esRef.current?.close();
        setIsStreaming(false);
      },
      onError: () => setCancelDialog(false),
    });
  };

  // ── Scroll stream log to bottom ───────────────────
  useEffect(() => {
    if (streamRef.current) return;
    const el = document.getElementById("stream-log");
    if (el) el.scrollTop = el.scrollHeight;
  }, [events]);

  // ── Render guards ─────────────────────────────────
  if (claimLoading) {
    return (
      <AppShell title="Claim Detail">
        <div style={{ textAlign: "center", padding: 60 }}>
          <span className="spinner" /> Loading claim…
        </div>
      </AppShell>
    );
  }

  if (claimError || !claim) {
    return (
      <AppShell title="Claim Detail">
        <div className="alert alert-error">
          Claim not found or you do not have access.{" "}
          <Link to="/claims">Back to claims</Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title={`Claim — ${claim.claim_date}`}>
      {/* ── Page header ── */}
      <div className="page-header">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div className="page-title">Claim Detail</div>
            <StatusBadge status={claim.status} />
          </div>
          <div className="page-subtitle">
            <Link to="/claims">← All claims</Link>
            <span style={{ margin: "0 8px", color: "var(--text-muted)" }}>·</span>
            <span className="font-mono text-xs">{claim.id}</span>
          </div>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="tabs">
        {["overview", "adjudication", "trace"].map((tab) => (
          <button
            key={tab}
            className={`tab-btn${activeTab === tab ? " active" : ""}`}
            onClick={() => setActiveTab(tab)}
            style={{ position: "relative" }}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === "adjudication" && isWaitingApproval && (
              <span
                style={{
                  display: "inline-block",
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "#f59e0b",
                  marginLeft: 6,
                  verticalAlign: "middle",
                  boxShadow: "0 0 0 2px rgba(245,158,11,0.4)",
                  animation: "pulse 1.5s infinite",
                }}
              />
            )}
          </button>
        ))}
      </div>

      {/* ── Tab: Overview ── */}
      {activeTab === "overview" && (
        <div>
          {/* ── Awaiting Approval Banner ── */}
          {isWaitingApproval && (
            <div
              style={{
                background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                borderRadius: "var(--radius)",
                padding: "20px 24px",
                marginBottom: 16,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 16,
                boxShadow: "0 4px 16px rgba(245,158,11,0.35)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 28 }}>⏸</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, color: "#fff" }}>
                    Awaiting Your Decision
                  </div>
                  <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", marginTop: 2 }}>
                    The AI pipeline has paused and requires human approval to finalize this claim.
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                <button
                  className="btn btn-sm"
                  style={{
                    background: "#fff",
                    color: "#d97706",
                    fontWeight: 700,
                    border: "none",
                  }}
                  onClick={() =>
                    setApproveDialog({ decision: "approve", label: "Approve Claim" })
                  }
                  disabled={approval.isPending}
                >
                  ✓ Approve
                </button>
                <button
                  className="btn btn-sm"
                  style={{
                    background: "rgba(0,0,0,0.2)",
                    color: "#fff",
                    fontWeight: 700,
                    border: "1px solid rgba(255,255,255,0.3)",
                  }}
                  onClick={() =>
                    setApproveDialog({ decision: "reject", label: "Reject Claim" })
                  }
                  disabled={approval.isPending}
                >
                  ✗ Reject
                </button>
                <button
                  className="btn btn-sm"
                  style={{
                    background: "rgba(0,0,0,0.2)",
                    color: "#fff",
                    border: "1px solid rgba(255,255,255,0.3)",
                  }}
                  onClick={() => {
                    setActiveTab("adjudication");
                  }}
                >
                  View Stream →
                </button>
              </div>
            </div>
          )}

          {/* Claim info card */}
          <div className="card mb-16">
            <div className="card-header">
              <span className="card-title">Claim Information</span>
            </div>
            <div className="card-body">
              <div className="detail-grid">
                <div>
                  <div className="detail-field-label">Client Name</div>
                  <div className="detail-field-value font-semibold">{claim.client_name || "—"}</div>
                </div>
                <div>
                  <div className="detail-field-label">Policy Number & Version</div>
                  <div className="detail-field-value">
                    {claim.policy_number ? `${claim.policy_number} (${claim.policy_version || "v1"})` : "—"}
                  </div>
                </div>
                <div>
                  <div className="detail-field-label">Policy Limit / Deductible</div>
                  <div className="detail-field-value text-sm text-secondary">
                    {claim.policy_limit != null ? `$${Number(claim.policy_limit).toLocaleString()}` : "—"} / {claim.deductible != null ? `$${Number(claim.deductible).toLocaleString()}` : "—"}
                  </div>
                </div>
                <div>
                  <div className="detail-field-label">Assigned Adjuster</div>
                  <div className="detail-field-value">
                    {claim.adjuster_name ? (
                      <span>
                        👤 {claim.adjuster_name}{" "}
                        {claim.adjuster_email && (
                          <span className="text-muted text-xs">({claim.adjuster_email})</span>
                        )}
                      </span>
                    ) : (
                      "—"
                    )}
                  </div>
                </div>
                <div>
                  <div className="detail-field-label">Claim Date</div>
                  <div className="detail-field-value">{claim.claim_date}</div>
                </div>
                <div>
                  <div className="detail-field-label">Status</div>
                  <div className="detail-field-value">
                    <StatusBadge status={claim.status} />
                  </div>
                </div>
                <div>
                  <div className="detail-field-label">Final Payout</div>
                  <div className="detail-field-value font-semibold" style={{ color: claim.final_payout != null ? "var(--accent)" : "var(--text-muted)" }}>
                    {claim.final_payout != null
                      ? `$${Number(claim.final_payout).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                      : "Not finalized"}
                  </div>
                </div>
                <div>
                  <div className="detail-field-label">Created</div>
                  <div className="detail-field-value text-sm text-muted">
                    {new Date(claim.created_at).toLocaleString()}
                  </div>
                </div>
                <div style={{ gridColumn: "1 / -1" }}>
                  <div className="detail-field-label">Claim ID</div>
                  <div className="detail-field-value font-mono text-xs text-muted">
                    {claim.id}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Jobs history */}
          {claim.jobs?.length > 0 && (
            <div className="card mb-16">
              <div className="card-header">
                <span className="card-title">Adjudication Jobs</span>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Job ID</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {claim.jobs.map((job) => (
                    <tr key={job.id}>
                      <td className="font-mono text-xs">
                        {job.id.slice(0, 8)}…
                      </td>
                      <td>
                        <StatusBadge status={job.status} />
                      </td>
                      <td className="text-muted text-sm">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => {
                            setJobId(job.id);
                            setActiveTab("adjudication");
                          }}
                        >
                          View →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Ask section */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Ask Policy Question</span>
              <span className="text-muted text-sm">RAG retrieval from policy documents</span>
            </div>
            <div className="card-body">
              <form onSubmit={askForm.handleSubmit(onAsk)}>
                <div style={{ display: "flex", gap: 10 }}>
                  <input
                    className="form-control"
                    placeholder="e.g. What is the deductible? What events are excluded?"
                    {...askForm.register("query", { required: true })}
                  />
                  <button
                    type="submit"
                    className="btn btn-outline"
                    disabled={ask.isPending}
                    style={{ flexShrink: 0 }}
                  >
                    {ask.isPending ? <span className="spinner" /> : "Ask"}
                  </button>
                </div>
              </form>
              {ask.isError && (
                <div className="alert alert-error mt-12">
                  {ask.error?.response?.data?.error ?? "Ask request failed."}
                </div>
              )}
              <AskResult result={askResult} />
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Adjudication ── */}
      {activeTab === "adjudication" && (
        <div>
          {/* Run form */}
          <div className="card mb-16">
            <div className="card-header">
              <span className="card-title">Run AI Adjudication</span>
              {jobId && liveStatus && (
                <StatusBadge status={liveStatus} />
              )}
            </div>
            <div className="card-body">
              <form onSubmit={runForm.handleSubmit(onRun)}>
                <div className="form-row">
                  <div className="form-group mb-0">
                    <label className="form-label required">Claimed Amount ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      className="form-control"
                      placeholder="0.00"
                      {...runForm.register("claimedAmount", {
                        required: "Claimed amount is required",
                        min: { value: 0, message: "Must be ≥ 0" },
                      })}
                    />
                    {runForm.formState.errors.claimedAmount && (
                      <div className="form-error">
                        {runForm.formState.errors.claimedAmount.message}
                      </div>
                    )}
                  </div>
                  <div className="form-group mb-0">
                    <label className="form-label">Deductible Override ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      className="form-control"
                      placeholder="Leave blank to use policy default"
                      {...runForm.register("deductibleOverride")}
                    />
                  </div>
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    marginTop: 16,
                    alignItems: "center",
                  }}
                >
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={adjudicate.isPending || isStreaming}
                  >
                    {adjudicate.isPending || isStreaming ? (
                      <><span className="spinner" /> Running…</>
                    ) : (
                      "▶ Run Adjudication"
                    )}
                  </button>
                  {jobId && isStreaming && (
                    <button
                      type="button"
                      className="btn btn-outline"
                      onClick={() => setCancelDialog(true)}
                    >
                      ⏹ Cancel
                    </button>
                  )}
                  {jobId && (
                    <span className="text-muted text-sm font-mono">
                      Job: {jobId.slice(0, 8)}…
                    </span>
                  )}
                </div>
              </form>

              {adjudicate.isError && (
                <div className="alert alert-error mt-12">
                  {adjudicate.error?.response?.data?.error ??
                    "Failed to submit adjudication."}
                </div>
              )}
            </div>
          </div>

          {/* SSE Stream */}
          {events.length > 0 && (
            <div className="card mb-16">
              <div className="card-header">
                <span className="card-title">Live Stream</span>
                {isStreaming && (
                  <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--brand-500)" }}>
                    <span className="spinner" style={{ width: 12, height: 12, borderWidth: 1.5 }} />
                    Streaming…
                  </span>
                )}
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                <div className="stream-log" id="stream-log">
                  {events.map((e, i) => (
                    <div
                      key={i}
                      className={`stream-entry ${getStreamEntryClass(e.type)}`}
                    >
                      <span className="stream-type-label">[{e.type}]</span>
                      <span className="stream-entry-data">
                        {e.type === "token"
                          ? e.data.token
                          : typeof e.data === "string"
                          ? e.data
                          : JSON.stringify(e.data)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <TokenStream events={events} isStreaming={isStreaming} />
              <PayoutCard events={events} />
            </div>
          )}

          {/* Approval section — only show when job is WAITING_APPROVAL */}
          {jobId && (isWaitingApproval || isTerminal) && (
            <div className="card mb-16">
              <div className="card-header">
                <span className="card-title">Human Review & Decision</span>
                {liveStatus && <StatusBadge status={liveStatus} />}
              </div>
              <div className="card-body">
                {isWaitingApproval ? (
                  <>
                    <p style={{ marginBottom: 16, color: "var(--text-secondary)", fontSize: 13 }}>
                      The AI adjudication is complete and awaiting your human review.
                      Review the stream output above and make a decision.
                    </p>
                    <div style={{ display: "flex", gap: 10 }}>
                      <button
                        className="btn btn-success"
                        onClick={() =>
                          setApproveDialog({ decision: "approve", label: "Approve Claim" })
                        }
                        disabled={approval.isPending}
                      >
                        ✓ Approve
                      </button>
                      <button
                        className="btn btn-outline"
                        style={{ borderColor: "#6366f1", color: "#6366f1" }}
                        onClick={() =>
                          setApproveDialog({ decision: "edit", label: "Edit & Approve" })
                        }
                        disabled={approval.isPending}
                      >
                        ✎ Edit & Approve
                      </button>
                      <button
                        className="btn btn-danger"
                        onClick={() =>
                          setApproveDialog({ decision: "reject", label: "Reject Claim" })
                        }
                        disabled={approval.isPending}
                      >
                        ✗ Reject
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="alert alert-info">
                    This job is{" "}
                    <strong>{liveStatus?.toLowerCase()}</strong>.
                    No further action required.
                  </div>
                )}

                {approval.isError && (
                  <div className="alert alert-error mt-12">
                    {approval.error?.response?.data?.error ?? "Decision failed."}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Trace ── */}
      {activeTab === "trace" && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Execution Trace</span>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => refetchTrace()}
              disabled={!jobId}
            >
              Refresh
            </button>
          </div>

          {!jobId ? (
            <div className="empty-state">
              <div className="empty-state-icon">🔍</div>
              <div className="empty-state-title">No job selected</div>
              <div className="empty-state-sub">
                Run an adjudication first, then return here.
              </div>
            </div>
          ) : !trace ? (
            <div className="card-body" style={{ textAlign: "center" }}>
              <span className="spinner" /> Loading trace…
            </div>
          ) : trace.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-title">No trace events yet</div>
              <div className="empty-state-sub">Try refreshing once the job completes.</div>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Kind</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {trace.map((item, i) => (
                  <tr key={i}>
                    <td className="text-xs text-muted font-mono">
                      {item.timestamp}
                    </td>
                    <td>
                      <span className="badge badge-running" style={{ fontSize: 10 }}>
                        {item.kind}
                      </span>
                    </td>
                    <td>
                      <pre
                        style={{
                          margin: 0,
                          fontSize: 11,
                          fontFamily: "ui-monospace, monospace",
                          whiteSpace: "pre-wrap",
                          wordBreak: "break-all",
                          maxWidth: 500,
                        }}
                      >
                        {typeof item.detail === "string"
                          ? item.detail
                          : JSON.stringify(item.detail, null, 2)}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── Approval confirmation dialog ── */}
      <ConfirmDialog
        open={!!approveDialog && approveDialog.decision !== "edit"}
        title={`${approveDialog?.label}?`}
        message={
          approveDialog?.decision === "approve"
            ? "You are about to approve this claim. This action will be recorded in the audit log."
            : "You are about to reject this claim. This action will be recorded in the audit log."
        }
        confirmLabel={approveDialog?.label ?? "Confirm"}
        confirmClass={
          approveDialog?.decision === "approve" ? "btn-success" : "btn-danger"
        }
        onConfirm={() => handleApprovalConfirm()}
        onCancel={() => setApproveDialog(null)}
        isLoading={approval.isPending}
      />

      <EditApproveDialog
        open={!!approveDialog && approveDialog.decision === "edit"}
        initialPayout={[...events].reverse().find(e => e.type === "payout")?.data?.payout}
        initialRationale={events.filter(e => e.type === "token").map(e => e.data.token ?? "").join("")}
        onConfirm={handleApprovalConfirm}
        onCancel={() => setApproveDialog(null)}
        isLoading={approval.isPending}
      />

      {/* ── Cancel confirmation dialog ── */}
      <ConfirmDialog
        open={cancelDialog}
        title="Cancel Adjudication Job?"
        message="This will stop the running AI pipeline. You can start a new adjudication afterwards."
        confirmLabel="Yes, cancel"
        confirmClass="btn-danger"
        onConfirm={handleCancelConfirm}
        onCancel={() => setCancelDialog(false)}
        isLoading={cancelMut.isPending}
      />
    </AppShell>
  );
}
