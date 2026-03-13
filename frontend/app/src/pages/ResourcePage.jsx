import { useMutation, useQuery } from "@tanstack/react-query";

import { DataTable } from "../components/DataTable";
import { apiRequest } from "../lib/api";
import { queryClient } from "../lib/queryClient";

export function ResourcePage({ title, description, queryKey, endpoint, columns, transform, actions }) {
  const query = useQuery({
    queryKey,
    queryFn: () => apiRequest(endpoint),
  });

  const resetMutation = useMutation({
    mutationFn: () => {
      if (endpoint === "/api/key-skills") {
        return apiRequest(endpoint, { method: "DELETE" });
      }
      return Promise.resolve(null);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });

  const rows = transform ? transform(query.data) : query.data || [];
  const showReset = endpoint === "/api/key-skills";

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Data View</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <div className="panel-actions">
          {actions?.map((action) => (
            <a key={action.href} className="secondary-button inline-button" href={action.href}>
              {action.label}
            </a>
          ))}
          {showReset ? (
            <button className="ghost-button" onClick={() => resetMutation.mutate()} type="button">
              Reset
            </button>
          ) : null}
        </div>
      </header>

      <section className="panel">
        <DataTable columns={columns} rows={rows} />
      </section>
    </section>
  );
}
