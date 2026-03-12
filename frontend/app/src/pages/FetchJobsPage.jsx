import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { apiRequest } from "../lib/api";
import { queryClient } from "../lib/queryClient";

export function FetchJobsPage() {
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const runsQuery = useQuery({
    queryKey: ["pipeline-runs"],
    queryFn: () => apiRequest("/api/pipeline-runs"),
    refetchInterval: (query) => {
      const rows = query.state.data || [];
      return rows.some((row) => row.status === "queued" || row.status === "running") ? 4000 : false;
    },
  });

  const portalMutation = useMutation({
    mutationFn: () => apiRequest("/api/portal/login", { method: "POST" }),
    onSuccess: (data) => {
      setError("");
      setStatus(data.message || "Naukri profile linked.");
    },
    onError: (err) => {
      setStatus("");
      setError(err.message || "Portal login failed.");
    },
  });

  const runMutation = useMutation({
    mutationFn: () => apiRequest("/api/fetch-jobs", { method: "POST" }),
    onSuccess: (data) => {
      setError("");
      setStatus(`Run #${data.run_id} queued.`);
      queryClient.invalidateQueries({ queryKey: ["pipeline-runs"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
    onError: (err) => {
      setStatus("");
      setError(err.message || "Pipeline run failed.");
    },
  });

  const clearMutation = useMutation({
    mutationFn: () => apiRequest("/api/pipeline-runs", { method: "DELETE" }),
    onSuccess: (data) => {
      setError("");
      setStatus(`Cleared ${data.deleted_count} pipeline runs.`);
      queryClient.invalidateQueries({ queryKey: ["pipeline-runs"] });
    },
    onError: (err) => {
      setStatus("");
      setError(err.message || "Clearing run history failed.");
    },
  });

  const latestRun = runsQuery.data?.[0];
  const showDirectoryLink = latestRun?.status === "completed";
  const isBusy = portalMutation.isPending || runMutation.isPending || clearMutation.isPending;
  const summary = latestRun
    ? `${latestRun.status} · fetched ${latestRun.fetched_count} · shortlisted ${latestRun.shortlisted_count}`
    : "No runs yet.";

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Automation</p>
          <h1>Fetch Jobs</h1>
          <p>Control panel settings drive the pipeline. This page only handles portal linking and execution.</p>
        </div>
      </header>

      <section className="action-strip">
        <button className="secondary-button" disabled={isBusy} onClick={() => portalMutation.mutate()} type="button">
          {portalMutation.isPending ? "Linking..." : "Link Naukri Profile"}
        </button>
        <button className="primary-button" disabled={isBusy} onClick={() => runMutation.mutate()} type="button">
          {runMutation.isPending ? "Running..." : "Run Pipeline"}
        </button>
        <button className="ghost-button" disabled={isBusy} onClick={() => clearMutation.mutate()} type="button">
          Clear History
        </button>
        {showDirectoryLink ? (
          <Link className="inline-chip" to="/jobs-directory">
            Go To Directory
          </Link>
        ) : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Run Status</p>
            <h2>Recent Runs</h2>
          </div>
          <span className="muted-text">{summary}</span>
        </div>
        {status ? <p className="form-success">{status}</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
        <DataTable
          columns={[
            { key: "started_at", label: "Date" },
            { key: "pages", label: "Pages" },
            { key: "auto_apply_limit", label: "Apply Limit" },
            { key: "fetched_count", label: "Fetched" },
            { key: "shortlisted_count", label: "Shortlisted" },
            { key: "message", label: "Message / Remark" },
          ]}
          rows={runsQuery.data || []}
        />
      </section>
    </section>
  );
}
