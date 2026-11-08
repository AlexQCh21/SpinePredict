document.addEventListener("DOMContentLoaded", function () {
  const menuBtn = document.getElementById("menu_toggle");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar_backdrop");
  const perfilTrigger = document.getElementById("perfil_trigger");
  const panelConf = document.getElementById("panel_conf");
  const notiTrigger = document.getElementById("icon_noti");
  const notiPanel = document.getElementById("noti_panel");

  const mobileQuery = window.matchMedia("(max-width: 1024px)");

  function isMobile() {
    return mobileQuery.matches;
  }

  function setExpanded(el, expanded) {
    if (el) el.setAttribute("aria-expanded", String(expanded));
  }

  function syncMenuButton() {
    if (!menuBtn || !sidebar) return;
    const expanded = isMobile()
      ? sidebar.classList.contains("is-open")
      : !sidebar.classList.contains("is-collapsed");
    setExpanded(menuBtn, expanded);
  }

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("is-open");
    if (backdrop) backdrop.classList.add("is-visible");
    document.body.classList.add("nav-open");
    syncMenuButton();
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("is-open");
    if (backdrop) backdrop.classList.remove("is-visible");
    document.body.classList.remove("nav-open");
    syncMenuButton();
  }

  function toggleSidebar() {
    if (!sidebar) return;
    if (isMobile()) {
      if (sidebar.classList.contains("is-open")) {
        closeSidebar();
      } else {
        openSidebar();
      }
      return;
    }

    const collapsed = sidebar.classList.toggle("is-collapsed");
    setExpanded(menuBtn, !collapsed);
  }

  function closePanel(panel, trigger) {
    if (!panel || panel.classList.contains("d-none")) return;
    panel.classList.add("d-none");
    setExpanded(trigger, false);
  }

  function togglePanel(panel, trigger) {
    if (!panel) return;
    const willOpen = panel.classList.contains("d-none");
    panel.classList.toggle("d-none");
    setExpanded(trigger, willOpen);
  }

  if (menuBtn) {
    menuBtn.addEventListener("click", toggleSidebar);
    syncMenuButton();
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeSidebar);
  }

  if (sidebar) {
    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (isMobile()) closeSidebar();
      });
    });
  }

  if (perfilTrigger && panelConf) {
    perfilTrigger.addEventListener("click", function (event) {
      event.stopPropagation();
      togglePanel(panelConf, perfilTrigger);
      closePanel(notiPanel, notiTrigger);
    });
  }

  if (notiTrigger && notiPanel) {
    notiTrigger.addEventListener("click", function (event) {
      event.stopPropagation();
      togglePanel(notiPanel, notiTrigger);
      closePanel(panelConf, perfilTrigger);
    });
  }

  document.addEventListener("click", function (event) {
    if (panelConf && perfilTrigger && !panelConf.contains(event.target) && !perfilTrigger.contains(event.target)) {
      closePanel(panelConf, perfilTrigger);
    }
    if (notiPanel && notiTrigger && !notiPanel.contains(event.target) && !notiTrigger.contains(event.target)) {
      closePanel(notiPanel, notiTrigger);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    closePanel(panelConf, perfilTrigger);
    closePanel(notiPanel, notiTrigger);
    if (isMobile() && sidebar && sidebar.classList.contains("is-open")) {
      closeSidebar();
    }
  });

  document.addEventListener("submit", function (event) {
    const form = event.target.closest("form[data-confirm]");
    if (!form) return;
    if (!window.confirm(form.getAttribute("data-confirm"))) {
      event.preventDefault();
    }
  });

  function handleViewportChange() {
    if (!isMobile()) {
      closeSidebar();
      document.body.classList.remove("nav-open");
    }
    syncMenuButton();
  }

  if (mobileQuery.addEventListener) {
    mobileQuery.addEventListener("change", handleViewportChange);
  } else if (mobileQuery.addListener) {
    mobileQuery.addListener(handleViewportChange);
  }
});
