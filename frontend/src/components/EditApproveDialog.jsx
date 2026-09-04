import { useState, useEffect } from "react";

export default function EditApproveDialog({
  open,
  initialPayout,
  initialRationale,
  onConfirm,
  onCancel,
  isLoading = false,
}) {
  const [payout, setPayout] = useState(initialPayout || "");
  const [rationale, setRationale] = useState(initialRationale || "");

  useEffect(() => {
    if (open) {
      setPayout(initialPayout || "");
      setRationale(initialRationale || "");
    }
  }, [open, initialPayout, initialRationale]);

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()} style={{ minWidth: 500 }}>
        <div className="modal-title">Edit & Approve Claim</div>
        <div className="modal-body">
          <p style={{ marginBottom: 16, fontSize: 13, color: "var(--text-secondary)" }}>
            You are about to manually override the AI's recommended payout and rationale before approving the claim.
          </p>
          
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: 12, fontWeight: 600 }}>Final Payout Amount ($)</label>
            <input
              type="number"
              className="form-control"
              value={payout}
              onChange={(e) => setPayout(e.target.value)}
              placeholder="e.g. 25000.00"
              style={{ width: "100%" }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: 12, fontWeight: 600 }}>Approval Rationale</label>
            <textarea
              className="form-control"
              rows={6}
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              style={{ width: "100%", resize: "vertical" }}
            />
          </div>
        </div>
        <div className="modal-actions">
          <button
            className="btn btn-outline btn-sm"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            className="btn btn-success btn-sm"
            onClick={() => onConfirm(Number(payout), rationale)}
            disabled={isLoading}
          >
            {isLoading ? <span className="spinner" /> : "Approve with Edits"}
          </button>
        </div>
      </div>
    </div>
  );
}
