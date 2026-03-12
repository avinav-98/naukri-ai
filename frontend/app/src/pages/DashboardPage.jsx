import { useQuery } from "@tanstack/react-query";

import { DataTable } from "../components/DataTable";
import { apiRequest } from "../lib/api";

export function DashboardPage() {
  const statsQuery = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => apiRequest("/api/dashboard-stats"),
  });
  const runsQuery = useQuery({
    queryKey: ["pipeline-runs"],
    queryFn: () => apiRequest("/api/pipeline-runs"),
    refetchInterval: (query) => {
      const items = query.state.data || [];
      return items.some((item) => item.status === "queued" || item.status === "running") ? 4000 : false;
    },
  });

  const stats = statsQuery.data || { scraped: 0, relevant: 0, applied: 0 };

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Dashboard</h1>
          <p>Operational summary for scraping, ranking, and application activity.</p>
        </div>
      </header>

      <div className="stat-grid">
        <article className="stat-card">
          <span>Scraped</span>
          <strong>{stats.scraped}</strong>
        </article>
        <article className="stat-card">
          <span>Relevant</span>
          <strong>{stats.relevant}</strong>
        </article>
        <article className="stat-card">
          <span>Applied</span>
          <strong>{stats.applied}</strong>
        </article>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Activity</p>
            <h2>Recent Pipeline Runs</h2>
          </div>
        </div>
        <DataTable
          columns={[
            { key: "started_at", label: "Started At" },
            { key: "status", label: "Status" },
            { key: "pages", label: "Pages" },
            { key: "auto_apply_limit", label: "Apply Limit" },
            { key: "fetched_count", label: "Fetched" },
            { key: "shortlisted_count", label: "Shortlisted" },
            { key: "applied_count", label: "Applied" },
            { key: "message", label: "Message" },
          ]}
          rows={runsQuery.data || []}
        />
      </section>
    </section>
  );
}
