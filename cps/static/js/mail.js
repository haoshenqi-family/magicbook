/* Site mail state and inbox controller (R243).
 *
 * Why one module owns unread state: the Buddy FAB, settings menu, drawer tab and
 * /mail page must never drift into separate counters. This module keeps one
 * in-memory snapshot, exposes a small read-only API, and renders all numeric
 * badges from that snapshot. It intentionally uses browser-memory state only.
 */
(function (window, document) {
  "use strict";

  var ENDPOINTS = {
    unread: "/ajax/mail/unread-count",
    page: "/ajax/mail/page",
    read: "/ajax/mail/read",
    readAll: "/ajax/mail/read-all"
  };
  var ACTION_LABELS = {
    "/buddy": "Open Buddies",
    "/achievements": "View achievements",
    "/credits": "View Credits",
    "/learning": "Open Daily Learning",
    "/mail": "Open Mail"
  };
  var state = {
    status: "idle",
    unreadCount: null,
    lastKnownUnreadCount: null,
    error: null,
    lastUpdatedAt: null
  };
  var listeners = [];
  var requestSeq = 0;
  var appliedSeq = 0;
  var unreadPromise = null;
  var lastRefreshAt = 0;
  var pageLoadSeq = 0;
  var currentPage = 1;
  var pageSize = 20;
  var currentPageData = null;

  function t(id) {
    return typeof window.mbT === "function" ? window.mbT(id) : id;
  }

  function snapshot() {
    return {
      status: state.status,
      unreadCount: state.unreadCount,
      lastKnownUnreadCount: state.lastKnownUnreadCount,
      error: state.error,
      lastUpdatedAt: state.lastUpdatedAt
    };
  }

  function notify() {
    renderSharedBadges();
    listeners.slice().forEach(function (listener) {
      try { listener(snapshot()); } catch (e) { /* listener errors must not stop siblings */ }
    });
  }

  function setStatus(status, error) {
    state.status = status;
    state.error = error || null;
    if (status === "error") state.unreadCount = null;
    notify();
  }

  function normalizeCount(value) {
    var n = Number(value);
    if (!isFinite(n) || n < 0 || Math.floor(n) !== n) {
      throw new Error(t("Mail returned an invalid unread count"));
    }
    return n;
  }

  function applyCount(seq, value) {
    if (seq < appliedSeq) return;
    var count = normalizeCount(value);
    appliedSeq = seq;
    state.status = "ready";
    state.unreadCount = count;
    state.lastKnownUnreadCount = count;
    state.error = null;
    state.lastUpdatedAt = Date.now();
    notify();
  }

  function applyFailure(seq, error) {
    if (seq < appliedSeq) return;
    appliedSeq = seq;
    setStatus("error", errorMessage(error));
  }

  function errorMessage(error) {
    if (!error) return t("Mail is temporarily unavailable");
    return String(error.message || error || t("Mail is temporarily unavailable"));
  }

  function responseMessage(response) {
    var data = response && response.data;
    if (data && typeof data === "object") {
      return String(data.message || data.error || "").trim();
    }
    return "";
  }

  function unwrapResponse(response, fallback) {
    if (!response || !response.ok) {
      throw new Error(responseMessage(response) || fallback + " (" +
        ((response && response.status) || "network") + ")");
    }
    if (!response.data || response.data.success !== true) {
      throw new Error(responseMessage(response) || fallback);
    }
    return response.data.result;
  }

  function getJson(url) {
    if (!window.MBApi || typeof window.MBApi.httpJson !== "function") {
      return Promise.reject(new Error(t("The shared API helper is unavailable")));
    }
    return window.MBApi.httpJson(url, { credentials: "same-origin" });
  }

  function postJson(url, body) {
    if (!window.MBApi || typeof window.MBApi.csrfToken !== "function" ||
        typeof window.MBApi.httpJson !== "function") {
      return Promise.reject(new Error(t("The shared API helper is unavailable")));
    }
    var csrf = window.MBApi.csrfToken();
    if (!csrf) {
      return Promise.reject(new Error(t("Your session has expired. Please sign in again.")));
    }
    return window.MBApi.httpJson(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify(body || {})
    });
  }

  function refreshUnread() {
    var now = Date.now();
    if (unreadPromise) return unreadPromise;
    // Initial load, focus, visibility and pageshow can fire together on bfcache
    // restoration. Keep one request and avoid a second call inside one second.
    if (now - lastRefreshAt < 1000) {
      return Promise.resolve(state.unreadCount === null
        ? getUnreadForRouting() : state.unreadCount);
    }
    lastRefreshAt = now;
    var seq = ++requestSeq;
    setStatus("loading");
    unreadPromise = getJson(ENDPOINTS.unread).then(function (response) {
      var result = unwrapResponse(response, t("Failed to load unread mail count"));
      var count = result && typeof result === "object" ? result.count : result;
      applyCount(seq, count);
      return normalizeCount(count);
    }).catch(function (error) {
      applyFailure(seq, error);
      throw error;
    });
    function clearPending() { unreadPromise = null; }
    unreadPromise.then(clearPending, clearPending);
    return unreadPromise;
  }

  function normalizePage(result, requestedPage, requestedSize) {
    if (!result || typeof result !== "object" || !Array.isArray(result.records)) {
      throw new Error(t("Mail returned an invalid page"));
    }
    var records = result.records.slice().sort(function (a, b) {
      return (Number(b && b.createdAt) || 0) - (Number(a && a.createdAt) || 0);
    });
    return {
      records: records,
      total: Math.max(0, Number(result.total) || 0),
      pageNo: Math.max(1, Number(result.pageNo) || requestedPage || 1),
      pageSize: Math.max(1, Number(result.pageSize) || requestedSize || 20),
      unreadCount: result.unreadCount === undefined ? null : result.unreadCount
    };
  }

  function loadPage(pageNo, requestedPageSize) {
    var wantedPage = Math.max(1, parseInt(pageNo, 10) || 1);
    var wantedSize = Math.max(1, Math.min(50, parseInt(requestedPageSize, 10) || 20));
    var seq = ++requestSeq;
    var url = ENDPOINTS.page + "?pageNo=" + encodeURIComponent(wantedPage) +
      "&pageSize=" + encodeURIComponent(wantedSize);
    return getJson(url).then(function (response) {
      var result = unwrapResponse(response, t("Failed to load mail"));
      var page = normalizePage(result, wantedPage, wantedSize);
      if (page.unreadCount !== null) applyCount(seq, page.unreadCount);
      return page;
    });
  }

  function markRead(id) {
    var seq = ++requestSeq;
    return postJson(ENDPOINTS.read, { id: id }).then(function (response) {
      var result = unwrapResponse(response, t("Failed to mark mail as read"));
      if (result && result.unreadCount !== undefined) {
        applyCount(seq, result.unreadCount);
      }
      return result || {};
    });
  }

  function markAllRead() {
    var seq = ++requestSeq;
    return postJson(ENDPOINTS.readAll, {}).then(function (response) {
      var result = unwrapResponse(response, t("Failed to mark all mail as read"));
      if (result && result.unreadCount !== undefined) {
        applyCount(seq, result.unreadCount);
      }
      return result || {};
    });
  }

  function getUnreadForRouting() {
    if ($isNumber(state.unreadCount)) return state.unreadCount;
    if ($isNumber(state.lastKnownUnreadCount)) return state.lastKnownUnreadCount;
    return 0;
  }

  function $isNumber(value) {
    return typeof value === "number" && isFinite(value) && value >= 0;
  }

  function subscribe(listener) {
    if (typeof listener !== "function") return function () {};
    listeners.push(listener);
    try { listener(snapshot()); } catch (e) { /* caller owns its rendering errors */ }
    return function () {
      var i = listeners.indexOf(listener);
      if (i >= 0) listeners.splice(i, 1);
    };
  }

  function getState() {
    return snapshot();
  }

  function openInbox() {
    window.location.href = (window.__mbBasePath || "") + "/mail";
  }

  function text(value) {
    return value === null || value === undefined ? "" : String(value);
  }

  function params(mail) {
    return mail && mail.params && typeof mail.params === "object" ? mail.params : {};
  }

  function isUnread(mail) {
    return !!mail && !mail.readAt && !mail.resolvedAt;
  }

  function safeActionPath(path) {
    return Object.prototype.hasOwnProperty.call(ACTION_LABELS, path) ? path : "";
  }

  function replaceTokens(template, values) {
    return String(template).replace(/\{([A-Za-z0-9_]+)\}/g, function (_, key) {
      return Object.prototype.hasOwnProperty.call(values, key)
        ? text(values[key]) : "{" + key + "}";
    });
  }

  function describeMail(mail) {
    var p = params(mail);
    var title = t("Notification");
    var body = "";
    if (mail && mail.mailType === "BUDDY_CLAIMABLE") {
      title = t("New buddy visit");
      body = p.buddyName
        ? replaceTokens(t("{name} is waiting for you. Visit Buddies to claim them."),
          { name: p.buddyName })
        : t("A new buddy is waiting for you. Visit Buddies to claim them.");
    } else if (mail && mail.mailType === "ACHIEVEMENT_UNLOCKED") {
      title = t("Achievement unlocked");
      if (p.achievementName) {
        body = replaceTokens(t("You unlocked “{name}”."), { name: p.achievementName });
        if (p.description) body += " " + text(p.description);
        if (p.points !== undefined && p.points !== null && p.points !== "") {
          body += " " + replaceTokens(t("+{points} XP"), { points: p.points });
        }
      } else {
        body = t("You unlocked a new achievement.");
      }
    } else if (mail && mail.mailType === "CREDIT_GRANTED") {
      title = t("Credits received");
      if (p.amount !== undefined && p.balanceAfter !== undefined) {
        body = replaceTokens(t("{amount} credits were added. Current balance: {balance}."),
          { amount: p.amount, balance: p.balanceAfter });
      } else {
        body = t("Credits were added to your account.");
      }
    } else if (mail && mail.mailType === "ADMIN_ANNOUNCEMENT") {
      title = text(mail.title).trim() || t("Announcement");
      // Why 留空：运营邮件的正文是必填事实，缺失时不能伪装成一条通用公告。
      body = "";
    } else {
      body = t("You have a new notification.");
    }
    var custom = text(mail && mail.customMessage).trim();
    if (custom) body = custom;
    var actionPath = safeActionPath(mail && mail.actionPath);
    return {
      title: title,
      body: body,
      actionPath: actionPath,
      actionLabel: actionPath ? t(ACTION_LABELS[actionPath]) : "",
      unread: isUnread(mail),
      resolved: !!(mail && mail.resolvedAt)
    };
  }

  function formatDate(value) {
    var ms = Number(value);
    if (!isFinite(ms) || ms <= 0) return "";
    try {
      return new Date(ms).toLocaleString();
    } catch (e) {
      return "";
    }
  }

  function element(tag, className, value) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = value;
    return node;
  }

  function showItemError(item, message) {
    var error = item.querySelector(".mail-item-error");
    if (!error) {
      error = element("p", "mail-item-error");
      error.setAttribute("role", "alert");
      item.appendChild(error);
    }
    error.textContent = text(message);
  }

  function buildMailItem(mail, options) {
    var opts = options || {};
    var view = describeMail(mail);
    var article = element("article", "mail-item" + (opts.compact ? " mail-item-compact" : ""));
    article.setAttribute("data-mail-id", text(mail && mail.id));
    article.classList.toggle("is-unread", view.unread);
    article.classList.toggle("is-resolved", view.resolved);

    var summary = element("button", "mail-item-summary");
    summary.type = "button";
    summary.setAttribute("aria-expanded", "false");

    var main = element("span", "mail-item-main");
    var titleRow = element("span", "mail-item-title-row");
    var dot = element("span", "mail-unread-dot");
    dot.setAttribute("aria-hidden", "true");
    dot.hidden = !view.unread;
    titleRow.appendChild(dot);
    titleRow.appendChild(element("span", "mail-item-title", view.title));
    if (view.resolved) {
      titleRow.appendChild(element("span", "mail-resolved-label", t("Completed")));
    }
    main.appendChild(titleRow);
    main.appendChild(element("span", "mail-item-preview", view.body));
    main.appendChild(element("span", "mail-item-time", formatDate(mail && mail.createdAt)));
    summary.appendChild(main);

    var body = element("div", "mail-item-body");
    body.hidden = true;
    body.appendChild(element("p", "mail-item-copy", view.body));
    if (view.actionPath) {
      var action = element("a", "mail-action", view.actionLabel);
      action.href = view.actionPath;
      body.appendChild(action);
    }
    article.appendChild(summary);
    article.appendChild(body);

    function setRead(readAt) {
      if (!mail) return;
      if (!mail.readAt) mail.readAt = readAt || Date.now();
      article.classList.remove("is-unread");
      dot.hidden = true;
      var error = article.querySelector(".mail-item-error");
      if (error && error.parentNode) error.parentNode.removeChild(error);
    }

    summary.addEventListener("click", function () {
      var opening = body.hidden;
      body.hidden = !opening;
      summary.setAttribute("aria-expanded", opening ? "true" : "false");
      article.classList.toggle("is-open", opening);
      if (opening && typeof opts.onOpen === "function") {
        opts.onOpen(mail, itemApi);
      }
    });

    if (opts.expanded) {
      body.hidden = false;
      summary.setAttribute("aria-expanded", "true");
      article.classList.add("is-open");
    }

    var itemApi = {
      element: article,
      setRead: setRead,
      setError: function (message) { showItemError(article, message); },
      view: view
    };
    return itemApi;
  }

  function setBadge(id, stateSnapshot, kind) {
    var badge = document.getElementById(id);
    if (!badge) return;
    var count = stateSnapshot.unreadCount;
    var show = stateSnapshot.status === "ready" && $isNumber(count) && count > 0;
    badge.hidden = !show;
    badge.textContent = show ? String(count) : "";
    badge.classList.toggle("mail-unavailable", stateSnapshot.status === "error");
    if (show) {
      badge.setAttribute("aria-label",
        replaceTokens(t("{count} unread mail"), { count: count }));
    } else {
      badge.removeAttribute("aria-label");
    }
    if (kind === "tab") {
      var tab = document.getElementById("ai-tab-mail");
      if (tab) {
        tab.classList.toggle("has-mail", show);
        tab.classList.toggle("mail-unavailable", stateSnapshot.status === "error");
      }
    }
  }

  function setActionability(id) {
    var button = document.getElementById(id);
    if (!button) return;
    var localLoading = false;
    if (id === "mail-mark-all") {
      var loading = document.getElementById("mail-page-loading");
      localLoading = !!(loading && !loading.hidden);
    }
    button.disabled = localLoading || !(state.status === "ready" &&
      $isNumber(state.unreadCount) && state.unreadCount > 0);
  }

  function renderSharedBadges() {
    setBadge("top-mail-badge", state, "settings");
    setBadge("ai-tab-mail-badge", state, "tab");

    var fabBadge = document.getElementById("ai-companion-mail-badge");
    if (fabBadge) {
      var hasMail = $isNumber(state.lastKnownUnreadCount) &&
        state.lastKnownUnreadCount > 0;
      fabBadge.hidden = !hasMail;
      fabBadge.classList.toggle("mail-unavailable", state.status === "error");
      var fab = document.getElementById("ai-companion-fab");
      if (fab) {
        fab.classList.toggle("has-mail", hasMail);
        fab.classList.toggle("mail-unavailable", state.status === "error");
      }
      if (window.AICompanion && typeof window.AICompanion.syncLetterBadge === "function") {
        window.AICompanion.syncLetterBadge();
      }
    }

    var topMail = document.getElementById("top_mail");
    if (topMail) topMail.classList.toggle("mail-unavailable", state.status === "error");

    ["ai-mail-unread-count", "mail-page-unread-count"].forEach(function (id) {
      var node = document.getElementById(id);
      if (!node) return;
      node.classList.toggle("mail-unavailable", state.status === "error");
      if (state.status === "error") {
        node.textContent = t("Mail status unavailable");
      } else if (state.status === "loading" || state.status === "idle") {
        node.textContent = t("Checking mail...");
      } else if (state.unreadCount > 0) {
        node.textContent = replaceTokens(t("{count} unread"), { count: state.unreadCount });
      } else {
        node.textContent = t("No unread mail");
      }
    });
    setActionability("ai-mail-mark-all");
    setActionability("mail-mark-all");
  }

  function showPageState(mode, message) {
    var loading = document.getElementById("mail-page-loading");
    var empty = document.getElementById("mail-page-empty");
    var error = document.getElementById("mail-page-error");
    var list = document.getElementById("mail-page-list");
    var pager = document.getElementById("mail-page-pager");
    if (!loading || !empty || !error || !list || !pager) return;
    loading.hidden = mode !== "loading";
    empty.hidden = mode !== "empty";
    error.hidden = mode !== "error";
    list.hidden = mode !== "list";
    pager.hidden = mode !== "list";
    if (mode === "error") {
      var textNode = error.querySelector(".mail-page-error-text");
      if (textNode) textNode.textContent = text(message);
    }
  }

  function renderPagePager(page) {
    var totalPages = Math.max(1, Math.ceil(page.total / Math.max(1, page.pageSize)));
    var label = document.getElementById("mail-page-indicator");
    var prev = document.getElementById("mail-page-prev");
    var next = document.getElementById("mail-page-next");
    if (label) {
      label.textContent = replaceTokens(t("Page {page} of {total}"),
        { page: page.pageNo, total: totalPages });
    }
    if (prev) prev.disabled = page.pageNo <= 1;
    if (next) next.disabled = page.pageNo >= totalPages;
  }

  function renderPageData(page) {
    var list = document.getElementById("mail-page-list");
    if (!list) return;
    list.textContent = "";
    page.records.forEach(function (mail) {
      var item = buildMailItem(mail, {
        onOpen: function (mailData, itemApi) {
          if (!isUnread(mailData)) return;
          markRead(mailData.id).then(function (result) {
            itemApi.setRead(result.readAt);
          }).catch(function (error) {
            itemApi.setError(errorMessage(error));
          });
        }
      });
      list.appendChild(item.element);
    });
    if (!page.records.length) {
      showPageState("empty");
      renderSharedBadges();
      return;
    }
    showPageState("list");
    renderPagePager(page);
    renderSharedBadges();
  }

  function loadInboxPage(pageNo) {
    var seq = ++pageLoadSeq;
    currentPage = Math.max(1, parseInt(pageNo, 10) || 1);
    showPageState("loading");
    renderSharedBadges();
    loadPage(currentPage, pageSize).then(function (page) {
      if (seq !== pageLoadSeq) return;
      currentPageData = page;
      renderPageData(page);
    }).catch(function (error) {
      if (seq !== pageLoadSeq) return;
      showPageState("error", errorMessage(error));
      renderSharedBadges();
    });
  }

  function initPage() {
    var pageRoot = document.getElementById("mail-page");
    if (!pageRoot) return;
    var prev = document.getElementById("mail-page-prev");
    var next = document.getElementById("mail-page-next");
    var retry = document.getElementById("mail-page-retry");
    var markAll = document.getElementById("mail-mark-all");
    if (prev) prev.addEventListener("click", function () { loadInboxPage(currentPage - 1); });
    if (next) next.addEventListener("click", function () { loadInboxPage(currentPage + 1); });
    if (retry) retry.addEventListener("click", function () { loadInboxPage(currentPage); });
    if (markAll) {
      markAll.addEventListener("click", function () {
        markAll.disabled = true;
        markAllRead().then(function () {
          if (!currentPageData) return;
          currentPageData.records.forEach(function (mail) {
            if (!mail.readAt && !mail.resolvedAt) mail.readAt = Date.now();
          });
          renderPageData(currentPageData);
        }).catch(function (error) {
          showPageState("error", errorMessage(error));
          renderSharedBadges();
        });
      });
    }
    loadInboxPage(1);
  }

  function init() {
    renderSharedBadges();
    if (document.getElementById("top-mail-badge") ||
        document.getElementById("ai-companion-mail-badge") ||
        document.getElementById("ai-mail-pane") ||
        document.getElementById("mail-page")) {
      refreshUnread().catch(function () { /* explicit UI states consume the same error */ });
    }
    initPage();

    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) refreshUnread().catch(function () {});
    });
    window.addEventListener("focus", function () {
      refreshUnread().catch(function () {});
    });
    window.addEventListener("pageshow", function () {
      refreshUnread().catch(function () {});
    });
  }

  window.MBMail = {
    refreshUnread: refreshUnread,
    loadPage: loadPage,
    markRead: markRead,
    markAllRead: markAllRead,
    openInbox: openInbox,
    subscribe: subscribe,
    getState: getState,
    getUnreadForRouting: getUnreadForRouting,
    describeMail: describeMail,
    safeActionPath: safeActionPath,
    isUnread: isUnread,
    buildMailItem: buildMailItem,
    formatDate: formatDate
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}(window, document));
