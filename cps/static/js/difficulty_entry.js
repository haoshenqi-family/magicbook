/* 首页阅读难度入口（R216）：异步取当前档位。
   失败只落到「点此设置」——不猜档位、不显示假值；入口链接始终可用。 */
(function () {
  "use strict";

  var root = document.getElementById("difficulty-entry");
  if (!root || root.getAttribute("data-ready") === "1") { return; }
  root.setAttribute("data-ready", "1");

  var valueEl = root.querySelector(".difficulty-entry-value");
  var fallback = root.getAttribute("data-label-fallback") || "Tap to set";

  function show(text) {
    if (valueEl) { valueEl.textContent = text; }
  }

  fetch(root.getAttribute("data-settings-url"), { credentials: "same-origin" })
    .then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { /* 非 JSON 按失败处理 */ }
        return { ok: response.ok, data: data };
      });
    })
    .then(function (wrap) {
      var data = wrap.data || {};
      if (!wrap.ok || data.success !== true || !data.result) { throw new Error(); }
      var settings = data.result;
      var parts = [];
      if (settings.hardLevel !== undefined && settings.hardLevel !== null) {
        parts.push(String(settings.hardLevel));
      }
      if (settings.hardLevelName) { parts.push(settings.hardLevelName); }
      if (!parts.length) { throw new Error(); }
      var text = parts.join(" - ");
      if (settings.usingDefault) {
        text += " (" + (root.getAttribute("data-label-default") || "default") + ")";
      }
      show(text);
    })
    .catch(function () { show(fallback); });
})();
