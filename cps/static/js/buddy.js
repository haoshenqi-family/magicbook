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
      img.src = b.fullImageUrl || b.imageUrl || "";
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
        action.innerHTML = '<span class="buddy-state">' + mbT("Coming soon") + "</span>";
      }
      card.appendChild(action);

      root.appendChild(card);
    });
    // 花名册渲染完成 → 通知引导引擎：伙伴段的锚点（雪鸮领取按钮）此刻才存在
    if (window.MagicbookOnboarding && window.MagicbookOnboarding.onRosterReady) {
      window.MagicbookOnboarding.onRosterReady();
    }
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
    load();
  });
})();
