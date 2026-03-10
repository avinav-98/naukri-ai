(function () {
  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DURATION = 280;

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

  function onReady() {
    const topbarTitle = document.querySelector(".topbar h1");
    if (topbarTitle) {
      const map = {
        "/dashboard": "Dashboard",
        "/resume-analyzer": "Resume Analyzer",
        "/keywords": "Keywords",
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
    setActiveNav();
    animateIn([...document.querySelectorAll(".panel-card, .table-shell, .auth-card, table tbody tr")]);

    const profileMenu = document.getElementById("profileMenu");
    const profileToggle = document.getElementById("profileToggle");
    if (profileMenu && profileToggle) {
      profileToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        const open = profileMenu.classList.toggle("open");
        profileToggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      document.addEventListener("click", (e) => {
        if (!profileMenu.contains(e.target)) {
          profileMenu.classList.remove("open");
          profileToggle.setAttribute("aria-expanded", "false");
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", onReady);
  window.addEventListener("pageshow", onReady);

  if (window.htmx) {
    document.body.addEventListener("htmx:beforeRequest", (evt) => {
      const trigger = evt.detail && evt.detail.elt;
      if (trigger) {
        trigger.dataset.prevLabel = trigger.innerText || "";
        trigger.setAttribute("aria-busy", "true");
        trigger.style.opacity = "0.75";
      }
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
      } else if (xhr.status >= 200 && xhr.status < 300 && evt.type === "htmx:afterRequest") {
        const headerMessage = xhr.getResponseHeader("X-Status-Message");
        if (headerMessage) toast(headerMessage, "ok");
      }
    });

    document.body.addEventListener("htmx:afterSwap", () => {
      setActiveNav();
      animateIn([...document.querySelectorAll(".panel-card, .table-shell, table tbody tr")]);
    });
  }
})();
