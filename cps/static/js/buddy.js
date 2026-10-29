/* 伙伴页逻辑（R206）：拉花名册 → 渲染卡片 → 领取/装备后就地刷新。
   数据面全在 moon-well /buddy，本站只透传；解包/CSRF 复用全站公共层 window.MBApi。 */
(function () {
  "use strict";

  var mbT = window.mbT || function (id) { return id; };
  function $(id) { return document.getElementById(id); }

  function csrf() {
    if (window.MBApi && window.MBApi.csrfToken) { return window.MBApi.csrfToken(); }
    var el = $("buddy-csrf");
    return el ? el.value : "";
  }

  function showError(message) {
    $("buddy-error-text").textContent = message || mbT("Failed to load");
    $("buddy-error").classList.remove("hidden");
  }
  function hideError() { $("buddy-error").classList.add("hidden"); }

  function unwrap(data) {
    if (window.MBApi && window.MBApi.unwrapResult) { return window.MBApi.unwrapResult(data); }
    return (data && data.success) ? data.result : null;
  }

  function render(list) {
    var root = $("buddy-roster");
    root.innerHTML = "";
    list.forEach(function (b) {
      var card = document.createElement("div");
      var locked = !b.owned && !b.claimable;
      card.className = "buddy-card" + (b.equipped ? " equipped" : "") + (locked ? " locked" : "");

      var img = document.createElement("img");
      img.className = "buddy-avatar";
      img.src = (b.fullImageUrl || b.imageUrl)
        ? "/ajax/buddy/image?src=" + encodeURIComponent(b.fullImageUrl || b.imageUrl)
        : "";
      img.alt = b.name;
      img.onerror = function () { img.style.visibility = "hidden"; };
      card.appendChild(img);

      var name = document.createElement("div");
      name.className = "buddy-name";
      name.textContent = b.name;
      card.appendChild(name);

      if (b.rarity) {
        var rar = document.createElement("div");
        rar.className = "buddy-rarity " + b.rarity;
        rar.textContent = b.rarity;
        card.appendChild(rar);
      }

      var action = document.createElement("div");
      action.className = "buddy-action";
      if (b.equipped) {
        action.innerHTML = '<span class="buddy-state on">' + mbT("In use") + "</span>";
      } else if (b.owned) {
        action.appendChild(mkBtn(mbT("Equip"), "btn btn-default btn-xs", function () { post("/ajax/buddy/equip", b.code); }, "buddy-equip-" + b.code));
      } else if (b.claimable) {
        action.appendChild(mkBtn(mbT("Claim"), "btn btn-primary btn-xs", function () { post("/ajax/buddy/claim", b.code); }, "buddy-claim-" + b.code));
      } else {
        action.innerHTML = '<span class="buddy-state">' + lockedLabel(b) + "</span>";
      }
      card.appendChild(action);

      root.appendChild(card);
    });
    // 花名册渲染完成 → 通知引导引擎：伙伴段的锚点（雪鸮领取按钮）此刻才存在
    if (window.MagicbookOnboarding && window.MagicbookOnboarding.onRosterReady) {
      window.MagicbookOnboarding.onRosterReady();
    }
  }

  // 锁定态按获取方式给准确文案：成就/积分是已定义的解锁路径，
  // 不再统一写「Coming soon」误导成未开发。
  function lockedLabel(b) {
    if (b.unlockType === "ACHIEVEMENT") { return mbT("Unlocks with an achievement"); }
    if (b.unlockType === "POINTS") { return mbT("Unlocks with credits"); }
    return mbT("Coming soon");
  }

  function mkBtn(text, cls, onClick, id) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = cls;
    btn.textContent = text;
    if (id) { btn.id = id; }
    btn.addEventListener("click", onClick);
    return btn;
  }

  function load() {
    hideError();
    fetch("/ajax/buddy/catalog", { credentials: "same-origin" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (data) {
        var list = unwrap(data);
        if (!Array.isArray(list)) { showError((data && data.message) || mbT("Failed to load")); return; }
        render(list);
      })
      .catch(function () { showError(mbT("Failed to load")); });
  }

  function post(url, code) {
    fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify({ code: code }),
    })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (data) {
        var list = unwrap(data);
        if (Array.isArray(list)) { render(list); }
        else { showError((data && data.message) || mbT("Operation failed")); }
      })
      .catch(function () { showError(mbT("Operation failed")); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    $("buddy-retry").addEventListener("click", load);
    var openChat = $("buddy-open-chat");
    if (openChat) {
      openChat.addEventListener("click", function () {
        if (window.AICompanion && window.AICompanion.openChat) {
          window.AICompanion.openChat();
        }
      });
    }
    load();
    initQuickActions();
  });

  // ------------------------------------------------------------------
  // R223 悬浮球快捷动作配置：勾选 4-5 个（chat 固定占位不可取消、恒第一位，
  // 服务端 R234 同样归一兜底），保存后全站 FAB hover 气泡按此渲染。
  // ------------------------------------------------------------------
  var qaSelected = [];

  function initQuickActions() {
    fetch("/ajax/buddy/quick-actions", { credentials: "same-origin" })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (data) {
        var payload = unwrap(data) || {};
        renderQuickActions(payload.available || [], payload.selected || []);
      })
      .catch(function () { renderQuickActions([], []); });
    $("buddy-qa-save").addEventListener("click", saveQuickActions);
  }

  function renderQuickActions(available, selected) {
    qaSelected = selected.slice();
    var root = $("buddy-quick-actions");
    root.innerHTML = "";
    available.forEach(function (a) {
      var isChat = a.id === "chat";
      var on = qaSelected.indexOf(a.id) !== -1 || isChat;
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "buddy-qa-chip" + (on ? " on" : "");
      chip.textContent = a.label + (isChat ? " ★" : "");
      chip.dataset.id = a.id;
      chip.addEventListener("click", function () {
        if (isChat) return;
        var idx = qaSelected.indexOf(a.id);
        if (idx !== -1) { qaSelected.splice(idx, 1); }
        else if (qaSelected.length < 5) { qaSelected.push(a.id); }
        syncQuickActionChips();
      });
      root.appendChild(chip);
    });
    syncQuickActionChips();
  }

  function syncQuickActionChips() {
    var root = $("buddy-quick-actions");
    Array.prototype.forEach.call(root.children, function (chip) {
      var on = chip.dataset.id === "chat" || qaSelected.indexOf(chip.dataset.id) !== -1;
      chip.classList.toggle("on", on);
    });
    $("buddy-qa-state").textContent = "";
  }

  function saveQuickActions() {
    if (qaSelected.indexOf("chat") === -1) { qaSelected.unshift("chat"); }
    if (qaSelected.length < 4) {
      $("buddy-qa-state").textContent = mbT("Pick at least 4 actions");
      return;
    }
    fetch("/ajax/buddy/quick-actions", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify({ selected: qaSelected.slice(0, 5) }),
    })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (data) {
        $("buddy-qa-state").textContent = data && data.success
          ? mbT("Saved")
          : ((data && data.message) || mbT("Operation failed"));
      })
      .catch(function () { $("buddy-qa-state").textContent = mbT("Operation failed"); });
  }
})();
