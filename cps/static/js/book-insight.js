// cps/static/js/book-insight.js — R214 B 详情页速览交互（目录展开 / 章首段 / 生成简介）。
//
// Why 零界面文案：i18n 契约（tests/test_i18n_seed_contract.py + tests/i18n_js_files.json）
// 的扫描面是静态 JS 里的 mbT() 取词；本文件所有可见文案都由模板经 data-* 注入，
// 不进种子、不绕过契约。生成失败时展示的服务端 message 本身就是用户可读文案
// （透传上游，LLD §8），失败可见不靠前端再编一套话术。
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState !== "loading") {
      fn();
    } else {
      document.addEventListener("DOMContentLoaded", fn);
    }
  }

  onReady(function () {
    // ---- 目录：展开全部 / 收起（前 8 章常显，其余 toc-extra 折叠）----
    var expand = document.getElementById("toc-expand");
    if (expand) {
      expand.addEventListener("click", function () {
        var expanded = expand.getAttribute("data-expanded") === "1";
        var extras = document.querySelectorAll(".toc-extra");
        for (var i = 0; i < extras.length; i++) {
          extras[i].hidden = !expanded;
        }
        expand.setAttribute("data-expanded", expanded ? "0" : "1");
        var label = expand.getAttribute(expanded ? "data-label-collapsed" : "data-label-expanded");
        if (label) {
          expand.textContent = label;
        }
      });
    }

    // ---- 章节行：点击章名展开/收起该章首段 ----
    var tocList = document.querySelector(".toc-list");
    if (tocList) {
      tocList.addEventListener("click", function (event) {
        var node = event.target;
        var toggle = null;
        while (node && node !== tocList) {
          if (node.classList && node.classList.contains("toc-toggle")) {
            toggle = node;
            break;
          }
          node = node.parentNode;
        }
        if (!toggle) {
          return;
        }
        var targetId = toggle.getAttribute("data-target");
        var panel = targetId ? document.getElementById(targetId) : null;
        if (panel) {
          panel.hidden = !panel.hidden;
        }
      });
    }

    // ---- 生成简介（admin）：成功整页重载，简介区块按三级回退服务端渲染 ----
    var generate = document.getElementById("generate-book-summary");
    if (generate) {
      generate.addEventListener("click", function () {
        var errorBox = document.getElementById("book-summary-error");
        var idleLabel = generate.getAttribute("data-idle-label") || generate.textContent;
        generate.disabled = true;
        generate.textContent = generate.getAttribute("data-busy-label") || idleLabel;
        if (errorBox) {
          errorBox.textContent = "";
        }
        fetch("/ajax/book-summary", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": generate.getAttribute("data-csrf-token") || ""
          },
          body: JSON.stringify({
            book_id: parseInt(generate.getAttribute("data-book-id"), 10),
            book_format: generate.getAttribute("data-book-format") || "epub"
          })
        }).then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, data: data };
          });
        }).then(function (outcome) {
          if (outcome.data && outcome.data.success) {
            // 生成即定稿（拍板⑦无「重新生成」）：重载让服务端按三级回退统一渲染。
            window.location.reload();
            return;
          }
          if (errorBox) {
            errorBox.textContent = (outcome.data && outcome.data.message) || "HTTP " +
              (outcome.data ? "" : "error");
          }
          generate.disabled = false;
          generate.textContent = idleLabel;
        }).catch(function (error) {
          if (errorBox) {
            errorBox.textContent = String(error);
          }
          generate.disabled = false;
          generate.textContent = idleLabel;
        });
      });
    }
  });
})();
