import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { DataTable } from "../../components/DataTable";
import { apiRequest } from "../../lib/api";
import { queryClient } from "../../lib/queryClient";

const defaultProfileForm = {
  full_name: "",
  email: "",
  naukri_id: "",
  naukri_password: "",
};

const defaultSettingsForm = {
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

const defaultAccessForm = {
  role: "user",
  account_status: "active",
  new_password: "",
};

export function AdminUsersPage() {
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [profileForm, setProfileForm] = useState(defaultProfileForm);
  const [settingsForm, setSettingsForm] = useState(defaultSettingsForm);
  const [accessForm, setAccessForm] = useState(defaultAccessForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => apiRequest("/api/admin/users"),
  });
  const profileQuery = useQuery({
    queryKey: ["admin-user-profile", selectedUserId],
    queryFn: () => apiRequest(`/api/admin/users/${selectedUserId}/profile`),
    enabled: Boolean(selectedUserId),
  });
  const dataQuery = useQuery({
    queryKey: ["admin-user-data", selectedUserId],
    queryFn: () => apiRequest(`/api/admin/users/${selectedUserId}/data`),
    enabled: Boolean(selectedUserId),
  });

  useEffect(() => {
    if (!selectedUserId && usersQuery.data?.length) {
      setSelectedUserId(usersQuery.data[0].id);
    }
  }, [selectedUserId, usersQuery.data]);

  useEffect(() => {
    if (!profileQuery.data) {
      return;
    }
    setProfileForm({
      full_name: profileQuery.data.full_name || "",
      email: profileQuery.data.email || "",
      naukri_id: profileQuery.data.naukri_id || "",
      naukri_password: "",
    });
    setAccessForm({
      role: profileQuery.data.role || "user",
      account_status: profileQuery.data.account_status || "active",
      new_password: "",
    });
    setSettingsForm({
      job_role: profileQuery.data.settings?.job_role || "",
      preferred_location: profileQuery.data.settings?.preferred_location || "",
      experience: profileQuery.data.settings?.experience || "",
      salary: profileQuery.data.settings?.salary || "",
      keywords: profileQuery.data.settings?.keywords || "",
      scan_mode: profileQuery.data.settings?.scan_mode || "basic",
      pages_to_scrape: profileQuery.data.settings?.pages_to_scrape || 5,
      auto_apply_limit: profileQuery.data.settings?.auto_apply_limit || 10,
      max_job_age_days: profileQuery.data.settings?.max_job_age_days || 10,
    });
  }, [profileQuery.data]);

  function handleSuccess(nextMessage) {
    setMessage(nextMessage);
    setError("");
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    queryClient.invalidateQueries({ queryKey: ["admin-user-profile", selectedUserId] });
    queryClient.invalidateQueries({ queryKey: ["admin-user-data", selectedUserId] });
  }

  const profileMutation = useMutation({
    mutationFn: ({ userId, form }) => apiRequest(`/api/admin/users/${userId}/profile`, { method: "POST", form }),
    onSuccess: () => {
      setProfileForm((previous) => ({ ...previous, naukri_password: "" }));
      handleSuccess("User profile saved.");
    },
    onError: (mutationError) => setError(mutationError.message),
  });
  const settingsMutation = useMutation({
    mutationFn: ({ userId, form }) => apiRequest(`/api/admin/users/${userId}/settings`, { method: "POST", form }),
    onSuccess: () => handleSuccess("User settings saved."),
    onError: (mutationError) => setError(mutationError.message),
  });
  const roleMutation = useMutation({
    mutationFn: ({ userId, role }) => apiRequest(`/api/admin/users/${userId}/role`, { method: "POST", form: { role } }),
    onSuccess: () => handleSuccess("User role updated."),
    onError: (mutationError) => setError(mutationError.message),
  });
  const statusMutation = useMutation({
    mutationFn: ({ userId, account_status }) =>
      apiRequest(`/api/admin/users/${userId}/status`, { method: "POST", form: { account_status } }),
    onSuccess: () => handleSuccess("Account status updated."),
    onError: (mutationError) => setError(mutationError.message),
  });
  const passwordMutation = useMutation({
    mutationFn: ({ userId, new_password }) =>
      apiRequest(`/api/admin/users/${userId}/reset-password`, { method: "POST", form: { new_password } }),
    onSuccess: () => {
      setAccessForm((previous) => ({ ...previous, new_password: "" }));
      handleSuccess("Password reset applied.");
    },
    onError: (mutationError) => setError(mutationError.message),
  });
  const deleteMutation = useMutation({
    mutationFn: (userId) => apiRequest(`/api/admin/users/${userId}`, { method: "DELETE" }),
    onSuccess: () => {
      setMessage("User deleted.");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setSelectedUserId(null);
    },
    onError: (mutationError) => setError(mutationError.message),
  });

  function handleProfileChange(event) {
    const { name, value } = event.target;
    setProfileForm((previous) => ({ ...previous, [name]: value }));
  }

  function handleSettingsChange(event) {
    const { name, value } = event.target;
    setSettingsForm((previous) => ({ ...previous, [name]: value }));
  }

  function handleAccessChange(event) {
    const { name, value } = event.target;
    setAccessForm((previous) => ({ ...previous, [name]: value }));
  }

  function submitProfile(event) {
    event.preventDefault();
    setMessage("");
    setError("");
    profileMutation.mutate({ userId: selectedUserId, form: profileForm });
  }

  function submitSettings(event) {
    event.preventDefault();
    setMessage("");
    setError("");
    settingsMutation.mutate({ userId: selectedUserId, form: settingsForm });
  }

  function submitAccess(event) {
    event.preventDefault();
    setMessage("");
    setError("");
    roleMutation.mutate({ userId: selectedUserId, role: accessForm.role });
    statusMutation.mutate({ userId: selectedUserId, account_status: accessForm.account_status });
    if (accessForm.new_password) {
      passwordMutation.mutate({ userId: selectedUserId, new_password: accessForm.new_password });
    }
  }

  function confirmDelete() {
    if (selectedUserId && window.confirm(`Delete user ${selectedUserId}?`)) {
      deleteMutation.mutate(selectedUserId);
    }
  }

  const rows = (usersQuery.data || []).map((user) => ({
    ...user,
    actions: (
      <div className="inline-actions">
        <button className="ghost-button" onClick={() => setSelectedUserId(user.id)} type="button">
          Inspect
        </button>
      </div>
    ),
  }));
  const selectedProfile = profileQuery.data;
  const counts = Object.entries(dataQuery.data?.counts || {});

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>User Management</h1>
          <p>Inspect accounts, edit profile details, and manage per-user settings with the existing admin APIs.</p>
        </div>
      </header>

      <section className="panel">
        <DataTable
          columns={[
            { key: "id", label: "User ID" },
            { key: "full_name", label: "Name" },
            { key: "email", label: "Email" },
            { key: "role", label: "Role" },
            { key: "account_status", label: "Status" },
            { key: "last_login", label: "Last Login" },
            { key: "created_at", label: "Created" },
            { key: "actions", label: "Actions" },
          ]}
          rows={rows}
        />
      </section>

      {message ? <p className="form-success">{message}</p> : null}
      {error ? <p className="form-error">{error}</p> : null}

      {selectedProfile ? (
        <div className="split-grid">
          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Inspection</p>
                <h2>User Profile</h2>
              </div>
              <span className={`status-pill ${selectedProfile.account_status || "active"}`}>
                {selectedProfile.account_status || "active"}
              </span>
            </div>
            <dl className="detail-list">
              <div>
                <dt>User ID</dt>
                <dd>{selectedProfile.id}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{selectedProfile.email}</dd>
              </div>
              <div>
                <dt>Role</dt>
                <dd>{selectedProfile.role}</dd>
              </div>
              <div>
                <dt>Naukri ID</dt>
                <dd>{selectedProfile.naukri_id || "-"}</dd>
              </div>
              <div>
                <dt>Last Login</dt>
                <dd>{selectedProfile.last_login || "-"}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{selectedProfile.created_at || "-"}</dd>
              </div>
            </dl>
            <div className="micro-grid">
              {counts.map(([key, value]) => (
                <article className="stat-card compact-card" key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <strong>{value}</strong>
                </article>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Edit</p>
                <h2>Profile & Access</h2>
              </div>
            </div>
            <form className="stack-form" onSubmit={submitProfile}>
              <div className="form-grid">
                <label>
                  Full Name
                  <input name="full_name" onChange={handleProfileChange} value={profileForm.full_name} />
                </label>
                <label>
                  Email
                  <input name="email" onChange={handleProfileChange} type="email" value={profileForm.email} />
                </label>
                <label>
                  Naukri ID
                  <input name="naukri_id" onChange={handleProfileChange} value={profileForm.naukri_id} />
                </label>
                <label>
                  Naukri Password
                  <input
                    name="naukri_password"
                    onChange={handleProfileChange}
                    placeholder="Leave blank to keep current value"
                    type="password"
                    value={profileForm.naukri_password}
                  />
                </label>
              </div>
              <button className="primary-button" disabled={profileMutation.isPending} type="submit">
                {profileMutation.isPending ? "Saving..." : "Save Profile"}
              </button>
            </form>

            <form className="stack-form" onSubmit={submitAccess}>
              <div className="form-grid">
                <label>
                  Role
                  <select name="role" onChange={handleAccessChange} value={accessForm.role}>
                    <option value="admin">admin</option>
                    <option value="co_admin">co_admin</option>
                    <option value="user">user</option>
                  </select>
                </label>
                <label>
                  Account Status
                  <select name="account_status" onChange={handleAccessChange} value={accessForm.account_status}>
                    <option value="active">active</option>
                    <option value="disabled">disabled</option>
                  </select>
                </label>
                <label>
                  Reset Password
                  <input
                    minLength="6"
                    name="new_password"
                    onChange={handleAccessChange}
                    placeholder="Optional"
                    type="password"
                    value={accessForm.new_password}
                  />
                </label>
              </div>
              <div className="inline-actions">
                <button
                  className="secondary-button"
                  disabled={roleMutation.isPending || statusMutation.isPending || passwordMutation.isPending}
                  type="submit"
                >
                  Save Access
                </button>
                <button className="danger-button" disabled={deleteMutation.isPending} onClick={confirmDelete} type="button">
                  Delete User
                </button>
              </div>
            </form>
          </section>

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">User Settings</p>
                <h2>Automation Preferences</h2>
              </div>
            </div>
            <form className="stack-form" onSubmit={submitSettings}>
              <div className="form-grid">
                <label>
                  Job Role
                  <input name="job_role" onChange={handleSettingsChange} value={settingsForm.job_role} />
                </label>
                <label>
                  Preferred Location
                  <input
                    name="preferred_location"
                    onChange={handleSettingsChange}
                    value={settingsForm.preferred_location}
                  />
                </label>
                <label>
                  Experience
                  <input name="experience" onChange={handleSettingsChange} value={settingsForm.experience} />
                </label>
                <label>
                  Salary
                  <input name="salary" onChange={handleSettingsChange} value={settingsForm.salary} />
                </label>
                <label>
                  Scan Mode
                  <select name="scan_mode" onChange={handleSettingsChange} value={settingsForm.scan_mode}>
                    <option value="basic">basic</option>
                    <option value="advance">advance</option>
                    <option value="extreme">extreme</option>
                  </select>
                </label>
                <label>
                  Pages To Scrape
                  <input
                    min="1"
                    name="pages_to_scrape"
                    onChange={handleSettingsChange}
                    type="number"
                    value={settingsForm.pages_to_scrape}
                  />
                </label>
                <label>
                  Auto Apply Limit
                  <input
                    min="1"
                    name="auto_apply_limit"
                    onChange={handleSettingsChange}
                    type="number"
                    value={settingsForm.auto_apply_limit}
                  />
                </label>
                <label>
                  Max Job Age Days
                  <input
                    min="1"
                    name="max_job_age_days"
                    onChange={handleSettingsChange}
                    type="number"
                    value={settingsForm.max_job_age_days}
                  />
                </label>
              </div>
              <label>
                Keywords
                <textarea name="keywords" onChange={handleSettingsChange} rows="5" value={settingsForm.keywords} />
              </label>
              <button className="primary-button" disabled={settingsMutation.isPending} type="submit">
                {settingsMutation.isPending ? "Saving..." : "Save Settings"}
              </button>
            </form>
          </section>
        </div>
      ) : null}
    </section>
  );
}
