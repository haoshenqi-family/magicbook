/* R216 阅读器账号主题同步：在 <head> 早载，异步取账号级阅读主题。
   成功 → 写 window.__mbReaderTheme 与 localStorage 镜像，并广播事件让已初始化的阅读器切换；
   失败 → 只 console.warn，本机主题照常生效（不阻塞阅读）。
   用户在本次会话手动选过主题（__mbReaderThemePicked）时，晚到的账号值不再覆盖。 */
(function () {
  "use strict";

  var KEY = "calibre.reader.theme";
  var BUILTIN = ["lightTheme", "darkTheme", "sepiaTheme", "amberTheme", "blackTheme"];

  // 兼容子路径部署：按本脚本自身的 src 反推应用根（同 onboarding.appPath 的口径）
  var script = document.currentScript;
  var base = "";
  if (script && script.src) {
    var at = script.src.indexOf("/static/js/ui-prefs.js");
    if (at >= 0) { base = script.src.slice(0, at); }
  }
  window.__mbBasePath = base;

  fetch(base + "/ajax/ui-settings", { credentials: "same-origin" })
    .then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { /* 非 JSON 按失败处理 */ }
        return { ok: response.ok, data: data };
      });
    })
    .then(function (wrap) {
      var data = wrap.data || {};
      if (!wrap.ok || data.success !== true || !data.result) {
        throw new Error("ui settings unavailable");
      }
      var theme = data.result.readerTheme;
      if (BUILTIN.indexOf(theme) < 0) { return; } // 账号未设置：保留本机选择
      if (window.__mbReaderThemePicked) { return; }
      window.__mbReaderTheme = theme;
      try { localStorage.setItem(KEY, theme); } catch (e) { /* 隐私模式 */ }
      try {
        window.dispatchEvent(new CustomEvent("magicbook:reader-theme", { detail: { theme: theme } }));
      } catch (e) { /* 老浏览器无 CustomEvent */ }
    })
    .catch(function (error) {
      if (window.console && console.warn) { console.warn("R216 reader theme sync failed:", error); }
    });
})();
