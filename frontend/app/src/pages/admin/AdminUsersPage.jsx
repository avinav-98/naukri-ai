import { useMutation, useQuery } from "@tanstack/react-query";

import { DataTable } from "../../components/DataTable";
import { apiRequest } from "../../lib/api";
import { queryClient } from "../../lib/queryClient";

export function AdminUsersPage() {
  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => apiRequest("/api/admin/users"),
  });

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }) => apiRequest(`/api/admin/users/${userId}/role`, { method: "POST", form: { role } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const statusMutation = useMutation({
    mutationFn: ({ userId, account_status }) =>
      apiRequest(`/api/admin/users/${userId}/status`, { method: "POST", form: { account_status } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const deleteMutation = useMutation({
    mutationFn: (userId) => apiRequest(`/api/admin/users/${userId}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const passwordMutation = useMutation({
    mutationFn: ({ userId, new_password }) =>
      apiRequest(`/api/admin/users/${userId}/reset-password`, { method: "POST", form: { new_password } }),
  });

  function promptRole(userId) {
    const role = window.prompt("Enter role: admin, co_admin, or user");
    if (role) {
      roleMutation.mutate({ userId, role });
    }
  }

  function promptStatus(userId) {
    const account_status = window.prompt("Enter status: active or disabled");
    if (account_status) {
      statusMutation.mutate({ userId, account_status });
    }
  }

  function promptPassword(userId) {
    const new_password = window.prompt("Enter new password (minimum 6 characters)");
    if (new_password) {
      passwordMutation.mutate({ userId, new_password });
    }
  }

  function confirmDelete(userId) {
    if (window.confirm(`Delete user ${userId}?`)) {
      deleteMutation.mutate(userId);
    }
  }

  const rows = (usersQuery.data || []).map((user) => ({
    ...user,
    actions: (
      <div className="inline-actions">
        <button className="ghost-button" onClick={() => promptRole(user.id)} type="button">
          Role
        </button>
        <button className="ghost-button" onClick={() => promptStatus(user.id)} type="button">
          Status
        </button>
        <button className="ghost-button" onClick={() => promptPassword(user.id)} type="button">
          Reset Password
        </button>
        <button className="danger-button" onClick={() => confirmDelete(user.id)} type="button">
          Delete
        </button>
      </div>
    ),
  }));

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>User Management</h1>
          <p>Manage account roles, status, and password resets from the existing FastAPI admin APIs.</p>
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
    </section>
  );
}
