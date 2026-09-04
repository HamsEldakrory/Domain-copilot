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

      <div style={{ maxWidth: 540, margin: "20px auto 40px auto", padding: "0 16px" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6, color: "var(--text-primary)" }}>
          Create Adjuster Account
        </h2>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 20 }}>
          Create a new adjuster login. They will be able to access assigned claims immediately.
        </p>

        {successMsg && (
          <div className="alert alert-success mb-20">{successMsg}</div>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="form-group mb-16">
            <label className="form-label required">Username</label>
            <input
              className={`form-control${errors.username ? " is-error" : ""}`}
              placeholder="e.g. john_adjuster"
              autoComplete="off"
              {...register("username", {
                required: "Username is required",
                minLength: { value: 3, message: "Username must be at least 3 characters" },
                maxLength: { value: 30, message: "Username must be at most 30 characters" },
                pattern: {
                  value: /^[a-zA-Z0-9_]+$/,
                  message: "Only letters, numbers, and underscores allowed",
                },
              })}
            />
            {errors.username && (
              <div className="form-error">{errors.username.message}</div>
            )}
          </div>

          <div className="form-group mb-16">
            <label className="form-label required">Email Address</label>
            <input
              type="email"
              className={`form-control${errors.email ? " is-error" : ""}`}
              placeholder="e.g. john@example.com"
              {...register("email", {
                required: "Email address is required",
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: "Please enter a valid email address",
                },
              })}
            />
            {errors.email && (
              <div className="form-error">{errors.email.message}</div>
            )}
          </div>

          <div className="form-group mb-20">
            <label className="form-label required">Password</label>
            <input
              type="password"
              className={`form-control${errors.password ? " is-error" : ""}`}
              placeholder="Minimum 8 characters"
              {...register("password", {
                required: "Password is required",
                minLength: { value: 8, message: "Password must be at least 8 characters" },
                maxLength: { value: 100, message: "Password must be at most 100 characters" },
              })}
            />
            {errors.password && (
              <div className="form-error">{errors.password.message}</div>
            )}
          </div>

          {apiError && (
            <div className="alert alert-error mb-20">{apiError}</div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={createAdjuster.isPending}
            style={{ width: "100%", justifyContent: "center", padding: "10px 16px" }}
          >
            {createAdjuster.isPending ? (
              <><span className="spinner" /> Creating Adjuster Account…</>
            ) : (
              "➕ Create Adjuster Account"
            )}
          </button>
        </form>
      </div>
    </AppShell>
  );
}
