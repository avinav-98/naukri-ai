import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { apiRequest } from "../../lib/api";
import { queryClient } from "../../lib/queryClient";

export function AdminSettingsPage() {
  const [formState, setFormState] = useState({ setting_key: "", setting_value: "" });
  const [message, setMessage] = useState("");
  const settingsQuery = useQuery({
    queryKey: ["admin-settings"],
    queryFn: () => apiRequest("/api/admin/settings"),
  });
  const saveMutation = useMutation({
    mutationFn: (form) => apiRequest("/api/admin/settings", { method: "POST", form }),
    onSuccess: () => {
      setMessage("System setting saved.");
      queryClient.invalidateQueries({ queryKey: ["admin-settings"] });
    },
  });

  function handleSubmit(event) {
    event.preventDefault();
    saveMutation.mutate(formState);
  }

  const entries = Object.entries(settingsQuery.data || {});

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>System Settings</h1>
          <p>Direct access to global admin settings stored in the backend.</p>
        </div>
      </header>

      <div className="split-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Stored Values</p>
              <h2>Current Settings</h2>
            </div>
          </div>
          <dl className="detail-list">
            {entries.length ? (
              entries.map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd>{String(value)}</dd>
                </div>
              ))
            ) : (
              <div>
                <dt>Status</dt>
                <dd>No settings saved yet.</dd>
              </div>
            )}
          </dl>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Update</p>
              <h2>Save Setting</h2>
            </div>
          </div>
          <form className="stack-form" onSubmit={handleSubmit}>
            <label>
              Setting Key
              <input
                name="setting_key"
                onChange={(event) => setFormState((prev) => ({ ...prev, setting_key: event.target.value }))}
                value={formState.setting_key}
              />
            </label>
            <label>
              Setting Value
              <textarea
                name="setting_value"
                onChange={(event) => setFormState((prev) => ({ ...prev, setting_value: event.target.value }))}
                rows="5"
                value={formState.setting_value}
              />
            </label>
            {message ? <p className="form-success">{message}</p> : null}
            <button className="primary-button" disabled={saveMutation.isPending} type="submit">
              {saveMutation.isPending ? "Saving..." : "Save"}
            </button>
          </form>
        </section>
      </div>
    </section>
  );
}
