/* /me 偏好页（R216）：语言走原生 POST，难度/主题/伙伴由本脚本处理。
   解包与 CSRF 复用全站公共层 window.MBApi；失败一律呈现到对应区块，不静默。 */
(function () {
  "use strict";

  var mbT = window.mbT || function (id) { return id; };
  var THEME_KEY = "calibre.reader.theme";
  var BUILTIN_THEMES = ["lightTheme", "darkTheme", "sepiaTheme", "amberTheme", "blackTheme"];

  function $(id) { return document.getElementById(id); }

  function csrfToken() {
    if (window.MBApi && window.MBApi.csrfToken) { return window.MBApi.csrfToken(); }
    var input = document.querySelector("input[name='csrf_token']");
    return input ? input.value : "";
  }

  function httpJson(url, options) {
    if (window.MBApi && window.MBApi.httpJson) { return window.MBApi.httpJson(url, options); }
    return fetch(url, options).then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { /* 非 JSON 按失败处理 */ }
        return { ok: response.ok, status: response.status, data: data, raw: text };
      });
    });
  }

  function getJson(url) {
    return httpJson(url, { credentials: "same-origin" });
  }

  function postJson(url, body) {
    return httpJson(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify(body || {})
    });
  }

  // moon-well Result 信封：success=false 抛上游文案；success=true 取 result。
  // 非信封响应原样返回，调用方必须同时判 response.ok。
  function unwrap(data) {
    if (data && typeof data === "object" && data.success === false) {
      throw new Error(data.message || mbT("Something went wrong"));
    }
    if (data && typeof data === "object" && data.success === true &&
        Object.prototype.hasOwnProperty.call(data, "result")) {
      return data.result;
    }
    return data;
  }

  function messageOf(response, fallback) {
    return (response.data && response.data.message) || fallback + " (HTTP " + response.status + ")";
  }

  function setStatus(el, text, isError) {
    if (!el) { return; }
    el.textContent = text || "";
    el.className = "me-status " + (isError ? "text-danger" : "text-muted");
  }

  /* ---------- 阅读难度 ---------- */
  (function initDifficulty() {
    var form = $("me-difficulty-form");
    if (!form) { return; }
    var select = $("me-hard-level");
    var save = $("me-difficulty-save");
    var status = $("me-difficulty-status");
    var retry = $("me-difficulty-retry");

    if (retry) {
      retry.addEventListener("click", function () { window.location.reload(); });
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var level = parseInt(select.value, 10);
      if (isNaN(level) || level < 0 || level > 9) {
        setStatus(status, mbT("Invalid level"), true);
        return;
      }
      save.disabled = true;
      setStatus(status, mbT("Saving..."));
      postJson(form.getAttribute("data-save-url"), { hardLevel: level })
        .then(function (response) {
          if (!response.ok || (response.data && response.data.success === false)) {
            throw new Error(messageOf(response, mbT("Save failed")));
          }
          setStatus(status, mbT("Saved") + " ✓");
        })
        .catch(function (error) {
          setStatus(status, (error && error.message) || mbT("Save failed"), true);
        })
        .finally(function () { save.disabled = false; });
    });
  })();

  /* ---------- 阅读主题 ---------- */
  (function initTheme() {
    var form = $("me-theme-form");
    if (!form) { return; }
    var save = $("me-theme-save");
    var status = $("me-theme-status");
    var touched = false;

    function selected() {
      var checked = form.querySelector("input[name='reader-theme']:checked");
      return checked ? checked.value : null;
    }

    function check(value) {
      var list = form.querySelectorAll("input[name='reader-theme']");
      for (var i = 0; i < list.length; i++) {
        list[i].checked = list[i].value === value;
      }
    }

    function readLocal() {
      try {
        var value = localStorage.getItem(THEME_KEY);
        return BUILTIN_THEMES.indexOf(value) >= 0 ? value : null;
      } catch (e) { return null; }
    }

    function writeLocal(value) {
      try { localStorage.setItem(THEME_KEY, value); } catch (e) { /* 隐私模式：服务端仍是权威 */ }
    }

    var local = readLocal();
    if (local) { check(local); }

    // 账号值优先：读到后覆盖本机镜像；读不到只提示，不假装已同步。
    getJson("/ajax/ui-settings")
      .then(function (response) {
        if (!response.ok || !response.data || typeof response.data !== "object") {
          throw new Error(messageOf(response, mbT("Failed to load")));
        }
        var settings = unwrap(response.data) || {};
        // 用户在请求返回前已经改过单选，就不覆盖他的选择
        if (!touched && BUILTIN_THEMES.indexOf(settings.readerTheme) >= 0) {
          check(settings.readerTheme);
          writeLocal(settings.readerTheme);
        }
      })
      .catch(function () {
        setStatus(status, mbT("Could not load your saved theme; showing this device's last choice."), true);
      });

    form.addEventListener("change", function (event) {
      if (event.target && event.target.name === "reader-theme") { touched = true; }
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var value = selected();
      if (!value) {
        setStatus(status, mbT("Choose a theme first."), true);
        return;
      }
      save.disabled = true;
      setStatus(status, mbT("Saving..."));
      postJson("/ajax/ui-settings/reader-theme", { theme: value })
        .then(function (response) {
          if (!response.ok || !response.data || typeof response.data !== "object") {
            throw new Error(messageOf(response, mbT("Save failed")));
          }
          var settings = unwrap(response.data) || {};
          var saved = BUILTIN_THEMES.indexOf(settings.readerTheme) >= 0 ? settings.readerTheme : value;
          writeLocal(saved);
          check(saved);
          touched = false;
          setStatus(status, mbT("Theme saved"));
        })
        .catch(function (error) {
          setStatus(status, (error && error.message) || mbT("Theme could not be synced to your account"), true);
        })
        .finally(function () { save.disabled = false; });
    });
  })();

  /* ---------- 伙伴（只读卡片） ---------- */
  (function initBuddy() {
    var body = $("me-buddy-body");
    if (!body) { return; }

    function textNode(tag, className, text) {
      var el = document.createElement(tag);
      el.className = className;
      el.textContent = text;
      return el;
    }

    function render(list) {
      body.innerHTML = "";
      var equipped = null;
      for (var i = 0; i < list.length; i++) {
        if (list[i].equipped) { equipped = list[i]; break; }
      }
      if (!equipped && list.length) { equipped = list[0]; }
      if (!equipped) {
        body.appendChild(textNode("span", "me-buddy-state text-muted", mbT("No buddy equipped yet.")));
        return;
      }
      if (equipped.imageUrl || equipped.fullImageUrl) {
        var img = document.createElement("img");
        img.className = "me-buddy-avatar";
        img.src = "/ajax/buddy/image?src=" + encodeURIComponent(equipped.imageUrl || equipped.fullImageUrl);
        img.alt = equipped.name || "";
        img.onerror = function () { img.style.visibility = "hidden"; };
        body.appendChild(img);
      }
      var text = document.createElement("div");
      text.className = "me-buddy-text";
      text.appendChild(textNode("span", "me-buddy-name", equipped.name || ""));
      var state = [];
      if (equipped.equipped) { state.push(mbT("In use")); }
      if (equipped.rarity && equipped.rarity !== "COMMON") { state.push(equipped.rarity); }
      if (state.length) {
        text.appendChild(textNode("span", "me-buddy-state text-muted", state.join(" · ")));
      }
      body.appendChild(text);
    }

    function fail() {
      body.innerHTML = "";
      body.appendChild(textNode("span", "me-buddy-state text-danger", mbT("Could not load your buddy.")));
      var retry = document.createElement("button");
      retry.type = "button";
      retry.className = "btn btn-default btn-xs me-buddy-error-btn";
      retry.textContent = mbT("Retry");
      retry.addEventListener("click", load);
      body.appendChild(retry);
    }

    function load() {
      body.innerHTML = "";
      body.appendChild(textNode("span", "me-buddy-state text-muted", mbT("Loading")));
      getJson("/ajax/buddy/mine")
        .then(function (response) {
          if (!response.ok) {
            throw new Error(messageOf(response, mbT("Failed to load")));
          }
          var list = unwrap(response.data || {});
          if (!Array.isArray(list)) {
            throw new Error(messageOf(response, mbT("Failed to load")));
          }
          render(list);
        })
        .catch(fail);
    }

    load();
  })();
})();
