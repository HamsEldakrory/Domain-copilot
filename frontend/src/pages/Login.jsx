import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { useLogin, useCurrentUser } from "../hooks/useAuth";

export default function Login() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const login = useLogin();
  const navigate = useNavigate();
  const access = useSelector((state) => state.auth.access);

  // If already logged in redirect immediately
  useEffect(() => {
    if (access) navigate("/dashboard", { replace: true });
  }, [access, navigate]);

  const onSubmit = (data) => {
    login.mutate(data, {
      onSuccess: () => {
        navigate("/dashboard", { replace: true });
      },
    });
  };

  const errorMsg =
    login.error?.response?.data?.detail ||
    login.error?.response?.data?.error ||
    (login.isError ? "Invalid username or password." : null);

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">⚖️</div>
          <div className="login-logo-title">Domain Copilot</div>
          <div className="login-logo-sub">Insurance Claims Adjudication</div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="form-group">
            <label className="form-label required" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              className={`form-control${errors.username ? " is-error" : ""}`}
              placeholder="Enter your username"
              autoComplete="username"
              {...register("username", { required: "Username is required" })}
            />
            {errors.username && (
              <div className="form-error">{errors.username.message}</div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label required" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className={`form-control${errors.password ? " is-error" : ""}`}
              placeholder="Enter your password"
              autoComplete="current-password"
              {...register("password", { required: "Password is required" })}
            />
            {errors.password && (
              <div className="form-error">{errors.password.message}</div>
            )}
          </div>

          {errorMsg && (
            <div className="alert alert-error mb-16">{errorMsg}</div>
          )}

          <button
            type="submit"
            className="btn btn-primary w-full btn-lg"
            disabled={login.isPending}
          >
            {login.isPending ? (
              <>
                <span className="spinner" /> Signing in…
              </>
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        <div
          style={{
            marginTop: 24,
            padding: "12px 14px",
            background: "#f8fafc",
            borderRadius: 6,
            fontSize: 12,
            color: "#64748b",
            lineHeight: 1.7,
          }}
        >
          <strong>Demo credentials:</strong>
          <br />
          Manager: <code>demo_manager</code> / <code>DemoPass123!</code>
          <br />
          Adjuster: <code>demo_adjuster</code> / <code>DemoPass123!</code>
        </div>
      </div>
    </div>
  );
}
