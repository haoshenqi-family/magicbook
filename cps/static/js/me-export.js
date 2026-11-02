/* A7 learning-data export: create -> poll task list -> download while fresh. */
(function () {
  "use strict";

  var POLL_MS = 5000;

  function $(id) { return document.getElementById(id); }

  var form = $("me-export-form");
  var message = $("me-export-message");
  var tasksBox = $("me-export-tasks");
  if (!form || !tasksBox) { return; }

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

  function postJson(url, payload) {
    return httpJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      credentials: "same-origin",
      body: JSON.stringify(payload || {})
    });
  }

  function unwrap(data) {
    if (data && typeof data === "object" && data.success === false) {
      throw new Error(data.message || "请求失败");
    }
    if (data && typeof data === "object" &&
        Object.prototype.hasOwnProperty.call(data, "result")) {
      return data.result;
    }
    return data;
  }

  function messageOf(response, fallback) {
    return (response.data && response.data.message) || fallback + " (HTTP " + response.status + ")";
  }

  function say(text, isError) {
    message.textContent = text || "";
    message.className = "me-export-message " + (isError ? "text-danger" : "text-muted");
  }

  function formatSize(bytes) {
    if (!bytes && bytes !== 0) { return "–"; }
    if (bytes < 1024) { return bytes + " B"; }
    if (bytes < 1024 * 1024) { return (bytes / 1024).toFixed(1) + " KB"; }
    return (bytes / 1024 / 1024).toFixed(1) + " MB";
  }

  function formatTime(value) {
    if (!value) { return "–"; }
    return String(value).replace("T", " ").slice(0, 16);
  }

  var STATUS_LABELS = {
    PENDING: "已排队",
    RUNNING: "生成中",
    SUCCESS: "可下载",
    FAILED: "失败"
  };

  function statusLabel(task) {
    if (task.status === "SUCCESS" && !task.downloadable) { return "已过期"; }
    return STATUS_LABELS[task.status] || task.status;
  }

  function render(tasks) {
    tasksBox.innerHTML = "";
    if (!Array.isArray(tasks) || tasks.length === 0) {
      tasksBox.appendChild(document.createTextNode("还没有导出记录。"));
      return;
    }
    var list = document.createElement("ul");
    list.className = "me-export-task-list";
    tasks.forEach(function (task) {
      var item = document.createElement("li");
      item.className = "me-export-task";

      var line = document.createElement("div");
      var label = document.createElement("strong");
      label.textContent = "#" + task.id + " · " + statusLabel(task)
        + (task.encrypted === false ? " · 未加密" : "");
      line.appendChild(label);

      var detail = document.createElement("span");
      detail.className = "text-muted";
      detail.textContent = "  " + formatTime(task.createdAt)
        + (task.fileSize ? " · " + formatSize(task.fileSize) : "")
        + (task.expiresAt ? " · 有效期至 " + formatTime(task.expiresAt) : "");
      line.appendChild(detail);
      item.appendChild(line);

      if (task.status === "FAILED" && task.errorMessage) {
        var error = document.createElement("div");
        error.className = "text-danger small";
        error.textContent = task.errorMessage;
        item.appendChild(error);
      }
      if (task.downloadable) {
        var link = document.createElement("a");
        link.className = "btn btn-default btn-sm";
        link.href = "/ajax/user-export/tasks/" + task.id + "/download";
        link.textContent = "下载 ZIP";
        item.appendChild(link);
      }
      list.appendChild(item);
    });
    tasksBox.appendChild(list);
  }

  var pollTimer = null;

  function setPolling(active) {
    if (active && pollTimer === null) {
      pollTimer = setInterval(refresh, POLL_MS);
    } else if (!active && pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function refresh() {
    return httpJson("/ajax/user-export/tasks", { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) { throw new Error(messageOf(response, "加载失败")); }
        var tasks = unwrap(response.data);
        if (!Array.isArray(tasks)) { tasks = []; }
        render(tasks);
        setPolling(tasks.some(function (task) {
          return task.status === "PENDING" || task.status === "RUNNING";
        }));
      })
      .catch(function (error) {
        setPolling(false);
        tasksBox.textContent = (error && error.message) || "加载失败";
      });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var password = $("me-export-password").value;
    var repeat = $("me-export-password2").value;
    var payload = {};
    if (password !== "") {
      if (password.length < 6) {
        say("密码至少需要 6 个字符。", true);
        return;
      }
      if (password !== repeat) {
        say("两次输入的密码不一致。", true);
        return;
      }
      payload.password = password;
    }
    var button = $("me-export-start");
    button.disabled = true;
    say("正在创建导出…", false);
    postJson("/ajax/user-export/create", payload)
      .then(function (response) {
        if (!response.ok) { throw new Error(messageOf(response, "创建导出失败")); }
        say("导出已开始，通常不到一分钟完成。", false);
        $("me-export-password").value = "";
        $("me-export-password2").value = "";
        refresh();
      })
      .catch(function (error) {
        say((error && error.message) || "创建导出失败", true);
      })
      .then(function () {
        button.disabled = false;
      });
  });

  refresh();
})();
