import { useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useCreateAdjuster } from "../hooks/useUsers";
import { useCurrentUser } from "../hooks/useAuth";
import AppShell from "../components/AppShell";

export default function Users() {
  const { register, handleSubmit, formState: { errors }, reset } = useForm();
  const createAdjuster = useCreateAdjuster();
  const [successMsg, setSuccessMsg] = useState(null);
  const user = useSelector((s) => s.auth.user);
  useCurrentUser(true);
  const navigate = useNavigate();

  if (user && user.role !== "MANAGER") {
    navigate("/forbidden", { replace: true });
    return null;
  }

  const onSubmit = (data) => {
    createAdjuster.mutate(data, {
      onSuccess: (res) => {
        setSuccessMsg(
          `Adjuster account created: ${res.username ?? data.username}`
        );
        reset();
      },
    });
  };

  const apiError =
    createAdjuster.error?.response?.data?.username?.[0] ||
    createAdjuster.error?.response?.data?.error ||
    createAdjuster.error?.response?.data?.detail ||
    (createAdjuster.isError ? "Failed to create account." : null);

  return (
    <AppShell title="Users">
      <div className="page-header">
        <div>
          <div className="page-title">User Management</div>
          <div className="page-subtitle">Manager-only · Create adjuster accounts</div>
        </div>
      </div>

      <div style={{ maxWidth: 500 }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Create Adjuster Account</span>
          </div>
          <div className="card-body">
            {successMsg && (
              <div className="alert alert-success mb-16">{successMsg}</div>
            )}

            <form onSubmit={handleSubmit(onSubmit)}>
              <div className="form-group">
                <label className="form-label required">Username</label>
                <input
                  className={`form-control${errors.username ? " is-error" : ""}`}
                  placeholder="e.g. john_adjuster"
                  autoComplete="off"
                  {...register("username", {
                    required: "Username is required",
                    minLength: { value: 3, message: "At least 3 characters" },
                    pattern: {
                      value: /^[a-zA-Z0-9_]+$/,
                      message: "Letters, digits and underscores only",
                    },
                  })}
                />
                {errors.username && (
                  <div className="form-error">{errors.username.message}</div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label required">Email</label>
                <input
                  type="email"
                  className={`form-control${errors.email ? " is-error" : ""}`}
                  placeholder="e.g. john@example.com"
                  {...register("email", {
                    required: "Email is required",
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: "Enter a valid email address",
                    },
                  })}
                />
                {errors.email && (
                  <div className="form-error">{errors.email.message}</div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label required">Password</label>
                <input
                  type="password"
                  className={`form-control${errors.password ? " is-error" : ""}`}
                  placeholder="Minimum 8 characters"
                  {...register("password", {
                    required: "Password is required",
                    minLength: { value: 8, message: "At least 8 characters" },
                  })}
                />
                {errors.password && (
                  <div className="form-error">{errors.password.message}</div>
                )}
              </div>

              {apiError && (
                <div className="alert alert-error mb-16">{apiError}</div>
              )}

              <button
                type="submit"
                className="btn btn-primary"
                disabled={createAdjuster.isPending}
              >
                {createAdjuster.isPending ? (
                  <><span className="spinner" /> Creating…</>
                ) : (
                  "Create Adjuster"
                )}
              </button>
            </form>
          </div>
          <div className="card-footer">
            <p className="text-muted text-sm">
              The new adjuster will be able to log in immediately and see only
              claims assigned to them.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
