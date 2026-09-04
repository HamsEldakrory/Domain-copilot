import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useUploadPolicy } from "../hooks/usePolicies";
import { useDocumentStatus, useDocuments } from "../hooks/useDocuments";
import { useCurrentUser } from "../hooks/useAuth";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";

const STEPS = ["pending", "processing", "extracting", "chunked", "ingested"];
const ITEMS_PER_PAGE = 5;

function getStepIndex(status) {
  const i = STEPS.indexOf(status);
  return i === -1 ? 0 : i;
}

export default function PolicyUpload() {
  const { register, handleSubmit, formState: { errors }, reset } = useForm();
  const upload = useUploadPolicy();
  const [documentId, setDocumentId] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");

  const user = useSelector((s) => s.auth.user);
  useCurrentUser(true);
  const navigate = useNavigate();

  const { data: docStatus } = useDocumentStatus(
    documentId,
    Boolean(documentId)
  );
  const { data: documents, isLoading: docsLoading } = useDocuments();

  if (user && user.role !== "MANAGER") {
    navigate("/forbidden", { replace: true });
    return null;
  }

  const onSubmit = (data) => {
    const formData = new FormData();
    formData.append("file", data.file[0]);
    formData.append("policy_number", data.policyNumber);
    formData.append("version", data.version);
    formData.append("effective_from", data.effectiveFrom);
    if (data.policyLimit) formData.append("policy_limit", data.policyLimit);
    if (data.deductible) formData.append("deductible", data.deductible);

    upload.mutate(formData, {
      onSuccess: (res) => {
        setDocumentId(res.document_id);
        setSuccessMsg(`Document uploaded successfully. Tracking ID: ${res.document_id}`);
        reset();
      },
    });
  };

  const currentStatus = docStatus?.status ?? null;
  const isFailed   = currentStatus === "failed";
  const isIngested = currentStatus === "ingested";
  const stepIdx    = getStepIndex(currentStatus);

  // Filter documents by search query
  const filteredDocs = documents?.filter((doc) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      doc.filename?.toLowerCase().includes(q) ||
      doc.policy_number?.toLowerCase().includes(q) ||
      doc.policy_version?.toLowerCase().includes(q) ||
      doc.status?.toLowerCase().includes(q)
    );
  }) ?? [];

  const totalDocuments = filteredDocs.length;
  const totalPages = Math.max(1, Math.ceil(totalDocuments / ITEMS_PER_PAGE));
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedDocs = filteredDocs.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(1);
    }
  }, [totalDocuments, totalPages, currentPage]);

  return (
    <AppShell title="Upload Policy">
      <div className="page-header">
        <div>
          <div className="page-title">Policy Upload & Document Management</div>
          <div className="page-subtitle">Manager-only · Upload, track, and ingest policy documents</div>
        </div>
      </div>

      {/* ── Top Grid: Upload Form & Real-time Status Tracker ── */}
      <div style={{ display: "grid", gridTemplateColumns: documentId ? "1fr 1fr" : "1fr", gap: 24, marginBottom: 24 }}>
        {/* Upload Form Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">📄 Upload New Policy Document</span>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit(onSubmit)} encType="multipart/form-data">
              <div className="form-row mb-16">
                <div className="form-group mb-0">
                  <label className="form-label required">Policy Number / Code</label>
                  <input
                    className={`form-control${errors.policyNumber ? " is-error" : ""}`}
                    placeholder="e.g. auto_comp"
                    {...register("policyNumber", {
                      required: "Policy number is required",
                      minLength: { value: 2, message: "Must be at least 2 characters" },
                    })}
                  />
                  {errors.policyNumber && (
                    <div className="form-error">{errors.policyNumber.message}</div>
                  )}
                </div>
                <div className="form-group mb-0">
                  <label className="form-label required">Policy Version</label>
                  <input
                    className={`form-control${errors.version ? " is-error" : ""}`}
                    placeholder="e.g. 2024-01"
                    {...register("version", {
                      required: "Policy version is required",
                    })}
                  />
                  {errors.version && (
                    <div className="form-error">{errors.version.message}</div>
                  )}
                </div>
              </div>

              <div className="form-row mb-16">
                <div className="form-group mb-0">
                  <label className="form-label">Policy Limit ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    className={`form-control${errors.policyLimit ? " is-error" : ""}`}
                    placeholder="e.g. 50000"
                    {...register("policyLimit", {
                      min: { value: 0, message: "Policy limit cannot be negative" },
                    })}
                  />
                  {errors.policyLimit && (
                    <div className="form-error">{errors.policyLimit.message}</div>
                  )}
                </div>
                <div className="form-group mb-0">
                  <label className="form-label">Deductible ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    className={`form-control${errors.deductible ? " is-error" : ""}`}
                    placeholder="e.g. 1000"
                    {...register("deductible", {
                      min: { value: 0, message: "Deductible cannot be negative" },
                    })}
                  />
                  {errors.deductible && (
                    <div className="form-error">{errors.deductible.message}</div>
                  )}
                </div>
              </div>

              <div className="form-group mb-16">
                <label className="form-label required">Effective From</label>
                <input
                  type="date"
                  className={`form-control${errors.effectiveFrom ? " is-error" : ""}`}
                  {...register("effectiveFrom", { required: "Effective date is required" })}
                />
                {errors.effectiveFrom && (
                  <div className="form-error">{errors.effectiveFrom.message}</div>
                )}
              </div>

              <div className="form-group mb-20">
                <label className="form-label required">Policy File (.pdf or .docx)</label>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  className={`form-control${errors.file ? " is-error" : ""}`}
                  {...register("file", {
                    required: "A file is required",
                    validate: (files) => {
                      const f = files?.[0];
                      if (!f) return "Required";
                      if (!f.name.match(/\.(pdf|docx)$/i)) {
                        return "Only PDF or DOCX files allowed";
                      }
                      return true;
                    },
                  })}
                />
                {errors.file && (
                  <div className="form-error">{errors.file.message}</div>
                )}
              </div>

              {upload.isError && (
                <div className="alert alert-error mb-16">
                  {upload.error?.response?.data?.error ??
                    upload.error?.response?.data?.detail ??
                    "Upload failed. Check your inputs."}
                </div>
              )}

              <button
                type="submit"
                className="btn btn-primary"
                disabled={upload.isPending}
                style={{ width: "100%", justifyContent: "center" }}
              >
                {upload.isPending ? (
                  <><span className="spinner" /> Uploading & Initiating Ingestion…</>
                ) : (
                  "⬆ Upload & Ingest Policy"
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Real-time Ingestion Tracking Card */}
        {documentId && (
          <div className="card" style={{ height: "fit-content" }}>
            <div className="card-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span className="card-title">⚡ Ingestion Pipeline Tracker</span>
              {currentStatus && <StatusBadge status={currentStatus} />}
            </div>
            <div className="card-body">
              {successMsg && (
                <div className="alert alert-success mb-16">{successMsg}</div>
              )}

              {currentStatus && !isFailed && (
                <div className="progress-steps mb-16">
                  {STEPS.map((step, i) => {
                    const isDone   = i < stepIdx || isIngested;
                    const isActive = i === stepIdx && !isIngested;
                    return (
                      <div
                        key={step}
                        className={`progress-step${isDone ? " done" : ""}${isActive ? " active" : ""}`}
                      >
                        <div className="progress-step-dot">
                          {isDone ? "✓" : i + 1}
                        </div>
                        <div className="progress-step-label">{step}</div>
                      </div>
                    );
                  })}
                </div>
              )}

              {isFailed && (
                <div className="alert alert-error">
                  Ingestion failed. Please check the document format and try again.
                </div>
              )}

              {isIngested && (
                <div className="alert alert-success">
                  ✓ Policy successfully ingested into vector store and ready for adjudication.
                </div>
              )}

              {!isIngested && !isFailed && currentStatus && (
                <div className="alert alert-info" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span className="spinner" style={{ width: 14, height: 14, borderWidth: 1.5 }} />
                  Processing pipeline steps… Polling every 2 seconds.
                </div>
              )}

              <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
                <div className="detail-field-label">Document Tracking ID</div>
                <div className="detail-field-value font-mono text-xs text-muted" style={{ wordBreak: "break-all" }}>
                  {documentId}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Bottom Section: Uploaded Policy Documents Table with Pagination ── */}
      <div className="card">
        <div className="card-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <span className="card-title">📚 Uploaded Policy Documents ({totalDocuments})</span>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input
              className="form-control form-control-sm"
              placeholder="🔍 Search policies or status…"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: 220, fontSize: 13 }}
            />
          </div>
        </div>

        <div className="table-container" style={{ border: "none", borderRadius: 0, boxShadow: "none" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Policy Number</th>
                <th>Version</th>
                <th>Limit / Deductible</th>
                <th>Vector Chunks</th>
                <th>Status</th>
                <th>Uploaded At</th>
              </tr>
            </thead>
            <tbody>
              {docsLoading && (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: 30 }}>
                    <span className="spinner" /> Loading policy documents…
                  </td>
                </tr>
              )}
              {!docsLoading && paginatedDocs.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: 30 }}>
                    <div className="empty-state">
                      <div className="empty-state-icon">📂</div>
                      <div className="empty-state-title">No policy documents found</div>
                      <div className="empty-state-sub">
                        {searchQuery ? "No policies match your search query." : "Upload a policy document above to get started."}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
              {paginatedDocs.map((doc) => (
                <tr key={doc.id}>
                  <td className="font-semibold">{doc.filename}</td>
                  <td className="font-mono text-sm">{doc.policy_number || "—"}</td>
                  <td>
                    <span className="badge badge-neutral">{doc.policy_version || "—"}</span>
                  </td>
                  <td className="text-sm font-mono">
                    {doc.policy_limit != null ? `$${Number(doc.policy_limit).toLocaleString()}` : "—"} / {doc.deductible != null ? `$${Number(doc.deductible).toLocaleString()}` : "—"}
                  </td>
                  <td>
                    <span className="badge badge-primary font-mono text-xs" style={{ background: "rgba(99,102,241,0.15)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.3)" }}>
                      🧩 {doc.chunk_count ?? 0} chunks
                    </span>
                  </td>
                  <td>
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="text-muted text-xs">
                    {doc.created_at ? new Date(doc.created_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {totalDocuments > 0 && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 20px",
              borderTop: "1px solid var(--border)",
              background: "rgba(255,255,255,0.02)",
              flexWrap: "wrap",
              gap: 12,
            }}
          >
            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
              Showing <strong style={{ color: "var(--text-primary)" }}>{startIndex + 1}</strong> to{" "}
              <strong style={{ color: "var(--text-primary)" }}>{Math.min(startIndex + ITEMS_PER_PAGE, totalDocuments)}</strong> of{" "}
              <strong style={{ color: "var(--text-primary)" }}>{totalDocuments}</strong> documents
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                ← Previous
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pg) => (
                <button
                  key={pg}
                  className={`btn btn-sm ${currentPage === pg ? "btn-primary" : "btn-ghost"}`}
                  onClick={() => setCurrentPage(pg)}
                  style={{ minWidth: 32, padding: "4px 8px" }}
                >
                  {pg}
                </button>
              ))}

              <button
                className="btn btn-outline btn-sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages || totalPages === 0}
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
