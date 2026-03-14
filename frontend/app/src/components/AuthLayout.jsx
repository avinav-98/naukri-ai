import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";

export function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="screen-center">Loading session...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  if (location.pathname === "/signin" || location.pathname === "/") {
    return (
      <div className="public-shell">
        <Outlet />
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel auth-panel-compact">
        <Outlet />
      </div>
    </div>
  );
}
