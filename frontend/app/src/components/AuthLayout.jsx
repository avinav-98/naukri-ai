import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";

export function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="screen-center">Loading session...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <Outlet />
      </div>
      <aside className="auth-aside">
        <p className="eyebrow">React + Vite Migration</p>
        <h1>Naukri Auto Apply AI</h1>
        <p>
          FastAPI continues to own the API surface. This frontend handles routing, auth state, and
          data fetching through React Router and TanStack Query.
        </p>
      </aside>
    </div>
  );
}
