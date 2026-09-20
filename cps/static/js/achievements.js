/* 成就中心页逻辑：summary/detail/pending 三接口异步加载 + 解锁弹层。
   轮询 pending 仅在页面可见时进行（visibilitychange 控制），进入页面自动 claim。 */
(function () {
  "use strict";

  var TIER_ORDER = ["BRONZE", "SILVER", "GOLD", "PLATINUM"];
  var ICON_MAP = {
    book: "glyphicon-book",
    highlight: "glyphicon-pencil",
    note: "glyphicon-edit",
    word: "glyphicon-font",
    search: "glyphicon-search",
    flame: "glyphicon-fire",
    calendar: "glyphicon-calendar"
  };

  function $(id) { return document.getElementById(id); }

  function unwrapResult(data) {
    // moon-well Result 包装: {"success": bool, "result": ...}
    if (data && data.success) { return data.result; }
    return null;
  }

  function showError(message) {
    $("ach-error-text").textContent = message;
    $("ach-error").classList.remove("hidden");
  }

  function hideError() {
    $("ach-error").classList.add("hidden");
  }

  function fetchJson(url, options) {
    return fetch(url, options).then(function (resp) {
      return resp.json().catch(function () { return {}; });
    });
  }

  function getCsrfToken() {
    // Why: CSRFProtect 全局校验 POST；main.js 的 $.ajaxPrefilter 只兜底 jQuery，
    // 原生 fetch 必须自带 X-CSRFToken，否则 claim 一直 400
    var el = document.getElementById("ach-csrf");
    return el ? el.value : "";
  }

  // ---- 渲染 ----

  function renderSummary(summary) {
    if (!summary) { return; }
    $("ach-summary").hidden = false;
    $("ach-level-num").textContent = summary.level || 1;
    $("ach-total-points").textContent = summary.totalPoints || 0;
    $("ach-unlocked-count").textContent =
      (summary.unlockedCount || 0) + " / " + (summary.totalCount || 0);
    $("ach-streak").textContent = summary.currentStreakDays || 0;
    $("ach-pending-count").textContent = summary.pendingCount || 0;

    var cats = {};
    (summary.categories || []).forEach(function (c) { cats[c.category] = c; });
    $("ach-tab-all").textContent = (summary.unlockedCount || 0) + "/" + (summary.totalCount || 0);
    $("ach-tab-read").textContent = cats.READ ? cats.READ.unlocked + "/" + cats.READ.total : "";
    $("ach-tab-vocab").textContent = cats.VOCAB ? cats.VOCAB.unlocked + "/" + cats.VOCAB.total : "";
    $("ach-tab-streak").textContent = cats.STREAK ? cats.STREAK.unlocked + "/" + cats.STREAK.total : "";
    $("ach-tabs").hidden = false;
  }

  function tierClass(tier) {
    var t = (tier || "").toUpperCase();
    return TIER_ORDER.indexOf(t) >= 0 ? "ach-badge-" + t.toLowerCase() : "ach-badge-bronze";
  }

  function iconClass(iconKey) {
    return ICON_MAP[iconKey] || " glyphicon-certificate";
  }

  function formatDate(epochMillis) {
    if (!epochMillis) { return ""; }
    var d = new Date(epochMillis);
    return d.toLocaleDateString();
  }

  function renderDetail(list) {
    var container = $("ach-list");
    container.innerHTML = "";
    (list || []).forEach(function (a) {
      var card = document.createElement("div");
      card.className = "ach-card" + (a.unlocked ? "" : " locked");

      var pct = 0;
      if (a.progress && a.progress.target > 0) {
        pct = Math.min(100, Math.round(a.progress.current * 100 / a.progress.target));
      }

      card.innerHTML =
        '<div class="ach-badge ' + tierClass(a.tier) + '">' +
        '  <span class="glyphicon ' + iconClass(a.iconKey) + '"></span>' +
        "</div>" +
        '<div class="ach-info">' +
        '  <div class="ach-name"></div>' +
        '  <div class="ach-desc"></div>' +
        (a.unlocked
          ? '<div class="ach-unlocked-at"></div>'
          : '<div class="ach-progress">' +
            '  <div class="progress"><div class="progress-bar" style="width:' + pct + '%"></div></div>' +
            '  <div class="ach-progress-text">' + (a.progress ? a.progress.current : 0) +
            " / " + (a.progress ? a.progress.target : 0) + "</div>" +
            "</div>") +
        "</div>" +
        '<div class="ach-points"><span class="value">+' + (a.points || 0) +
        '</span><span class="label">XP</span></div>';

      card.querySelector(".ach-name").textContent = a.name || a.code;
      card.querySelector(".ach-desc").textContent = a.description || "";
      var unlockedAt = card.querySelector(".ach-unlocked-at");
      if (unlockedAt) { unlockedAt.textContent = "✓ " + formatDate(a.unlockedAt); }

      container.appendChild(card);
    });
  }

  // ---- 解锁弹层 ----

  var pendingQueue = [];
  var claiming = false;

  function playNextPending() {
    if (claiming || pendingQueue.length === 0) { return; }
    var ach = pendingQueue.shift();
    $("ach-unlock-icon").className = "ach-unlock-icon " + tierClass(ach.tier);
    $("ach-unlock-icon").textContent = "★";
    $("ach-unlock-name").textContent = ach.name || ach.code;
    $("ach-unlock-desc").textContent = ach.description || "";
    $("ach-unlock-points").textContent = "+" + (ach.points || 0) + " XP";
    $("ach-unlock-modal").classList.remove("hidden");
    claiming = true;

    $("ach-unlock-claim").onclick = function () {
      fetchJson("/ajax/achievements-claim", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest",
                   "X-CSRFToken": getCsrfToken() },
        body: JSON.stringify({ code: ach.code })
      }).catch(function () { /* claim 失败下次轮询还会出现，不阻塞 */ })
        .finally(function () {
          $("ach-unlock-modal").classList.add("hidden");
          claiming = false;
          playNextPending();
          loadSummary(); // 刷新角标与等级
        });
    };
  }

  function loadPending() {
    if (document.visibilityState !== "visible") { return; }
    fetchJson("/ajax/achievements-pending").then(function (data) {
      var pending = unwrapResult(data);
      if (pending && pending.length) {
        pendingQueue = pendingQueue.concat(pending);
        playNextPending();
      }
    }).catch(function () { /* 轮询失败静默 */ });
  }

  // ---- 加载 ----

  var currentCategory = "";

  function loadSummary() {
    return fetchJson("/ajax/achievements-summary").then(function (data) {
      var summary = unwrapResult(data);
      if (!summary) {
        showError((data && data.message) || "achievements service unavailable");
        return;
      }
      hideError();
      renderSummary(summary);
    });
  }

  function loadDetail() {
    var url = "/ajax/achievements-detail";
    if (currentCategory) { url += "?category=" + encodeURIComponent(currentCategory); }
    return fetchJson(url).then(function (data) {
      var list = unwrapResult(data);
      if (!list) {
        showError((data && data.message) || "achievements service unavailable");
        return;
      }
      hideError();
      renderDetail(list);
    });
  }

  function loadAll() {
    loadSummary().then(loadDetail).catch(function () {
      showError("achievements service unavailable");
    });
  }

  // ---- 事件绑定 ----

  function bindTabs() {
    var tabs = $("ach-tabs");
    if (!tabs) { return; }
    tabs.addEventListener("click", function (event) {
      var li = event.target.closest("li");
      if (!li || !li.dataset) { return; }
      event.preventDefault();
      tabs.querySelectorAll("li").forEach(function (el) { el.classList.remove("active"); });
      li.classList.add("active");
      currentCategory = li.dataset.category || "";
      loadDetail();
    });
  }

  function bindRetry() {
    var retry = $("ach-retry");
    if (retry) { retry.onclick = loadAll; }
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindRetry();
    bindTabs();
    loadAll();
    // pending 轮询：60s，仅页面可见时
    setInterval(loadPending, 60000);
    loadPending();
  });
})();
