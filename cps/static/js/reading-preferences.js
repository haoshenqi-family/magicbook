/* A3: account-level reader theme plus the manual onboarding entry. */
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
        try { data = text ? JSON.parse(text) : null; } catch (e) { /* non-JSON is failure */ }
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

  function setStatus(element, text, isError) {
    if (!element) { return; }
    element.textContent = text || "";
    element.className = "reading-status " + (isError ? "text-danger" : "text-muted");
  }

  (function initTheme() {
    var form = $("reading-theme-form");
    if (!form) { return; }
    var save = $("reading-theme-save");
    var status = $("reading-theme-status");
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
      try { localStorage.setItem(THEME_KEY, value); } catch (e) { /* server remains authoritative */ }
    }

    var local = readLocal();
    if (local) { check(local); }

    getJson("/ajax/ui-settings")
      .then(function (response) {
        if (!response.ok || !response.data || typeof response.data !== "object") {
          throw new Error(messageOf(response, mbT("Failed to load")));
        }
        var settings = unwrap(response.data) || {};
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
        .then(function () { save.disabled = false; });
    });
  })();

  var onboarding = $("reading-onboarding-start");
  if (onboarding) {
    onboarding.addEventListener("click", function () {
      var trigger = $("top_onboarding");
      if (trigger) {
        trigger.click();
      } else if (window.MagicbookOnboarding && window.MagicbookOnboarding.start) {
        window.MagicbookOnboarding.start();
      }
    });
  }
})();
