async function linkPortal() {
  const status = document.getElementById("status");
  status.innerText = "Linking Naukri profile...";

  const res = await fetch("/api/portal/login", { method: "POST" });
  const data = await res.json();

  if (!res.ok) {
    status.innerText = data.error || "Portal login failed";
    return;
  }

  status.innerText = data.message || "Portal linked successfully";
}

async function runPipeline() {
  const status = document.getElementById("status");
  const form = document.getElementById("fetchForm");
  const formData = new FormData(form);
  const runBtn = document.getElementById("runBtn");

  if (!formData.get("resume_file") || formData.get("resume_file").size === 0) {
    status.innerText = "Upload a .txt resume file first";
    return;
  }

  status.innerText = "Submitting pipeline...";
  runBtn.disabled = true;

  const res = await fetch("/api/fetch-jobs", {
    method: "POST",
    body: formData
  });
  const data = await res.json();

  if (!res.ok) {
    status.innerText = data.error || "Pipeline failed";
    runBtn.disabled = false;
    await loadRuns();
    return;
  }

  status.innerText = `Run #${data.run_id} queued. Waiting for completion...`;
  pollRun(data.run_id, runBtn);
  await loadRuns();
}

async function pollRun(runId, runBtn) {
  const status = document.getElementById("status");

  const intervalId = setInterval(async () => {
    const res = await fetch(`/api/pipeline-runs/${runId}`);
    const data = await res.json();

    if (!res.ok) {
      status.innerText = data.error || "Unable to read run status";
      clearInterval(intervalId);
      runBtn.disabled = false;
      return;
    }

    if (data.status === "queued") {
      status.innerText = `Run #${runId} queued...`;
      return;
    }

    if (data.status === "running") {
      status.innerText = `Run #${runId} running...`;
      return;
    }

    if (data.status === "completed") {
      status.innerText = `Completed: fetched ${data.fetched_count}, shortlisted ${data.shortlisted_count}, applied ${data.applied_count}. ${data.message || ""}`;
      clearInterval(intervalId);
      runBtn.disabled = false;
      await loadRuns();
      return;
    }

    if (data.status === "failed") {
      status.innerText = `Run failed: ${data.message || "Unknown error"}`;
      clearInterval(intervalId);
      runBtn.disabled = false;
      await loadRuns();
    }
  }, 4000);
}

async function loadRuns() {
  const tbody = document.querySelector("#runsTable tbody");
  tbody.innerHTML = "";

  const res = await fetch("/api/pipeline-runs");
  const data = await res.json();

  data.forEach(run => {
    const row = `
    <tr>
      <td>${run.id}</td>
      <td>${run.status}</td>
      <td>${run.pages}</td>
      <td>${run.auto_apply_limit}</td>
      <td>${run.fetched_count}</td>
      <td>${run.shortlisted_count}</td>
      <td>${run.applied_count}</td>
      <td>${run.message || "-"}</td>
    </tr>
    `;
    tbody.innerHTML += row;
  });
}

document.getElementById("linkPortalBtn").addEventListener("click", linkPortal);
document.getElementById("runBtn").addEventListener("click", runPipeline);
loadRuns();
