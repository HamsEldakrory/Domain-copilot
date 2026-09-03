import { useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useUploadPolicy } from "../hooks/usePolicies";
import { useDocumentStatus } from "../hooks/useDocuments";
import { useCurrentUser } from "../hooks/useAuth";
import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";

const STEPS = ["pending", "processing", "extracting", "chunked", "ingested"];

function getStepIndex(status) {
  const i = STEPS.indexOf(status);
  return i === -1 ? 0 : i;
}

export default function PolicyUpload() {
  const { register, handleSubmit, formState: { errors }, reset } = useForm();
  const upload = useUploadPolicy();
  const [documentId, setDocumentId] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const user = useSelector((s) => s.auth.user);
  useCurrentUser(true);
  const navigate = useNavigate();

  const { data: docStatus } = useDocumentStatus(
    documentId,
    Boolean(documentId)
  );

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

    upload.mutate(formData, {
      onSuccess: (res) => {
        setDocumentId(res.document_id);
        setSuccessMsg(`Document uploaded. Tracking ID: ${res.document_id}`);
        reset();
      },
    });
  };

  const currentStatus = docStatus?.status ?? null;
  const isFailed   = currentStatus === "failed";
  const isIngested = currentStatus === "ingested";
  const stepIdx    = getStepIndex(currentStatus);

  return (
    <AppShell title="Upload Policy">
      <div className="page-header">
        <div>
          <div className="page-title">Upload Policy Document</div>
          <div className="page-subtitle">Manager-only · PDF or DOCX policy documents</div>
        </div>
      </div>

      <div style={{ maxWidth: 600 }}>
        <div className="card mb-16">
          <div className="card-header">
            <span className="card-title">Upload New Policy</span>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit(onSubmit)} encType="multipart/form-data">
              <div className="form-row mb-16">
                <div className="form-group mb-0">
                  <label className="form-label required">Policy Number</label>
                  <input
                    className={`form-control${errors.policyNumber ? " is-error" : ""}`}
                    placeholder="e.g. auto_comp"
                    {...register("policyNumber", { required: "Required" })}
                  />
                  {errors.policyNumber && (
                    <div className="form-error">{errors.policyNumber.message}</div>
                  )}
                </div>
                <div className="form-group mb-0">
                  <label className="form-label required">Version</label>
                  <input
                    className={`form-control${errors.version ? " is-error" : ""}`}
                    placeholder="e.g. v1.0"
                    {...register("version", { required: "Required" })}
                  />
                  {errors.version && (
                    <div className="form-error">{errors.version.message}</div>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label required">Effective From</label>
                <input
                  type="date"
                  className={`form-control${errors.effectiveFrom ? " is-error" : ""}`}
                  {...register("effectiveFrom", { required: "Required" })}
                />
                {errors.effectiveFrom && (
                  <div className="form-error">{errors.effectiveFrom.message}</div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label required">File (PDF or DOCX)</label>
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
              >
                {upload.isPending ? (
                  <><span className="spinner" /> Uploading…</>
                ) : (
                  "Upload Policy"
                )}
              </button>
            </form>
          </div>
        </div>

        {documentId && (
          <div className="card">
            <div className="card-header">
              <span className="card-title">Ingestion Status</span>
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
                  Ingestion failed. Please check the document and try again.
                </div>
              )}

              {isIngested && (
                <div className="alert alert-success">
                  ✓ Policy successfully ingested and ready for adjudication.
                </div>
              )}

              {!isIngested && !isFailed && currentStatus && (
                <div className="alert alert-info">
                  <span className="spinner" style={{ width: 14, height: 14, borderWidth: 1.5 }} />
                  &nbsp; Processing… Polling every 2 seconds.
                </div>
              )}

              <div className="detail-field-label mt-12">Document ID</div>
              <div className="detail-field-value font-mono text-xs">{documentId}</div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
