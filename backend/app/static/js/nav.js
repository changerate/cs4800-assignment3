(() => {
  const isModifiedClick = (event) =>
    event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;

  const canHandleLink = (anchor) => {
    if (!anchor || !anchor.href) return false;
    if (anchor.dataset && anchor.dataset.relatedModal === "true") return false;
    if (anchor.target && anchor.target !== "_self") return false;
    if (anchor.hasAttribute("download")) return false;
    const nextUrl = new URL(anchor.href, window.location.href);
    if (nextUrl.origin !== window.location.origin) return false;
    if (nextUrl.hash && nextUrl.pathname === window.location.pathname && nextUrl.search === window.location.search) {
      return false;
    }
    return true;
  };

  const htmlCache = new Map();
  let inFlightController = null;

  const setBusy = (isBusy) => {
    document.body.classList.toggle("is-nav-loading", isBusy);
  };

  const fetchHtml = async (url) => {
    const key = url.toString();
    if (htmlCache.has(key)) return htmlCache.get(key);
    const response = await fetch(key, {
      headers: { "X-Requested-With": "spa-nav" },
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error(`Navigation failed: ${response.status}`);
    const html = await response.text();
    htmlCache.set(key, html);
    return html;
  };

  const replaceShellFromHtml = (html) => {
    const nextDoc = new DOMParser().parseFromString(html, "text/html");
    const nextShell = nextDoc.querySelector(".shell");
    const currentShell = document.querySelector(".shell");
    if (!nextShell || !currentShell) return false;
    currentShell.replaceWith(nextShell);
    const nextTitle = nextDoc.querySelector("title");
    if (nextTitle) document.title = nextTitle.textContent || document.title;
    return true;
  };

  const navigateTo = async (url, shouldPushState = true) => {
    if (inFlightController) inFlightController.abort();
    inFlightController = new AbortController();
    setBusy(true);
    try {
      const html = await fetchHtml(url);
      if (replaceShellFromHtml(html) && shouldPushState) {
        window.history.pushState({}, "", url);
      }
    } catch (error) {
      // Fall back to native navigation for robustness.
      window.location.assign(url);
    } finally {
      setBusy(false);
      inFlightController = null;
    }
  };

  let relatedBackdrop = null;
  let relatedOnKeyDown = null;

  const closeRelatedModal = () => {
    if (!relatedBackdrop) return;
    const toRemove = relatedBackdrop;
    toRemove.classList.remove("is-open");
    relatedBackdrop = null;
    document.body.classList.remove("related-modal-open");
    if (relatedOnKeyDown) {
      document.removeEventListener("keydown", relatedOnKeyDown);
      relatedOnKeyDown = null;
    }
    window.setTimeout(() => {
      toRemove?.remove();
    }, 240);
  };

  const openRelatedModal = async (url) => {
    if (relatedBackdrop) closeRelatedModal();

    relatedBackdrop = document.createElement("div");
    relatedBackdrop.className = "related-backdrop";
    relatedBackdrop.setAttribute("role", "dialog");
    relatedBackdrop.setAttribute("aria-modal", "true");

    const panel = document.createElement("div");
    panel.className = "related-panel";
    panel.addEventListener("click", (e) => e.stopPropagation());

    relatedBackdrop.appendChild(panel);
    document.body.appendChild(relatedBackdrop);

    document.body.classList.add("related-modal-open");

    // Click outside the panel closes.
    relatedBackdrop.addEventListener("click", (e) => {
      if (e.target === relatedBackdrop) closeRelatedModal();
    });

    // ESC closes.
    relatedOnKeyDown = (e) => {
      if (e.key === "Escape") closeRelatedModal();
    };
    document.addEventListener("keydown", relatedOnKeyDown);

    window.requestAnimationFrame(() => relatedBackdrop.classList.add("is-open"));

    panel.innerHTML =
      '<div class="empty-state muted" style="padding: 1.25rem 0;">Loading related feed…</div>';

    try {
      const html = await fetchHtml(url);
      const nextDoc = new DOMParser().parseFromString(html, "text/html");
      const nextMain = nextDoc.querySelector(".feed-main");

      if (!nextMain) {
        panel.innerHTML = '<div class="empty-state muted">No related content.</div>';
        return;
      }

      panel.innerHTML = "";
      // Clone so we don't move nodes out of the parsed document.
      const clonedMain = nextMain.cloneNode(true);
      clonedMain.classList.add("related-feed");
      panel.appendChild(clonedMain);
    } catch (error) {
      panel.innerHTML =
        '<div class="empty-state muted">Failed to load related feed. Please try again.</div>';
    }
  };

  document.addEventListener("click", (event) => {
    const anchor = event.target.closest("a");
    if (
      anchor &&
      anchor.dataset &&
      anchor.dataset.relatedModal === "true" &&
      !isModifiedClick(event)
    ) {
      event.preventDefault();
      event.stopImmediatePropagation();
      openRelatedModal(anchor.href);
      return;
    }
    if (!anchor || isModifiedClick(event) || !canHandleLink(anchor)) return;
    event.preventDefault();
    navigateTo(anchor.href, true);
  });

  const prefetchLink = (anchor) => {
    if (!canHandleLink(anchor)) return;
    const url = new URL(anchor.href, window.location.href);
    fetchHtml(url).catch(() => {});
  };

  document.addEventListener(
    "mouseover",
    (event) => {
      const anchor = event.target.closest("a");
      if (anchor) prefetchLink(anchor);
    },
    { passive: true }
  );

  document.addEventListener(
    "focusin",
    (event) => {
      const anchor = event.target.closest("a");
      if (anchor) prefetchLink(anchor);
    },
    { passive: true }
  );

  window.addEventListener("popstate", () => {
    navigateTo(window.location.href, false);
  });

  const updateSaveFormUI = (form, isSaved) => {
    const button = form.querySelector("button[type='submit']");
    const icon = button?.querySelector("i");
    if (!button || !icon) return;

    form.dataset.saved = isSaved ? "true" : "false";
    if (isSaved) {
      form.action = form.action.replace(/\/save$/, "/unsave");
      button.setAttribute("aria-label", "Unsave paper");
      icon.className = "bi bi-bookmark-check-fill";
    } else {
      form.action = form.action.replace(/\/unsave$/, "/save");
      button.setAttribute("aria-label", "Save paper");
      icon.className = "bi bi-bookmark-plus";
    }
  };

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest("form.paper-save-form");
    if (!form) return;
    event.preventDefault();

    const button = form.querySelector("button[type='submit']");
    if (!button || button.disabled) return;

    const currentlySaved = form.dataset.saved === "true";
    button.disabled = true;
    button.classList.add("is-loading");

    try {
      const response = await fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-Requested-With": "spa-nav" },
      });

      if (response.redirected && response.url.includes("/auth")) {
        window.location.assign(response.url);
        return;
      }
      if (!response.ok) throw new Error(`Save toggle failed: ${response.status}`);

      const nextSaved = !currentlySaved;
      // Save state changed server-side; invalidate prefetched page cache so
      // Home/Saved/related views don't show stale paper lists.
      htmlCache.clear();
      updateSaveFormUI(form, nextSaved);

      if (!nextSaved && form.dataset.page === "saved") {
        const card = form.closest(".paper-card");
        card?.remove();
      }
    } catch (error) {
      HTMLFormElement.prototype.submit.call(form);
    } finally {
      button.disabled = false;
      button.classList.remove("is-loading");
    }
  });
})();
