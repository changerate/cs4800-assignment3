(() => {
  const SHOW_DELAY_MS = 1000;
  const HIDE_DELAY_MS = 160;

  let tip = null;
  let showTimer = null;
  let hideTimer = null;
  let activeTrigger = null;

  const getTip = () => {
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "paper-abstract-tooltip";
      tip.setAttribute("role", "tooltip");
      tip.hidden = true;
      document.body.appendChild(tip);
      tip.addEventListener("mouseenter", () => {
        if (hideTimer) {
          clearTimeout(hideTimer);
          hideTimer = null;
        }
      });
      tip.addEventListener("mouseleave", () => {
        if (hideTimer) clearTimeout(hideTimer);
        hideTimer = window.setTimeout(hide, HIDE_DELAY_MS);
      });
    }
    return tip;
  };

  const clearShowTimer = () => {
    if (showTimer) {
      clearTimeout(showTimer);
      showTimer = null;
    }
  };

  const clearHideTimer = () => {
    if (hideTimer) {
      clearTimeout(hideTimer);
      hideTimer = null;
    }
  };

  const hide = () => {
    clearShowTimer();
    clearHideTimer();
    const el = getTip();
    el.hidden = true;
    el.textContent = "";
    activeTrigger = null;
  };

  const position = (trigger, el) => {
    const r = trigger.getBoundingClientRect();
    const pad = 12;
    const maxW = Math.min(520, window.innerWidth - pad * 2);
    el.style.maxWidth = `${maxW}px`;
    const left = Math.max(pad, Math.min(r.left, window.innerWidth - maxW - pad));
    el.style.left = `${left}px`;
    const h = el.offsetHeight;
    const spaceBelow = window.innerHeight - r.bottom - pad;
    const spaceAbove = r.top - pad;
    if (spaceBelow >= Math.min(h + 12, 180) || spaceBelow >= spaceAbove) {
      el.style.top = `${Math.min(r.bottom + 10, window.innerHeight - h - pad)}px`;
    } else {
      el.style.top = `${Math.max(pad, r.top - h - 10)}px`;
    }
  };

  const show = (trigger) => {
    const raw = trigger.getAttribute("data-abstract");
    if (!raw || !raw.trim()) return;
    const el = getTip();
    el.textContent = raw.trim();
    el.hidden = false;
    activeTrigger = trigger;
    position(trigger, el);
    requestAnimationFrame(() => position(trigger, el));
  };

  const scheduleShow = (trigger) => {
    clearShowTimer();
    clearHideTimer();
    showTimer = window.setTimeout(() => show(trigger), SHOW_DELAY_MS);
  };

  document.addEventListener(
    "mouseover",
    (e) => {
      if (!window.matchMedia("(hover: hover)").matches) return;
      const tr = e.target.closest?.(".paper-title-hover");
      if (!tr) return;
      if (tr.contains(e.relatedTarget)) return;
      scheduleShow(tr);
    },
    true
  );

  document.addEventListener(
    "mouseout",
    (e) => {
      const tr = e.target.closest?.(".paper-title-hover");
      if (!tr || tr.contains(e.relatedTarget)) return;
      const tipEl = getTip();
      if (e.relatedTarget && tipEl.contains(e.relatedTarget)) return;
      clearShowTimer();
      if (!tipEl.hidden) {
        clearHideTimer();
        hideTimer = window.setTimeout(hide, HIDE_DELAY_MS);
      }
    },
    true
  );

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hide();
  });

  document.addEventListener("papershell:updated", hide);

  window.addEventListener(
    "scroll",
    () => {
      const el = getTip();
      if (!el.hidden && activeTrigger) position(activeTrigger, el);
    },
    true
  );

  window.addEventListener("resize", () => {
    const el = getTip();
    if (!el.hidden && activeTrigger) position(activeTrigger, el);
  });
})();
