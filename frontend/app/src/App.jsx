import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthLayout } from "./components/AuthLayout";
import { SignInPage } from "./pages/auth/SignInPage";
import { SignUpPage } from "./pages/auth/SignUpPage";
import { ForgotPasswordPage } from "./pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/auth/ResetPasswordPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FetchJobsPage } from "./pages/FetchJobsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ResourcePage } from "./pages/ResourcePage";
import { AdminOverviewPage } from "./pages/admin/AdminOverviewPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";
import { AdminSettingsPage } from "./pages/admin/AdminSettingsPage";
import { AdminLogsPage } from "./pages/admin/AdminLogsPage";

const resourceConfigs = {
  "/jobs-directory": {
    title: "Job Directory",
    queryKey: ["jobs-directory"],
    endpoint: "/api/jobs-directory",
    description: "Latest scraped jobs for the active user.",
    columns: [
      { key: "title", label: "Job Title" },
      { key: "company", label: "Company" },
      { key: "location", label: "Location" },
      { key: "url", label: "Job Link", type: "link" },
    ],
  },
  "/relevant-jobs": {
    title: "Relevant Jobs",
    queryKey: ["relevant-jobs"],
    endpoint: "/api/relevant-jobs",
    description: "Ranked matches after relevance scoring.",
    columns: [
      { key: "title", label: "Job Title" },
      { key: "company", label: "Company" },
      { key: "location", label: "Location" },
      { key: "score", label: "Score" },
      { key: "url", label: "Job Link", type: "link" },
    ],
  },
  "/applied-jobs": {
    title: "Applied Jobs",
    queryKey: ["applied-jobs"],
    endpoint: "/api/applied-jobs",
    description: "Only jobs with confirmed internal application success.",
    columns: [
      { key: "title", label: "Job Title" },
      { key: "company", label: "Company" },
      { key: "location", label: "Location" },
      { key: "experience", label: "Experience" },
      { key: "applied_at", label: "Applied At" },
      { key: "status", label: "Status" },
      { key: "url", label: "Job Link", type: "link" },
    ],
  },
  "/ext-jobs": {
    title: "External Jobs",
    queryKey: ["ext-jobs"],
    endpoint: "/api/ext-jobs",
    description: "Jobs that redirect to company sites and require manual application.",
    columns: [
      { key: "title", label: "Job Title" },
      { key: "company", label: "Company" },
      { key: "location", label: "Location" },
      { key: "experience", label: "Experience" },
      { key: "resume_match_score", label: "Match Score" },
      { key: "job_url", label: "Naukri Link", type: "link" },
      { key: "external_apply_url", label: "External Apply", type: "link" },
      { key: "captured_at", label: "Captured At" },
    ],
  },
  "/resume-analyzer": {
    title: "Resume Analyzer",
    queryKey: ["resume-analyzer"],
    endpoint: "/api/resume-analyzer",
    description: "Resume match scores driven by stored resume text and key-skills.",
    columns: [
      { key: "title", label: "Job Title" },
      { key: "company", label: "Company" },
      { key: "location", label: "Location" },
      { key: "score", label: "Score" },
      { key: "matched_keywords", label: "Matched Key-Skills", type: "list" },
      { key: "job_url", label: "Job Link", type: "link" },
    ],
  },
  "/keywords": {
    title: "Key-Skills",
    queryKey: ["key-skills"],
    endpoint: "/api/key-skills",
    description: "Stored key-skills extracted from job listings and settings.",
    columns: [{ key: "value", label: "Key-Skills" }],
    transform: (payload) => (payload?.items || []).map((item) => ({ value: item })),
    actions: [{ label: "Download Key-Skills (.txt)", href: "/api/key-skills/download" }],
  },
};

export default function App() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/" element={<Navigate to="/signin" replace />} />
        <Route path="/signin" element={<SignInPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
      </Route>

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/fetch-jobs" element={<FetchJobsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        {Object.entries(resourceConfigs).map(([path, config]) => (
          <Route key={path} path={path} element={<ResourcePage {...config} />} />
        ))}
        <Route path="/admin" element={<ProtectedRoute roles={["admin", "co_admin"]}><AdminOverviewPage /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute roles={["admin", "co_admin"]}><AdminUsersPage /></ProtectedRoute>} />
        <Route path="/admin/settings" element={<ProtectedRoute roles={["admin"]}><AdminSettingsPage /></ProtectedRoute>} />
        <Route path="/admin/logs" element={<ProtectedRoute roles={["admin", "co_admin"]}><AdminLogsPage /></ProtectedRoute>} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
