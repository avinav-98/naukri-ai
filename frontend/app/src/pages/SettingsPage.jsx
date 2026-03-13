import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { apiRequest } from "../lib/api";
import { queryClient } from "../lib/queryClient";

const defaultSettings = {
  job_role: "",
  preferred_location: "",
  experience: "",
  salary: "",
  keywords: "",
  scan_mode: "basic",
  pages_to_scrape: 5,
  auto_apply_limit: 10,
  max_job_age_days: 10,
};

export function SettingsPage() {
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: () => apiRequest("/api/settings"),
  });
  const uiQuery = useQuery({
    queryKey: ["ui-preferences"],
    queryFn: () => apiRequest("/api/ui-preferences"),
  });

  const [settingsState, setSettingsState] = useState(defaultSettings);
  const [uiState, setUiState] = useState({
    theme_mode: "system",
    layout_mode: "standard",
    accent_color: "#0b57d0",
  });
  const [settingsMessage, setSettingsMessage] = useState("");
  const [uiMessage, setUiMessage] = useState("");
  const [settingsError, setSettingsError] = useState("");
  const [uiError, setUiError] = useState("");

  useEffect(() => {
    if (settingsQuery.data) {
      setSettingsState((prev) => ({ ...prev, ...settingsQuery.data }));
    }
  }, [settingsQuery.data]);

  useEffect(() => {
    if (uiQuery.data) {
      setUiState((prev) => ({ ...prev, ...uiQuery.data }));
    }
  }, [uiQuery.data]);

  const saveSettingsMutation = useMutation({
    mutationFn: (formData) => apiRequest("/api/settings", { method: "POST", form: formData }),
    onSuccess: () => {
      setSettingsMessage("Settings saved.");
      setSettingsError("");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["key-skills"] });
      queryClient.invalidateQueries({ queryKey: ["resume-analyzer"] });
    },
    onError: (error) => {
      setSettingsError(error.message);
      setSettingsMessage("");
    },
  });

  const saveUiMutation = useMutation({
    mutationFn: (formData) => apiRequest("/api/ui-preferences", { method: "POST", form: formData }),
    onSuccess: () => {
      setUiMessage("UI preferences saved.");
      setUiError("");
      queryClient.invalidateQueries({ queryKey: ["ui-preferences"] });
      queryClient.invalidateQueries({ queryKey: ["session"] });
    },
    onError: (error) => {
      setUiError(error.message);
      setUiMessage("");
    },
  });

  function handleSettingsSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    saveSettingsMutation.mutate(formData);
  }

  function handleUiSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    saveUiMutation.mutate(formData);
  }

  function handleSettingsChange(event) {
    const { name, value } = event.target;
    setSettingsState((prev) => ({ ...prev, [name]: value }));
  }

  function handleUiChange(event) {
    const { name, value } = event.target;
    setUiState((prev) => ({ ...prev, [name]: value }));
  }

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Configuration</p>
          <h1>Settings</h1>
          <p>Control panel values remain the single source of truth for scanning and automation.</p>
        </div>
      </header>

      <div className="split-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Control Panel</p>
              <h2>Job Fetch Settings</h2>
            </div>
          </div>
          <form className="stack-form" onSubmit={handleSettingsSubmit}>
            <label>
              Job Role
              <input name="job_role" onChange={handleSettingsChange} value={settingsState.job_role || ""} />
            </label>
            <label>
              Preferred Location
              <input
                name="preferred_location"
                onChange={handleSettingsChange}
                value={settingsState.preferred_location || ""}
              />
            </label>
            <label>
              Total Experience
              <input name="experience" onChange={handleSettingsChange} value={settingsState.experience || ""} />
            </label>
            <label>
              Salary Expectation
              <input name="salary" onChange={handleSettingsChange} value={settingsState.salary || ""} />
            </label>
            <label>
              Key-Skills
              <textarea name="keywords" onChange={handleSettingsChange} rows="4" value={settingsState.keywords || ""} />
            </label>
            <label>
              Scan Mode
              <select name="scan_mode" onChange={handleSettingsChange} value={settingsState.scan_mode || "basic"}>
                <option value="basic">Basic</option>
                <option value="advance">Advance</option>
                <option value="extreme">Extreme</option>
              </select>
            </label>
            <label>
              Scrap Pages
              <input name="pages_to_scrape" min="1" onChange={handleSettingsChange} type="number" value={settingsState.pages_to_scrape || 5} />
            </label>
            <label>
              Auto Apply Limit
              <input
                name="auto_apply_limit"
                min="1"
                onChange={handleSettingsChange}
                type="number"
                value={settingsState.auto_apply_limit || 10}
              />
            </label>
            <label>
              Max Job Age Days
              <input
                name="max_job_age_days"
                min="1"
                onChange={handleSettingsChange}
                type="number"
                value={settingsState.max_job_age_days || 10}
              />
            </label>
            <label>
              Resume.txt
              <input accept=".txt" name="resume_file" type="file" />
            </label>
            {settingsQuery.data?.has_resume ? <p className="muted-text">A resume is already stored for this account.</p> : null}
            {settingsMessage ? <p className="form-success">{settingsMessage}</p> : null}
            {settingsError ? <p className="form-error">{settingsError}</p> : null}
            <button className="primary-button" disabled={saveSettingsMutation.isPending} type="submit">
              {saveSettingsMutation.isPending ? "Saving..." : "Save Settings"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">User Interface</p>
              <h2>UI Preferences</h2>
            </div>
          </div>
          <form className="stack-form" onSubmit={handleUiSubmit}>
            <label>
              Theme Mode
              <select name="theme_mode" onChange={handleUiChange} value={uiState.theme_mode}>
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </label>
            <label>
              Layout Mode
              <select name="layout_mode" onChange={handleUiChange} value={uiState.layout_mode}>
                <option value="compact">Compact</option>
                <option value="standard">Standard</option>
                <option value="wide">Wide</option>
              </select>
            </label>
            <label>
              Accent Color
              <input name="accent_color" onChange={handleUiChange} type="color" value={uiState.accent_color} />
            </label>
            {uiMessage ? <p className="form-success">{uiMessage}</p> : null}
            {uiError ? <p className="form-error">{uiError}</p> : null}
            <button className="secondary-button" disabled={saveUiMutation.isPending} type="submit">
              {saveUiMutation.isPending ? "Saving..." : "Save UI Preferences"}
            </button>
          </form>
        </section>
      </div>
    </section>
  );
}
