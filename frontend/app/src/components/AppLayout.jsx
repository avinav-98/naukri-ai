import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";

const primaryLinks = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/fetch-jobs", label: "Fetch Jobs" },
  { to: "/jobs-directory", label: "Job Directory" },
  { to: "/relevant-jobs", label: "Relevant Jobs" },
  { to: "/applied-jobs", label: "Applied Jobs" },
  { to: "/ext-jobs", label: "External Jobs" },
  { to: "/resume-analyzer", label: "Resume Analyzer" },
  { to: "/keywords", label: "Key-Skills" },
  { to: "/settings", label: "Settings" },
  { to: "/profile", label: "Profile" },
];

const adminLinks = [
  { to: "/admin", label: "Admin Overview" },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/settings", label: "System Settings", adminOnly: true },
  { to: "/admin/logs", label: "Logs" },
];

export function AppLayout() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  async function handleLogout() {
    await logout();
    navigate("/signin", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">Control Center</p>
          <h2>Naukri AI</h2>
          <p>{user?.email}</p>
        </div>

        <nav className="sidebar-nav">
          {primaryLinks.map((link) => (
            <NavItem key={link.to} link={link} />
          ))}
        </nav>

        {["admin", "co_admin"].includes(user?.role) ? (
          <nav className="sidebar-nav admin-nav">
            <p className="nav-heading">Admin</p>
            {adminLinks
              .filter((link) => !link.adminOnly || user?.role === "admin")
              .map((link) => (
                <NavItem key={link.to} link={link} />
              ))}
          </nav>
        ) : null}

        <button className="secondary-button" type="button" onClick={handleLogout}>
          Sign Out
        </button>
      </aside>

      <main className="content-shell">
        <Outlet />
      </main>
    </div>
  );
}

function NavItem({ link }) {
  return (
    <NavLink
      className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
      to={link.to}
    >
      {link.label}
    </NavLink>
  );
}
