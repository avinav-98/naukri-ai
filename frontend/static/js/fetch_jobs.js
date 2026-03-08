let canRunPipeline = false;

function setStatus(message) {
  const status = document.getElementById("status");
  status.innerText = message;
}

function formatRunDate(ts) {
  if (!ts) return "-";
  const parsed = new Date(ts);
  return Number.isNaN(parsed.getTime()) ? ts : parsed.toLocaleString();
}

async function linkPortal() {
  setStatus("Linking Naukri profile...");

  const res = await fetch("/api/portal/login", { method: "POST" });
  const data = await res.json();
  const runBtn = document.getElementById("runBtn");

  if (!res.ok) {
    canRunPipeline = false;
    runBtn.disabled = true;
    setStatus(data.error || "Portal login failed");
    return;
  }

  canRunPipeline = true;
  runBtn.disabled = false;
  setStatus(data.message || "Portal linked successfully. You can run pipeline now.");
}

async function runPipeline() {
  const runBtn = document.getElementById("runBtn");

  if (!canRunPipeline) {
    setStatus("Link Naukri profile before running pipeline.");
    return;
  }

  setStatus("Submitting pipeline...");
  runBtn.disabled = true;

  const res = await fetch("/api/fetch-jobs", {
    method: "POST"
  });
  const data = await res.json();

  if (!res.ok) {
    setStatus(data.error || "Pipeline failed");
    runBtn.disabled = false;
    await loadRuns();
    return;
  }

  setStatus(`Run #${data.run_id} queued. Waiting for completion...`);
  pollRun(data.run_id, runBtn);
  await loadRuns();
}

async function pollRun(runId, runBtn) {
  const intervalId = setInterval(async () => {
    const res = await fetch(`/api/pipeline-runs/${runId}`);
    const data = await res.json();

    if (!res.ok) {
      setStatus(data.error || "Unable to read run status");
      clearInterval(intervalId);
      runBtn.disabled = false;
      return;
    }

    if (data.status === "queued") {
      setStatus(`Run #${runId} queued...`);
      return;
    }

    if (data.status === "running") {
      setStatus(`Run #${runId} running...`);
      return;
    }

    if (data.status === "completed") {
      setStatus(`Completed: fetched ${data.fetched_count}, shortlisted ${data.shortlisted_count}. ${data.message || ""}`);
      clearInterval(intervalId);
      runBtn.disabled = false;
      await loadRuns();
      return;
    }

    if (data.status === "failed") {
      setStatus(`Run failed: ${data.message || "Unknown error"}`);
      clearInterval(intervalId);
      runBtn.disabled = false;
      await loadRuns();
    }
  }, 4000);
}

async function clearHistory() {
  const runBtn = document.getElementById("runBtn");
  const res = await fetch("/api/pipeline-runs", { method: "DELETE" });
  const data = await res.json();

  if (!res.ok) {
    setStatus(data.error || "Unable to clear history");
    return;
  }

  setStatus(`Cleared ${data.deleted_count || 0} run records.`);
  runBtn.disabled = !canRunPipeline;
  await loadRuns();
}

async function loadRuns() {
  const tbody = document.querySelector("#runsTable tbody");
  tbody.innerHTML = "";

  const res = await fetch("/api/pipeline-runs");
  const data = await res.json();

  if (!Array.isArray(data) || data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6">No runs yet.</td></tr>`;
    return;
  }

  data.forEach(run => {
    const row = `
    <tr>
      <td>${formatRunDate(run.started_at || run.finished_at)}</td>
      <td>${run.pages}</td>
      <td>${run.auto_apply_limit}</td>
      <td>${run.fetched_count}</td>
      <td>${run.shortlisted_count}</td>
      <td>${run.status}: ${run.message || "-"}</td>
    </tr>
    `;
    tbody.innerHTML += row;
  });
}

async function loadControlPanelStatus() {
  const res = await fetch("/api/settings");
  if (!res.ok) return;

  const data = await res.json();
  if (!data.has_resume) {
    setStatus("Upload resume.txt in Control Panel, then link profile and run pipeline.");
  }
}

document.getElementById("linkPortalBtn").addEventListener("click", linkPortal);
document.getElementById("runBtn").addEventListener("click", runPipeline);
document.getElementById("clearHistoryBtn").addEventListener("click", clearHistory);
loadControlPanelStatus();
loadRuns();
