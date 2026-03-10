(function () {
  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DURATION = 280;
  let profileListenersBound = false;
  let navTransitionBound = false;
  const seenToasts = new Set();
  const pipelineMonitor = {
    activeRunId: null,
    intervalId: null,
    lastStatus: "",
  };

  function animateIn(elements) {
    if (reduceMotion) return;
    elements.forEach((el, idx) => {
      if (!el || el.dataset.animatedIn === "1") return;
      el.dataset.animatedIn = "1";
      el.style.opacity = "0";
      el.style.transform = "translateY(8px)";
      el.style.transition = `opacity ${DURATION}ms ease, transform ${DURATION}ms ease`;
      window.setTimeout(() => {
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
      }, Math.min(idx * 30, 180));
    });
  }

  function setActiveNav() {
    const currentPath = window.location.pathname.replace(/\/+$/, "") || "/";
    document.querySelectorAll(".nav-links a").forEach((link) => {
      const path = (new URL(link.href, window.location.origin).pathname || "/").replace(/\/+$/, "") || "/";
      const isActive = currentPath === path;
      link.classList.toggle("is-active", isActive);
      if (isActive) {
        link.style.fontWeight = "700";
        link.style.borderLeft = "3px solid var(--accent-color)";
        link.style.paddingLeft = "17px";
      } else {
        link.style.fontWeight = "";
        link.style.borderLeft = "";
        link.style.paddingLeft = "";
      }
    });
  }

  function ensureToastRoot() {
    let root = document.getElementById("toastRoot");
    if (root) return root;
    root = document.createElement("div");
    root.id = "toastRoot";
    root.style.position = "fixed";
    root.style.right = "18px";
    root.style.bottom = "18px";
    root.style.zIndex = "9999";
    root.style.display = "grid";
    root.style.gap = "8px";
    document.body.appendChild(root);
    return root;
  }

  function toast(message, type) {
    if (!message) return;
    const root = ensureToastRoot();
    const item = document.createElement("div");
    item.textContent = message;
    item.style.padding = "10px 12px";
    item.style.borderRadius = "8px";
    item.style.boxShadow = "0 8px 20px rgba(0,0,0,0.18)";
    item.style.fontSize = "13px";
    item.style.maxWidth = "420px";
    item.style.background = type === "error" ? "#b91c1c" : "#0f766e";
    item.style.color = "#fff";
    item.style.opacity = "0";
    item.style.transform = "translateY(6px)";
    item.style.transition = "opacity 180ms ease, transform 180ms ease";
    root.appendChild(item);
    requestAnimationFrame(() => {
      item.style.opacity = "1";
      item.style.transform = "translateY(0)";
    });
    window.setTimeout(() => {
      item.style.opacity = "0";
      item.style.transform = "translateY(6px)";
      window.setTimeout(() => item.remove(), 220);
    }, 2600);
  }

  function markRowsAnimated(scope) {
    const rows =
      scope instanceof HTMLElement && scope.tagName === "TR"
        ? [scope]
        : [...(scope || document).querySelectorAll("table tbody tr")];
    rows.forEach((row) => {
      if (row.dataset.rowAnimated === "1") return;
      row.dataset.rowAnimated = "1";
      row.classList.add("row-enter");
      window.setTimeout(() => row.classList.remove("row-enter"), 320);
    });
  }

  function bindTableObservers() {
    const tbodies = document.querySelectorAll("table tbody");
    tbodies.forEach((tbody) => {
      if (tbody.dataset.observeRows === "1") return;
      tbody.dataset.observeRows = "1";
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((m) => {
          m.addedNodes.forEach((node) => {
            if (!(node instanceof HTMLElement)) return;
            if (node.tagName === "TR") {
              markRowsAnimated(node);
            } else {
              markRowsAnimated(node);
            }
          });
        });
      });
      observer.observe(tbody, { childList: true, subtree: true });
    });
    markRowsAnimated(document);
  }

  function applyPageEnterTransition() {
    if (reduceMotion) return;
    document.body.classList.add("page-fade-enter");
    requestAnimationFrame(() => {
      document.body.classList.add("page-fade-enter-active");
    });
    window.setTimeout(() => {
      document.body.classList.remove("page-fade-enter", "page-fade-enter-active");
    }, 240);
  }

  function bindNavTransitions() {
    if (navTransitionBound || reduceMotion) return;
    navTransitionBound = true;
    document.addEventListener("click", (evt) => {
      const link = evt.target.closest("a[href]");
      if (!link) return;
      if (link.target === "_blank" || evt.defaultPrevented) return;
      const href = link.getAttribute("href") || "";
      if (!href.startsWith("/") || href.startsWith("//")) return;
      evt.preventDefault();
      document.body.classList.add("page-fade-leave");
      window.setTimeout(() => {
        window.location.assign(href);
      }, 180);
    });
  }

  function bindButtonRipple() {
    document.querySelectorAll(".mui-btn").forEach((btn) => {
      if (btn.dataset.rippleBound === "1") return;
      btn.dataset.rippleBound = "1";
      btn.addEventListener("click", (evt) => {
        const rect = btn.getBoundingClientRect();
        const ripple = document.createElement("span");
        const size = Math.max(rect.width, rect.height);
        ripple.className = "btn-ripple";
        ripple.style.width = `${size}px`;
        ripple.style.height = `${size}px`;
        ripple.style.left = `${evt.clientX - rect.left - size / 2}px`;
        ripple.style.top = `${evt.clientY - rect.top - size / 2}px`;
        btn.appendChild(ripple);
        window.setTimeout(() => ripple.remove(), 460);
      });
    });
  }

  function setStageState(stageNode, state) {
    if (!stageNode) return;
    stageNode.classList.remove("is-active", "is-done", "is-failed");
    if (state) stageNode.classList.add(state);
  }

  function updatePipelineProgress(run) {
    const progress = document.getElementById("pipelineProgress");
    const stateNode = document.getElementById("pipelineProgressState");
    if (!progress || !stateNode) return;

    const fetching = progress.querySelector('[data-stage="fetching"]');
    const ranking = progress.querySelector('[data-stage="ranking"]');
    const applying = progress.querySelector('[data-stage="applying"]');

    const fetched = Number(run && run.fetched_count ? run.fetched_count : 0);
    const shortlisted = Number(run && run.shortlisted_count ? run.shortlisted_count : 0);
    const applied = Number(run && run.applied_count ? run.applied_count : 0);
    const status = ((run && run.status) || "idle").toLowerCase();

    stateNode.className = "pipeline-state";

    if (status === "queued" || status === "running") {
      stateNode.classList.add("state-running");
      stateNode.textContent = status === "queued" ? "Queued" : "Running";
      setStageState(fetching, "is-active");
      setStageState(ranking, "");
      setStageState(applying, "");
      if (fetched > 0) {
        setStageState(fetching, "is-done");
        setStageState(ranking, "is-active");
      }
      if (shortlisted > 0) {
        setStageState(ranking, "is-done");
        setStageState(applying, "is-active");
      }
      if (applied > 0) {
        setStageState(applying, "is-active");
      }
      return;
    }

    if (status === "completed") {
      stateNode.classList.add("state-completed");
      stateNode.textContent = "Completed";
      setStageState(fetching, "is-done");
      setStageState(ranking, "is-done");
      setStageState(applying, "is-done");
      return;
    }

    if (status === "failed") {
      stateNode.classList.add("state-failed");
      stateNode.textContent = "Failed";
      setStageState(fetching, fetched > 0 ? "is-done" : "is-failed");
      setStageState(ranking, shortlisted > 0 ? "is-done" : fetched > 0 ? "is-failed" : "");
      setStageState(applying, applied > 0 ? "is-done" : shortlisted > 0 ? "is-failed" : "");
      return;
    }

    stateNode.classList.add("state-idle");
    stateNode.textContent = "Idle";
    setStageState(fetching, "");
    setStageState(ranking, "");
    setStageState(applying, "");
  }

  function extractRunId(messageText) {
    if (!messageText) return null;
    const match = messageText.match(/run\s*#(\d+)/i);
    if (!match) return null;
    return Number(match[1]);
  }

  async function getPipelineRun(runId) {
    const response = await fetch(`/api/pipeline-runs/${runId}`, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Run ${runId} unavailable`);
    return response.json();
  }

  async function getLatestPipelineRun() {
    const response = await fetch("/api/pipeline-runs", { headers: { Accept: "application/json" } });
    if (!response.ok) return null;
    const rows = await response.json();
    if (!Array.isArray(rows) || rows.length === 0) return null;
    return rows[0];
  }

  function stopPipelineMonitor() {
    if (pipelineMonitor.intervalId) {
      window.clearInterval(pipelineMonitor.intervalId);
      pipelineMonitor.intervalId = null;
    }
  }

  async function monitorPipelineRun(runId) {
    if (!runId) return;
    if (pipelineMonitor.activeRunId !== runId) {
      pipelineMonitor.lastStatus = "";
    }
    pipelineMonitor.activeRunId = runId;
    stopPipelineMonitor();

    const readAndRender = async () => {
      try {
        const run = await getPipelineRun(runId);
        updatePipelineProgress(run);

        const status = (run.status || "").toLowerCase();
        if (status && status !== pipelineMonitor.lastStatus) {
          if (status === "completed" && !seenToasts.has(`completed-${runId}`)) {
            seenToasts.add(`completed-${runId}`);
            toast(`Pipeline #${runId} completed`, "ok");
          } else if (status === "failed" && !seenToasts.has(`failed-${runId}`)) {
            seenToasts.add(`failed-${runId}`);
            toast(`Pipeline #${runId} failed`, "error");
          }
        }

        pipelineMonitor.lastStatus = status;
        if (status === "completed" || status === "failed") {
          stopPipelineMonitor();
        }
      } catch (_err) {
        stopPipelineMonitor();
      }
    };

    await readAndRender();
    pipelineMonitor.intervalId = window.setInterval(readAndRender, 4000);
  }

  async function initPipelineProgress() {
    if (window.location.pathname !== "/fetch-jobs") return;
    const latestRun = await getLatestPipelineRun();
    if (!latestRun) {
      updatePipelineProgress({ status: "idle" });
      return;
    }
    const status = (latestRun.status || "").toLowerCase();
    updatePipelineProgress(latestRun);
    if (status === "queued" || status === "running") {
      await monitorPipelineRun(latestRun.id);
    }
  }

  function bindProfileMenu() {
    if (profileListenersBound) return;
    profileListenersBound = true;
    document.addEventListener("click", (e) => {
      const profileMenu = document.getElementById("profileMenu");
      const profileToggle = document.getElementById("profileToggle");
      if (!profileMenu || !profileToggle) return;

      if (profileToggle.contains(e.target)) {
        e.stopPropagation();
        const open = profileMenu.classList.toggle("open");
        profileToggle.setAttribute("aria-expanded", open ? "true" : "false");
        return;
      }

      if (!profileMenu.contains(e.target)) {
        profileMenu.classList.remove("open");
        profileToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  function syncTopbarTitle() {
    const topbarTitle = document.querySelector(".topbar h1");
    if (!topbarTitle) return;
    const map = {
      "/dashboard": "Dashboard",
      "/resume-analyzer": "Resume Analyzer",
      "/keywords": "Key-Skills",
      "/fetch-jobs": "Fetch Jobs",
      "/jobs-directory": "Jobs Directory",
      "/relevant-jobs": "Relevant Jobs",
      "/applied-jobs": "Applied Jobs",
      "/ext-jobs": "External Jobs",
      "/settings": "Control Panel",
      "/profile": "Profile",
      "/admin": "Admin Dashboard",
      "/admin/users": "Manage Users",
      "/admin/settings": "System Settings",
      "/admin/logs": "Admin Logs",
    };
    const currentPath = window.location.pathname.replace(/\/+$/, "") || "/";
    if (map[currentPath]) topbarTitle.textContent = map[currentPath];
  }

  function onReady() {
    syncTopbarTitle();
    setActiveNav();
    animateIn([...document.querySelectorAll(".panel-card, .table-shell, .auth-card, table tbody tr")]);
    bindProfileMenu();
    bindButtonRipple();
    bindNavTransitions();
    bindTableObservers();
    applyPageEnterTransition();
    initPipelineProgress();
  }

  document.addEventListener("DOMContentLoaded", onReady);
  window.addEventListener("pageshow", onReady);

  if (window.htmx) {
    document.body.addEventListener("htmx:beforeRequest", (evt) => {
      const trigger = evt.detail && evt.detail.elt;
      if (!trigger) return;
      trigger.setAttribute("aria-busy", "true");
      trigger.style.opacity = "0.75";
    });

    document.body.addEventListener("htmx:afterRequest", (evt) => {
      const trigger = evt.detail && evt.detail.elt;
      if (trigger) {
        trigger.removeAttribute("aria-busy");
        trigger.style.opacity = "";
      }

      const xhr = evt.detail && evt.detail.xhr;
      if (!xhr) return;

      if (xhr.status >= 400) {
        toast("Action failed. Please retry.", "error");
      } else if (xhr.status >= 200 && xhr.status < 300) {
        const target = evt.detail && evt.detail.target;
        const fromRunPipeline = trigger && trigger.getAttribute && trigger.getAttribute("hx-post") === "/ui/run-pipeline";
        if (fromRunPipeline && !seenToasts.has("pipeline-started-last")) {
          seenToasts.add("pipeline-started-last");
          window.setTimeout(() => seenToasts.delete("pipeline-started-last"), 900);
          toast("Pipeline started", "ok");
        }

        const headerMessage = xhr.getResponseHeader("X-Status-Message");
        if (headerMessage) toast(headerMessage, "ok");

        if (target && target.id === "actionStatus") {
          const runId = extractRunId((target.textContent || "").trim());
          if (runId) {
            monitorPipelineRun(runId);
          }
        }
      }
    });

    document.body.addEventListener("htmx:afterSwap", (evt) => {
      setActiveNav();
      animateIn([...document.querySelectorAll(".panel-card, .table-shell, table tbody tr")]);
      bindButtonRipple();
      bindTableObservers();

      const target = evt.detail && evt.detail.target;
      if (target && target.id === "actionStatus") {
        const runId = extractRunId((target.textContent || "").trim());
        if (runId) {
          monitorPipelineRun(runId);
        }
      }
    });
  }
})();
