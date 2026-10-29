/* R250 administrator operation mail.
 *
 * The page owns only transient browser state. Recipient lists and message
 * content are deliberately never written to localStorage/sessionStorage.
 */
(function (window, document) {
  "use strict";

  var MAX_RECIPIENTS = 5000;
  var MAX_TITLE = 80;
  var MAX_BODY = 500;
  var PAGE_SIZE = 20;
  var ACTION_LABELS = {
    "/credits": "View Credits",
    "/buddy": "Open Buddies",
    "/achievements": "View achievements",
    "/learning": "Open Daily Learning",
    "/mail": "Open Mail"
  };
  var state = {
    audience: "SELECTED",
    audienceCount: null,
    audienceRequest: 0,
    selected: [],
    preview: null,
    sending: false,
    historyPage: 1,
    historyPageSize: PAGE_SIZE,
    historyData: null
  };

  function t(id) {
    return typeof window.mbT === "function" ? window.mbT(id) : id;
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function text(value) {
    return value === null || value === undefined ? "" : String(value);
  }

  function element(tag, className, value) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = value;
    return node;
  }

  function responseMessage(response) {
    var data = response && response.data;
    return data && typeof data === "object"
      ? text(data.message || data.error).trim() : "";
  }

  function unwrap(response, fallback) {
    if (!response || !response.ok) {
      throw new Error(responseMessage(response) || fallback + " (" +
        ((response && response.status) || "network") + ")");
    }
    if (!response.data || response.data.success !== true) {
      throw new Error(responseMessage(response) || fallback);
    }
    return response.data.result;
  }

  function requestJson(url, options) {
    if (!window.MBApi || typeof window.MBApi.httpJson !== "function") {
      return Promise.reject(new Error(t("The shared API helper is unavailable")));
    }
    return window.MBApi.httpJson(url, options || { credentials: "same-origin" });
  }

  function postJson(url, body) {
    var csrf = window.MBApi && typeof window.MBApi.csrfToken === "function"
      ? window.MBApi.csrfToken() : "";
    if (!csrf) {
      return Promise.reject(new Error(
        t("Your session has expired. Please sign in again.")));
    }
    return requestJson(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify(body || {})
    });
  }

  function showAlert(message) {
    var alert = byId("admin-mail-alert");
    if (!alert) return;
    alert.textContent = text(message);
    alert.hidden = !message;
  }

  function showHistoryError(message) {
    var error = byId("admin-mail-history-error");
    if (!error) return;
    error.textContent = text(message);
    error.hidden = !message;
  }

  function selectedIndex(userId) {
    for (var i = 0; i < state.selected.length; i += 1) {
      if (state.selected[i].userId === userId) return i;
    }
    return -1;
  }

  function addRecipient(user) {
    if (!user || !Number.isInteger(user.userId) || user.userId <= 0) return;
    if (selectedIndex(user.userId) >= 0) return;
    if (state.selected.length >= MAX_RECIPIENTS) {
      showAlert(t("At most 5000 recipients per send"));
      return;
    }
    state.selected.push({
      userId: user.userId,
      username: text(user.username),
      nickname: text(user.nickname),
      email: text(user.email)
    });
    renderRecipients();
    invalidatePreview();
  }

  function removeRecipient(userId) {
    var index = selectedIndex(userId);
    if (index < 0) return;
    state.selected.splice(index, 1);
    renderRecipients();
    invalidatePreview();
  }

  function renderRecipients() {
    var list = byId("admin-mail-recipients");
    var count = byId("admin-mail-selected-count");
    if (count) count.textContent = String(state.selected.length);
    if (!list) return;
    list.textContent = "";
    if (!state.selected.length) {
      list.appendChild(element("p", "admin-mail-empty",
        t("No recipients selected yet.")));
      return;
    }
    state.selected.forEach(function (user) {
      var row = element("div", "admin-mail-recipient");
      var label = user.nickname || user.username || ("#" + user.userId);
      var detail = [("#" + user.userId), user.username, user.email]
        .filter(function (value) { return !!value; }).join(" · ");
      row.appendChild(element("span", "admin-mail-recipient-name", label));
      row.appendChild(element("span", "admin-mail-recipient-detail", detail));
      var remove = element("button", "admin-mail-remove", t("Remove"));
      remove.type = "button";
      remove.setAttribute("aria-label",
        t("Remove {name}").replace("{name}", label));
      remove.addEventListener("click", function () { removeRecipient(user.userId); });
      row.appendChild(remove);
      list.appendChild(row);
    });
  }

  function renderUserResults(users) {
    var results = byId("admin-mail-user-results");
    if (!results) return;
    results.textContent = "";
    if (!users.length) {
      results.appendChild(element("p", "admin-mail-empty", t("No matching users.")));
      return;
    }
    users.forEach(function (user) {
      var row = element("div", "admin-mail-user-result");
      var label = user.nickname || user.username || ("#" + user.userId);
      var detail = [("#" + user.userId), user.username, user.email]
        .filter(function (value) { return !!value; }).join(" · ");
      row.appendChild(element("span", "admin-mail-user-result-name", label));
      row.appendChild(element("span", "admin-mail-user-result-detail", detail));
      var add = element("button", "admin-mail-add", t("Add"));
      add.type = "button";
      add.disabled = selectedIndex(user.userId) >= 0;
      add.addEventListener("click", function () { addRecipient(user); });
      row.appendChild(add);
      results.appendChild(row);
    });
  }

  function searchUsers() {
    var input = byId("admin-mail-user-search");
    var results = byId("admin-mail-user-results");
    var keyword = input ? input.value.trim() : "";
    if (results) {
      results.textContent = "";
      results.appendChild(element("p", "admin-mail-empty", t("Searching users...")));
    }
    return requestJson("/ajax/admin-mail/users?keyword=" +
      encodeURIComponent(keyword) + "&limit=100").then(function (response) {
      var users = unwrap(response, t("Failed to load users"));
      if (!Array.isArray(users)) throw new Error(t("Users returned an invalid response"));
      renderUserResults(users);
    }).catch(function (error) {
      showAlert(error.message);
      if (results) {
        results.textContent = "";
        results.appendChild(element("p", "admin-mail-empty",
          t("Users are temporarily unavailable.")));
      }
    });
  }

  function setAudience(audience) {
    state.audience = audience === "ALL" ? "ALL" : "SELECTED";
    state.audienceCount = null;
    state.audienceRequest += 1;
    var selected = byId("admin-mail-selected");
    var hint = byId("admin-mail-all-hint");
    if (selected) selected.hidden = state.audience === "ALL";
    if (hint) hint.hidden = state.audience !== "ALL";
    renderAudiencePill();
    if (state.audience === "ALL") loadAudienceCount();
    invalidatePreview();
  }

  function renderAudiencePill() {
    var audiencePill = byId("admin-mail-preview-audience");
    if (!audiencePill) return;
    if (state.audience === "SELECTED") {
      audiencePill.textContent = String(state.selected.length) + " " + t("selected");
    } else if (state.audienceCount === null) {
      audiencePill.textContent = t("Loading...");
    } else {
      audiencePill.textContent = String(state.audienceCount) + " " + t("recipients");
    }
  }

  function loadAudienceCount() {
    var requestId = state.audienceRequest;
    return requestJson("/ajax/admin-mail/audience-count").then(function (response) {
      var count = unwrap(response, t("Failed to load audience"));
      if (!Number.isInteger(count) || count < 0) {
        throw new Error(t("Audience returned an invalid response"));
      }
      if (state.audience !== "ALL" || requestId !== state.audienceRequest) return;
      state.audienceCount = count;
      renderAudiencePill();
    }).catch(function (error) {
      if (state.audience !== "ALL" || requestId !== state.audienceRequest) return;
      showAlert(error.message);
      state.audienceCount = null;
      renderAudiencePill();
    });
  }

  function updateCounters() {
    var title = byId("admin-mail-title");
    var body = byId("admin-mail-body");
    var titleCount = byId("admin-mail-title-count");
    var bodyCount = byId("admin-mail-body-count");
    if (titleCount) titleCount.textContent = title.value.length + " / " + MAX_TITLE;
    if (bodyCount) bodyCount.textContent = body.value.length + " / " + MAX_BODY;
  }

  function buildPreview() {
    var titleInput = byId("admin-mail-title");
    var bodyInput = byId("admin-mail-body");
    var actionInput = byId("admin-mail-action");
    var title = titleInput.value.trim();
    var body = bodyInput.value.trim();
    var actionPath = actionInput.value;
    if (state.audience === "SELECTED" && !state.selected.length) {
      return { error: t("Select at least one user") };
    }
    if (state.audience === "SELECTED" && state.selected.length > MAX_RECIPIENTS) {
      return { error: t("At most 5000 recipients per send") };
    }
    if (state.audience === "ALL" && state.audienceCount === null) {
      return { error: t("Audience count is unavailable. Please try again.") };
    }
    if (state.audience === "ALL" && state.audienceCount > MAX_RECIPIENTS) {
      return { error: t("At most 5000 recipients per send") };
    }
    if (!title) return { error: t("Title is required") };
    if (title.length > MAX_TITLE) {
      return { error: t("Title must be at most 80 characters") };
    }
    if (!body) return { error: t("Message body is required") };
    if (body.length > MAX_BODY) {
      return { error: t("Message body must be at most 500 characters") };
    }
    if (actionPath && !ACTION_LABELS[actionPath]) {
      return { error: t("Invalid destination") };
    }
    return {
      audienceType: state.audience,
      userIds: state.audience === "SELECTED"
        ? state.selected.map(function (user) { return user.userId; }) : [],
      title: title,
      body: body,
      actionPath: actionPath
    };
  }

  function invalidatePreview() {
    state.preview = null;
    var content = byId("admin-mail-preview-content");
    var empty = byId("admin-mail-preview-empty");
    var send = byId("admin-mail-send");
    if (content) content.hidden = true;
    if (empty) empty.hidden = false;
    if (send) send.disabled = true;
    renderAudiencePill();
  }

  function showPreview(preview) {
    state.preview = preview;
    var content = byId("admin-mail-preview-content");
    var empty = byId("admin-mail-preview-empty");
    var title = byId("admin-mail-preview-title-text");
    var body = byId("admin-mail-preview-body-text");
    var action = byId("admin-mail-preview-action");
    var audience = byId("admin-mail-preview-audience");
    var send = byId("admin-mail-send");
    if (title) title.textContent = preview.title;
    if (body) body.textContent = preview.body;
    if (action) {
      action.textContent = preview.actionPath
        ? t(ACTION_LABELS[preview.actionPath]) : "";
      action.hidden = !preview.actionPath;
    }
    if (audience) {
      audience.textContent = preview.audienceType === "ALL"
        ? String(state.audienceCount) + " " + t("recipients")
        : preview.userIds.length + " " + t("recipients");
    }
    if (content) content.hidden = false;
    if (empty) empty.hidden = true;
    if (send) send.disabled = false;
  }

  function preview() {
    showAlert("");
    var built = buildPreview();
    if (built.error) {
      showAlert(built.error);
      invalidatePreview();
      return;
    }
    showPreview(built);
  }

  function confirmSend(previewData) {
    var audience = previewData.audienceType === "ALL"
      ? String(state.audienceCount) + " " + t("recipients")
      : String(previewData.userIds.length) + " " + t("recipients");
    return window.confirm(t("Send this announcement to {audience}? You can recall the whole batch later, but recipients may already see it.")
      .replace("{audience}", audience));
  }

  function send() {
    if (state.sending || !state.preview) return;
    if (!confirmSend(state.preview)) return;
    var button = byId("admin-mail-send");
    state.sending = true;
    if (button) {
      button.disabled = true;
      button.textContent = t("Sending...");
    }
    showAlert("");
    postJson("/ajax/admin-mail/send", state.preview).then(function (response) {
      var result = unwrap(response, t("Failed to send announcement"));
      showAlert(t("Sent to {target} users; {delivered} delivered. Campaign #{id}.")
        .replace("{target}", text(result.targetCount))
        .replace("{delivered}", text(result.deliveredCount))
        .replace("{id}", text(result.campaignId)));
      resetComposer();
      loadHistory(1);
    }).catch(function (error) {
      showAlert(error.message);
    }).finally(function () {
      state.sending = false;
      if (button) {
        button.disabled = !state.preview;
        button.textContent = t("Send announcement");
      }
    });
  }

  function resetComposer() {
    var title = byId("admin-mail-title");
    var body = byId("admin-mail-body");
    var action = byId("admin-mail-action");
    if (title) title.value = "";
    if (body) body.value = "";
    if (action) action.value = "";
    state.selected = [];
    state.audienceCount = null;
    state.audienceRequest += 1;
    renderRecipients();
    updateCounters();
    invalidatePreview();
    if (state.audience === "ALL") loadAudienceCount();
  }

  function historyStatus(mode, message) {
    var loading = byId("admin-mail-history-loading");
    var empty = byId("admin-mail-history-empty");
    var list = byId("admin-mail-history-list");
    var pager = byId("admin-mail-history-pager");
    if (loading) loading.hidden = mode !== "loading";
    if (empty) empty.hidden = mode !== "empty";
    if (list) list.hidden = mode !== "list";
    if (pager) pager.hidden = mode !== "list";
    if (mode === "error") showHistoryError(message);
    else showHistoryError("");
  }

  function formatDate(value) {
    var ms = Number(value);
    if (!isFinite(ms) || ms <= 0) return "";
    try { return new Date(ms).toLocaleString(); } catch (e) { return ""; }
  }

  function campaignStatus(campaign) {
    return campaign.recalledAt ? t("Recalled") : t("Sent");
  }

  function renderHistory(data) {
    var list = byId("admin-mail-history-list");
    if (!list) return;
    list.textContent = "";
    if (!data.records.length) {
      historyStatus("empty");
      return;
    }
    data.records.forEach(function (campaign) {
      var row = element("article", "admin-mail-history-row");
      var main = element("div", "admin-mail-history-main");
      var top = element("div", "admin-mail-history-top");
      top.appendChild(element("strong", "admin-mail-history-title",
        text(campaign.title)));
      top.appendChild(element("span", "admin-mail-history-status",
        campaignStatus(campaign)));
      main.appendChild(top);
      var meta = [
        formatDate(campaign.createdAt),
        campaign.audienceType === "ALL" ? t("All users") : t("Selected users"),
        t("Targets: {target} / delivered: {delivered}")
          .replace("{target}", text(campaign.targetCount))
          .replace("{delivered}", text(campaign.deliveredCount)),
        t("Operator #{id}").replace("{id}", text(campaign.operatorUserId))
      ].filter(function (value) { return !!value; }).join(" · ");
      main.appendChild(element("p", "admin-mail-history-meta", meta));
      main.appendChild(element("p", "admin-mail-history-body", text(campaign.body)));
      row.appendChild(main);
      if (!campaign.recalledAt) {
        var recall = element("button", "admin-mail-recall", t("Recall batch"));
        recall.type = "button";
        recall.addEventListener("click", function () {
          if (!window.confirm(t("Recall this whole batch? It disappears from inboxes and cannot be undone."))) return;
          recall.disabled = true;
          postJson("/ajax/admin-mail/recall", { campaignId: campaign.id })
            .then(function (response) {
              unwrap(response, t("Failed to recall campaign"));
              if (window.MBMail && typeof window.MBMail.refreshUnread === "function") {
                window.MBMail.refreshUnread().catch(function () {});
              }
              loadHistory(state.historyPage);
            }).catch(function (error) {
              showAlert(error.message);
              recall.disabled = false;
            });
        });
        row.appendChild(recall);
      }
      list.appendChild(row);
    });
    historyStatus("list");
  }

  function renderPager(data) {
    var totalPages = Math.max(1, Math.ceil(data.total / Math.max(1, data.pageSize)));
    var page = byId("admin-mail-history-page");
    var prev = byId("admin-mail-history-prev");
    var next = byId("admin-mail-history-next");
    if (page) {
      page.textContent = t("Page {page} of {total}")
        .replace("{page}", text(data.pageNo)).replace("{total}", text(totalPages));
    }
    if (prev) prev.disabled = data.pageNo <= 1;
    if (next) next.disabled = data.pageNo >= totalPages;
  }

  function loadHistory(pageNo) {
    var wanted = Math.max(1, parseInt(pageNo, 10) || 1);
    state.historyPage = wanted;
    historyStatus("loading");
    requestJson("/ajax/admin-mail/campaigns?pageNo=" + wanted +
      "&pageSize=" + state.historyPageSize).then(function (response) {
      var data = unwrap(response, t("Failed to load history"));
      if (!data || !Array.isArray(data.records)) {
        throw new Error(t("History returned an invalid response"));
      }
      state.historyData = data;
      renderHistory(data);
      if (data.records.length) renderPager(data);
    }).catch(function (error) {
      historyStatus("error", error.message);
    });
  }

  function init() {
    var root = byId("admin-mail-page");
    if (!root) return;
    var searchButton = byId("admin-mail-user-search-button");
    var searchInput = byId("admin-mail-user-search");
    var previewButton = byId("admin-mail-preview");
    var sendButton = byId("admin-mail-send");
    var refreshButton = byId("admin-mail-history-refresh");
    var prevButton = byId("admin-mail-history-prev");
    var nextButton = byId("admin-mail-history-next");
    var title = byId("admin-mail-title");
    var body = byId("admin-mail-body");
    Array.prototype.forEach.call(
      document.querySelectorAll('input[name="admin-mail-audience"]'),
      function (radio) {
        radio.addEventListener("change", function () {
          if (radio.checked) setAudience(radio.value);
        });
      });
    if (searchButton) searchButton.addEventListener("click", searchUsers);
    if (searchInput) {
      searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") { event.preventDefault(); searchUsers(); }
      });
    }
    if (title) title.addEventListener("input", function () {
      updateCounters(); invalidatePreview();
    });
    if (body) body.addEventListener("input", function () {
      updateCounters(); invalidatePreview();
    });
    if (byId("admin-mail-action")) {
      byId("admin-mail-action").addEventListener("change", invalidatePreview);
    }
    if (previewButton) previewButton.addEventListener("click", preview);
    if (sendButton) sendButton.addEventListener("click", send);
    if (refreshButton) refreshButton.addEventListener("click", function () {
      loadHistory(state.historyPage);
    });
    if (prevButton) prevButton.addEventListener("click", function () {
      loadHistory(state.historyPage - 1);
    });
    if (nextButton) nextButton.addEventListener("click", function () {
      loadHistory(state.historyPage + 1);
    });
    renderRecipients();
    updateCounters();
    invalidatePreview();
    setAudience("SELECTED");
    loadHistory(1);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.AdminMail = {
    MAX_RECIPIENTS: MAX_RECIPIENTS,
    MAX_TITLE: MAX_TITLE,
    MAX_BODY: MAX_BODY,
    ACTION_LABELS: ACTION_LABELS,
    addRecipient: addRecipient,
    removeRecipient: removeRecipient,
    setAudience: setAudience,
    invalidatePreview: invalidatePreview,
    getSelectedUserIds: function () {
      return state.selected.map(function (user) { return user.userId; });
    },
    getAudienceCount: function () { return state.audienceCount; },
    buildPreview: buildPreview
  };
})(window, document);
