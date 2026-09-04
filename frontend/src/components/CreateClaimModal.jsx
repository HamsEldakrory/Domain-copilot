import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useCreateClaim, useClients, usePolicyVersions } from "../hooks/useClaims";

export default function CreateClaimModal({ onClose, onCreated }) {
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { claim_date: new Date().toISOString().slice(0, 10) },
  });

  const createClaim     = useCreateClaim();
  const { data: clients = [] }        = useClients();
  const { data: policyVersions = [] } = usePolicyVersions();

  // close on Escape
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const onSubmit = (data) => {
    const payload = {
      client_id:         data.client_id,
      policy_version_id: data.policy_version_id || null,
      claim_date:        data.claim_date,
    };
    createClaim.mutate(payload, {
      onSuccess: (claim) => {
        onCreated?.(claim);
        onClose();
      },
    });
  };

  const errorMsg =
    createClaim.error?.response?.data?.error ||
    (createClaim.isError ? "Failed to create claim." : null);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">New Claim</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          {/* Client */}
          <div className="form-group">
            <label className="form-label required" htmlFor="cc-client">Client</label>
            <select
              id="cc-client"
              className={`form-control${errors.client_id ? " is-error" : ""}`}
              {...register("client_id", { required: "Client is required" })}
            >
              <option value="">Select a client…</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            {errors.client_id && <div className="form-error">{errors.client_id.message}</div>}
          </div>

          {/* Policy version (optional) */}
          <div className="form-group">
            <label className="form-label" htmlFor="cc-policy">Policy Version <span className="text-muted">(optional)</span></label>
            <select
              id="cc-policy"
              className="form-control"
              {...register("policy_version_id")}
            >
              <option value="">None / select later</option>
              {policyVersions.map((pv) => (
                <option key={pv.id} value={pv.id}>{pv.label}</option>
              ))}
            </select>
          </div>

          {/* Claim date */}
          <div className="form-group">
            <label className="form-label required" htmlFor="cc-date">Claim Date</label>
            <input
              id="cc-date"
              type="date"
              className={`form-control${errors.claim_date ? " is-error" : ""}`}
              {...register("claim_date", { required: "Claim date is required" })}
            />
            {errors.claim_date && <div className="form-error">{errors.claim_date.message}</div>}
          </div>

          {errorMsg && <div className="alert alert-error mb-16">{errorMsg}</div>}

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={createClaim.isPending}
            >
              {createClaim.isPending ? <><span className="spinner" /> Creating…</> : "Create Claim"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
