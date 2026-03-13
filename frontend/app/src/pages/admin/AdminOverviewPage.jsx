import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "../../lib/api";

export function AdminOverviewPage() {
  const overviewQuery = useQuery({
    queryKey: ["admin-overview"],
    queryFn: () => apiRequest("/api/admin/overview"),
  });
  const data = overviewQuery.data || {};

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>System Overview</h1>
          <p>Role-gated operational counts across users, jobs, and pipeline activity.</p>
        </div>
      </header>

      <div className="stat-grid">
        {Object.entries(data).map(([key, value]) => (
          <article className="stat-card" key={key}>
            <span>{key.replaceAll("_", " ")}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}
