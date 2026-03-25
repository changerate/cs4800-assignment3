(() => {
  const isModifiedClick = (event) =>
    event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;

  const canHandleLink = (anchor) => {
    if (!anchor || !anchor.href) return false;
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

  document.addEventListener("click", (event) => {
    const anchor = event.target.closest("a");
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
})();
