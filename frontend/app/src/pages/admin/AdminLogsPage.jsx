import { useQuery } from "@tanstack/react-query";

import { DataTable } from "../../components/DataTable";
import { apiRequest } from "../../lib/api";

export function AdminLogsPage() {
  const logsQuery = useQuery({
    queryKey: ["admin-logs"],
    queryFn: () => apiRequest("/api/admin/logs"),
  });

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Logs</h1>
          <p>Audit trail for login events, pipeline runs, and administrative actions.</p>
        </div>
      </header>

      <section className="panel">
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "user_id", label: "User ID" },
            { key: "event_type", label: "Event" },
            { key: "details", label: "Details" },
            { key: "level", label: "Level" },
            { key: "created_at", label: "Created At" },
          ]}
          rows={logsQuery.data || []}
        />
      </section>
    </section>
  );
}
