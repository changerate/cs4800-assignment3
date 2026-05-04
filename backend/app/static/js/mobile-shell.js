(() => {
  const closeDiscoverSheet = () => {
    const panel = document.getElementById("discover-panel");
    const backdrop = document.querySelector("[data-discover-backdrop]");
    const trigger = document.querySelector("[data-open-discover-sheet]");
    if (panel) panel.classList.remove("is-open");
    if (backdrop) {
      backdrop.classList.remove("is-open");
      backdrop.setAttribute("aria-hidden", "true");
    }
    if (trigger) trigger.setAttribute("aria-expanded", "false");
    document.body.classList.remove("discover-sheet-open");
  };

  const openDiscoverSheet = () => {
    const panel = document.getElementById("discover-panel");
    const backdrop = document.querySelector("[data-discover-backdrop]");
    const trigger = document.querySelector("[data-open-discover-sheet]");
    if (!panel || !backdrop) return;
    panel.classList.add("is-open");
    backdrop.classList.add("is-open");
    backdrop.setAttribute("aria-hidden", "false");
    if (trigger) trigger.setAttribute("aria-expanded", "true");
    document.body.classList.add("discover-sheet-open");
  };

  document.addEventListener(
    "click",
    (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      if (target.closest("[data-open-topic-filters]")) {
        event.preventDefault();
        const dialog = document.getElementById("topic-filters-dialog");
        const trigger = target.closest("[data-open-topic-filters]");
        if (dialog && typeof dialog.showModal === "function") {
          dialog.showModal();
          if (trigger) trigger.setAttribute("aria-expanded", "true");
        }
        return;
      }

      if (target.id === "topic-filters-dialog") {
        event.preventDefault();
        target.close();
        return;
      }

      if (target.closest("[data-open-discover-sheet]")) {
        event.preventDefault();
        openDiscoverSheet();
        return;
      }

      if (target.closest("[data-close-discover-sheet]")) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        closeDiscoverSheet();
        return;
      }

      const backdrop = target.closest("[data-discover-backdrop]");
      if (
        backdrop &&
        backdrop.classList.contains("is-open") &&
        event.target === backdrop
      ) {
        closeDiscoverSheet();
      }
    },
    true
  );

  document.addEventListener(
    "close",
    (event) => {
      const el = event.target;
      if (!(el instanceof HTMLDialogElement)) return;
      if (el.id !== "topic-filters-dialog") return;
      const trigger = document.querySelector("[data-open-topic-filters]");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
    },
    true
  );

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const panel = document.getElementById("discover-panel");
    if (panel && panel.classList.contains("is-open")) {
      event.preventDefault();
      closeDiscoverSheet();
    }
  });
})();
