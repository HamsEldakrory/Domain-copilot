import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useSelector } from "react-redux";

import Login        from "./pages/Login";
import Dashboard    from "./pages/Dashboard";
import Claims       from "./pages/Claims";
import ClaimDetail  from "./pages/ClaimDetail";
import PolicyUpload from "./pages/PolicyUpload";
import Users        from "./pages/Users";
import Forbidden    from "./pages/Forbidden";

function RequireAuth({ children }) {
  const access = useSelector((state) => state.auth.access);
  if (!access) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

/** Smart root redirect: login page if unauthenticated, claims if logged in */
function RootRedirect() {
  const access = useSelector((state) => state.auth.access);
  return <Navigate to={access ? "/claims" : "/login"} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />
        <Route path="/forbidden" element={<Forbidden />} />

        {/* Protected */}
        <Route
          path="/dashboard"
          element={<RequireAuth><Dashboard /></RequireAuth>}
        />
        <Route
          path="/claims"
          element={<RequireAuth><Claims /></RequireAuth>}
        />
        <Route
          path="/claims/:claimId"
          element={<RequireAuth><ClaimDetail /></RequireAuth>}
        />
        <Route
          path="/policies/upload"
          element={<RequireAuth><PolicyUpload /></RequireAuth>}
        />
        <Route
          path="/users"
          element={<RequireAuth><Users /></RequireAuth>}
        />

        {/* Root + catch-all: smart redirect */}
        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<RootRedirect />} />
      </Routes>
    </BrowserRouter>
  );
}
