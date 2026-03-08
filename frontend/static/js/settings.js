function setResumeStatus(message) {
  document.getElementById("resumeStatus").innerText = message;
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();

  document.getElementById("job_role").value = data.job_role || "";
  document.getElementById("location").value = data.preferred_location || "";
  document.getElementById("experience").value = data.experience || "";
  document.getElementById("salary").value = data.salary || "";
  document.getElementById("pages").value = data.pages_to_scrape || 5;
  document.getElementById("limit").value = data.auto_apply_limit || 10;
  setResumeStatus(data.has_resume ? "Resume.txt saved" : "No resume.txt uploaded");
}

document.getElementById("settingsForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const formData = new FormData();
  formData.append("job_role", document.getElementById("job_role").value);
  formData.append("preferred_location", document.getElementById("location").value);
  formData.append("experience", document.getElementById("experience").value);
  formData.append("salary", document.getElementById("salary").value);
  formData.append("pages_to_scrape", document.getElementById("pages").value);
  formData.append("auto_apply_limit", document.getElementById("limit").value);

  const resumeInput = document.getElementById("resume_file");
  if (resumeInput.files && resumeInput.files.length > 0) {
    formData.append("resume_file", resumeInput.files[0]);
  }

  const res = await fetch("/api/settings", {
    method: "POST",
    body: formData
  });
  const data = await res.json();

  if (!res.ok) {
    alert(data.error || "Unable to save settings");
    return;
  }

  setResumeStatus(data.has_resume ? "Resume.txt saved" : "No resume.txt uploaded");
  resumeInput.value = "";
  alert("Settings saved");
});

loadSettings();
