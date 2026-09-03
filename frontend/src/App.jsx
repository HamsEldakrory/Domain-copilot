import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useSelector } from "react-redux";
import Login from "./pages/Login";
import Claims from "./pages/Claims";
import ClaimDetail from "./pages/ClaimDetail";

function RequireAuth({ children }) {
  const access = useSelector(
    (state) => state.auth.access
  );
  if (!access) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );

  }
  return children;
}
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/claims"
          element={
            <RequireAuth>
              <Claims />
            </RequireAuth>
          }
        />

        <Route
          path="/claims/:claimId"
          element={
            <RequireAuth>
              <ClaimDetail />
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
