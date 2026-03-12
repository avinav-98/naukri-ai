import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../auth/AuthProvider";
import { apiRequest } from "../lib/api";

export function ProfilePage() {
  const { user } = useAuth();
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: () => apiRequest("/api/settings"),
  });

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">User</p>
          <h1>Profile</h1>
          <p>Session identity and saved control panel summary.</p>
        </div>
      </header>

      <div className="split-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Identity</p>
              <h2>Account</h2>
            </div>
          </div>
          <dl className="detail-list">
            <div>
              <dt>Name</dt>
              <dd>{user?.full_name || "-"}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user?.email || "-"}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{user?.role || "-"}</dd>
            </div>
            <div>
              <dt>Naukri ID</dt>
              <dd>{user?.naukri_id || "-"}</dd>
            </div>
            <div>
              <dt>Last Login</dt>
              <dd>{user?.last_login || "-"}</dd>
            </div>
          </dl>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Saved Filters</p>
              <h2>Current Settings</h2>
            </div>
          </div>
          <dl className="detail-list">
            {Object.entries(settingsQuery.data || {}).map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll("_", " ")}</dt>
                <dd>{String(value || "-")}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </section>
  );
}
