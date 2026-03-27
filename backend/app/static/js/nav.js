(() => {
  // #region agent log
  const debugLog = (runId, hypothesisId, location, message, data) => {
    fetch("http://127.0.0.1:7787/ingest/61c4bf4a-d62c-4622-93b7-a084d32dbd83", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "61e6cf" },
      body: JSON.stringify({
        sessionId: "61e6cf",
        runId,
        hypothesisId,
        location,
        message,
        data,
        timestamp: Date.now(),
      }),
    }).catch(() => {});
  };
  // #endregion

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
  const inFlightHtml = new Map();
  const lastPrefetchAt = new Map();
  let inFlightController = null;

  const setBusy = (isBusy) => {
    document.body.classList.toggle("is-nav-loading", isBusy);
  };

  const fetchHtml = async (url, reason = "unknown") => {
    const parsedUrl = typeof url === "string" ? new URL(url, window.location.href) : url;
    const key = parsedUrl.toString();
    if (htmlCache.has(key)) return htmlCache.get(key);
    if (inFlightHtml.has(key)) return inFlightHtml.get(key);
    const startedAt = performance.now();
    const requestPromise = (async () => {
      const response = await fetch(key, {
        headers: { "X-Requested-With": "spa-nav" },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error(`Navigation failed: ${response.status}`);
      const html = await response.text();
      htmlCache.set(key, html);
      // #region agent log
      debugLog("post-fix", "H5", "nav.js:fetchHtml", "html fetch complete", {
        reason,
        path: parsedUrl.pathname + parsedUrl.search,
        elapsedMs: Math.round((performance.now() - startedAt) * 100) / 100,
        cacheSize: htmlCache.size,
      });
      // #endregion
      return html;
    })();
    inFlightHtml.set(key, requestPromise);
    try {
      return await requestPromise;
    } finally {
      inFlightHtml.delete(key);
    }
  };

  const shouldPrefetch = (url) => {
    const key = url.toString();
    if (htmlCache.has(key) || inFlightHtml.has(key)) return false;
    const now = Date.now();
    const lastAt = lastPrefetchAt.get(key) || 0;
    if (now - lastAt < 1200) return false;
    lastPrefetchAt.set(key, now);
    return true;
  };

  const pathFromAnchor = (anchor) => {
    const url = new URL(anchor.href, window.location.href);
    return url.pathname + url.search;
  };

  const isRepeatedHoverWithinSameAnchor = (event, anchor) => {
    const prev = event.relatedTarget;
    return !!prev && anchor.contains(prev);
  };

  const prefetchLink = (anchor) => {
    if (!canHandleLink(anchor)) return;
    const url = new URL(anchor.href, window.location.href);
    if (!shouldPrefetch(url)) return;
    // #region agent log
    debugLog("post-fix", "H5", "nav.js:prefetchLink", "prefetch requested", {
      path: pathFromAnchor(anchor),
    });
    // #endregion
    fetchHtml(url, "prefetch").catch(() => {});
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
      const html = await fetchHtml(url, "navigate");
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
      const html = await fetchHtml(url, "related-modal");
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

  document.addEventListener(
    "mouseover",
    (event) => {
      const anchor = event.target.closest("a");
      if (anchor && isRepeatedHoverWithinSameAnchor(event, anchor)) return;
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
    if (form.dataset.pending === "true") return;

    const currentlySaved = form.dataset.saved === "true";
    const nextSaved = !currentlySaved;
    const card = form.closest(".paper-card");
    const cardParent = card?.parentElement || null;
    const cardNextSibling = card?.nextSibling || null;

    form.dataset.pending = "true";
    button.disabled = true;
    button.classList.add("is-loading");

    // Optimistic UI: flip immediately so the interaction feels instant.
    updateSaveFormUI(form, nextSaved);
    if (!nextSaved && form.dataset.page === "saved") {
      card?.remove();
    }

    try {
      const saveStartedAt = performance.now();
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

      // Save state changed server-side; invalidate prefetched page cache so
      // Home/Saved/related views don't show stale paper lists.
      htmlCache.clear();
      // #region agent log
      debugLog("post-fix", "H5", "nav.js:saveSubmit", "save/unsave response complete", {
        actionPath: new URL(form.action, window.location.href).pathname,
        responseStatus: response.status,
        redirected: response.redirected,
        elapsedMs: Math.round((performance.now() - saveStartedAt) * 100) / 100,
      });
      debugLog("post-fix", "H5", "nav.js:saveSubmit", "cache invalidated after save toggle", {
        cacheSize: htmlCache.size,
        nextSaved,
      });
      // #endregion
    } catch (error) {
      // Roll back optimistic state on any error.
      updateSaveFormUI(form, currentlySaved);
      if (!nextSaved && form.dataset.page === "saved" && card && cardParent) {
        if (cardNextSibling && cardNextSibling.parentNode === cardParent) {
          cardParent.insertBefore(card, cardNextSibling);
        } else {
          cardParent.appendChild(card);
        }
      }
      HTMLFormElement.prototype.submit.call(form);
    } finally {
      form.dataset.pending = "false";
      button.disabled = false;
      button.classList.remove("is-loading");
    }
  });
})();
