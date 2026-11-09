document.addEventListener("DOMContentLoaded", function () {
  const dialog = document.getElementById("legal_notice_modal");
  if (!dialog) return;

  const triggers = document.querySelectorAll("[data-legal-open]");
  const closers = dialog.querySelectorAll("[data-legal-close]");
  let lastTrigger = null;

  function isOpen() {
    return dialog.hasAttribute("open");
  }

  function openDialog(trigger) {
    if (isOpen()) return;
    lastTrigger = trigger;
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.setAttribute("open", "");
    }
    document.documentElement.classList.add("legal-open");
  }

  function closeDialog() {
    if (!isOpen()) return;
    if (typeof dialog.close === "function") {
      dialog.close();
      return;
    }
    dialog.removeAttribute("open");
    document.documentElement.classList.remove("legal-open");
    if (lastTrigger) lastTrigger.focus();
  }

  triggers.forEach(function (trigger) {
    trigger.addEventListener("click", function (event) {
      event.preventDefault();
      openDialog(trigger);
    });
  });

  closers.forEach(function (closer) {
    closer.addEventListener("click", closeDialog);
  });

  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) {
      closeDialog();
    }
  });

  dialog.addEventListener("close", function () {
    document.documentElement.classList.remove("legal-open");
    if (lastTrigger) lastTrigger.focus();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape" || !isOpen()) return;
    if (typeof dialog.showModal !== "function") {
      closeDialog();
    }
  });
});
