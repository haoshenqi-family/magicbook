/* AI Companion chat panel logic — agent 模式（moon-well 宿主）。
   - 会话列表/历史/改名/删除走 /ai/agent/* 薄代理（数据源 moon-well MySQL）
   - SSE 分型事件：delta 正文打字机 / tool_call+tool_result 工具芯片 / final 收尾 / error 错误条
   - 降级兼容：事件无 event: 行（旧裸文本流）时按 delta 渲染
   - 记忆面板：查/改/删本人长期记忆 + book 学情摘要
   Depends on: jQuery (loaded by reader pages), ai_page_extract.js */
(function ($) {
  "use strict";
  if (!window.AICompanion) return;

  var BOOK_ID = null;
  var BOOK_META = null;
  var currentConversationId = null;
  var sending = false;
  var deleting = false;

  function getCsrfToken() {
    return $("input[name='csrf_token']").val() || "";
  }

  function getBookIdFromUrl() {
    var m = window.location.pathname.match(/\/read\/(\d+)\/([A-Za-z0-9]+)/);
    if (m) return { id: parseInt(m[1], 10), format: m[2] };
    return { id: null, format: null };
  }

  function storageKey() {
    return "calibre.ai.conv." + BOOK_ID;
  }

  /** moon-well Result 包装解包：{success, result, message} → result（失败时抛错）。 */
  function unwrap(data) {
    if (data && data.success === false) {
      throw new Error(data.message || "moon-well 请求失败");
    }
    return data && data.result !== undefined ? data.result : data;
  }

  function init() {
    var info = getBookIdFromUrl();
    BOOK_ID = info.id;
    BOOK_META = window.AICompanionBookMeta || {};

    $("#ai-companion-fab").on("click", toggleDrawer);
    $("#ai-companion-close").on("click", closeDrawer);
    $("#ai-chat-send").on("click", sendMessage);
    $("#ai-chat-new").on("click", newConversation);
    $("#ai-chat-rename").on("click", renameConversation);
    $("#ai-chat-delete").on("click", deleteConversation);
    $("#ai-chat-memory").on("click", toggleMemoryPanel);
    $("#ai-memory-close").on("click", function () { $("#ai-memory-panel").removeClass("open"); });
    $("#ai-memory-add").on("click", addMemory);
    $("#ai-chat-conversations").on("change", function () {
      selectConversation(parseInt($(this).val(), 10));
    });
    $("#ai-chat-input").on("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    // ESC 关闭 AI 抽屉。EPUB 划词气泡打开时优先只关气泡（epub.js 的
    // ESC 监听负责），两个面板同开时逐层退出而不是一次全关。
    $(document).on("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (window.ReaderTranslation && window.ReaderTranslation.isOpen()) return;
      if ($("#ai-companion-drawer").hasClass("open")) closeDrawer();
    });

    loadConversations();
  }

  function toggleDrawer() {
    $("#ai-companion-drawer").toggleClass("open");
    if ($("#ai-companion-drawer").hasClass("open") && $("#ai-memory-panel").hasClass("open")) {
      loadMemoryPanel();
    }
  }
  function closeDrawer() {
    $("#ai-companion-drawer").removeClass("open");
  }

  // 阅读器划词右键菜单入口：把选中文本以「」引用形式追加到输入框（不发送），
  // 打开抽屉并把光标放到末尾——用户接着补提示词，写完自己按发送
  function insertIntoInput(text) {
    var quoted = String(text || "").trim();
    if (!quoted) return false;
    var $input = $("#ai-chat-input");
    if (!$input.length) return false;
    var current = $input.val();
    $input.val(current ? current.replace(/\s+$/, "") + "\n\n「" + quoted + "」\n" : "「" + quoted + "」\n");
    $("#ai-companion-drawer").addClass("open");
    var el = $input.get(0);
    el.focus();
    var end = el.value.length;
    try { el.setSelectionRange(end, end); } catch (e) {}
    return true;
  }
  window.AICompanion.insertIntoInput = insertIntoInput;

  // ------------------------------------------------------------------
  // 会话列表（moon-well MySQL 数据源，薄代理透传）
  // ------------------------------------------------------------------
  function loadConversations() {
    if (!BOOK_ID) return;
    $.getJSON("/ai/agent/conversations", { bookId: BOOK_ID })
      .then(function (raw) {
        var convs;
        try { convs = unwrap(raw) || []; } catch (e) { convs = []; }
        var $sel = $("#ai-chat-conversations").empty();
        if (!convs.length) {
          newConversation();
          return;
        }
        convs.forEach(function (c) {
          $sel.append($("<option>").val(c.id).text(c.title || "新会话"));
        });
        var preferred = parseInt(localStorage.getItem(storageKey()) || "", 10);
        var target = convs.some(function (c) { return c.id === preferred; }) ? preferred : convs[0].id;
        selectConversation(target);
      })
      .fail(function (xhr) {
        // agent 未开启 / moon-well 不可达：下拉留空，输入框仍可用（发送时报具体错误）
        $("#ai-chat-conversations").empty();
        currentConversationId = null;
        if (xhr && xhr.status === 400) return;
        console && console.warn && console.warn("conversations load failed:", xhr && xhr.status);
      });
  }

  /** 新会话 = 本地置空，首条消息由 moon-well 服务端建会话（final 事件回传 id）。 */
  function newConversation() {
    currentConversationId = null;
    persistSelection();
    $("#ai-chat-conversations").val(null);
    clearMessages();
    appendHint("新会话已就绪：第一句提问发出后自动创建。");
  }

  function selectConversation(conversationId) {
    if (!conversationId) return;
    currentConversationId = conversationId;
    persistSelection();
    $("#ai-chat-conversations").val(conversationId);
    loadHistory(conversationId);
  }

  function renameConversation() {
    var id = currentConversationId;
    if (!id) { window.alert("请先选择一个已创建的会话"); return; }
    var $opt = $("#ai-chat-conversations").find("option:selected");
    var newTitle = window.prompt("重命名会话", ($opt.text() || "").trim());
    if (newTitle === null) return;
    newTitle = (newTitle || "").trim();
    if (!newTitle) return;
    $.ajax({
      url: "/ai/agent/conversation/rename",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ conversationId: id, title: newTitle }),
    }).then(function (raw) {
      try { unwrap(raw); } catch (e) { window.alert(e.message); return; }
      $opt.text(newTitle);
    }).fail(function (xhr) {
      window.alert("重命名失败: " + errText(xhr));
    });
  }

  function deleteConversation() {
    var id = currentConversationId;
    if (!id || deleting) return;
    var title = $("#ai-chat-conversations").find("option:selected").text() || "";
    if (!window.confirm("删除会话「" + title + "」？该操作不可恢复。")) return;
    deleting = true;
    $.ajax({
      url: "/ai/agent/conversation/delete",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ conversationId: id }),
    }).then(function () {
      deleting = false;
      var $cur = $("#ai-chat-conversations").find("option[value='" + id + "']");
      $cur.remove();
      var $next = $("#ai-chat-conversations").find("option").first();
      if ($next.length) {
        selectConversation(parseInt($next.val(), 10));
      } else {
        newConversation();
      }
    }).fail(function (xhr) {
      deleting = false;
      window.alert("删除失败: " + errText(xhr));
    });
  }

  function persistSelection() {
    try {
      if (currentConversationId) localStorage.setItem(storageKey(), String(currentConversationId));
      else localStorage.removeItem(storageKey());
    } catch (e) {}
  }

  function errText(xhr) {
    try {
      var data = JSON.parse(xhr.responseText);
      return data.message || data.error || ("HTTP " + xhr.status);
    } catch (e) { return "HTTP " + xhr.status; }
  }

  // ------------------------------------------------------------------
  // 消息渲染
  // ------------------------------------------------------------------
  function clearMessages() {
    $("#ai-chat-messages").empty();
  }

  function appendHint(text) {
    $('<div class="ai-chat-hint"></div>').text(text).appendTo("#ai-chat-messages");
    scrollMessages();
  }

  function appendMessage(role, content) {
    var safe = renderMarkdown(content);
    var cls = role === "user" ? "user" : "assistant";
    $('<div class="ai-chat-msg ' + cls + '"></div>').html(safe).appendTo("#ai-chat-messages");
    scrollMessages();
  }

  function renderMarkdown(text) {
    if (!text) return "";
    var esc = $("<div>").text(text).html(); // escape HTML first
    esc = esc.replace(/```([\s\S]*?)```/g, function (_, code) {
      return "<pre><code>" + code.replace(/^\n/, "") + "</code></pre>";
    });
    esc = esc.replace(/`([^`]+)`/g, "<code>$1</code>");
    esc = esc.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    esc = esc.replace(/\n/g, "<br>");
    return esc;
  }

  /** 工具芯片：tool_call 建立折叠行，tool_result 收尾（✓/✗ + 耗时 + 可展开详情）。 */
  function appendToolChip(step, name, argsSummary, requireConfirm) {
    var $chip = $('<div class="ai-tool-chip" data-step="' + step + '">' +
      '<span class="ai-tool-icon">' + (requireConfirm ? "✍" : "🔧") + '</span>' +
      '<span class="ai-tool-name"></span>' +
      '<span class="ai-tool-args"></span>' +
      '<span class="ai-tool-status">…</span>' +
      '<span class="ai-tool-detail"></span>' +
      '</div>');
    $chip.find(".ai-tool-name").text(name);
    $chip.find(".ai-tool-args").text(argsSummary ? "(" + argsSummary + ")" : "");
    if (requireConfirm) $chip.addClass("write");
    $chip.on("click", function () { $chip.toggleClass("expanded"); });
    $chip.appendTo("#ai-chat-messages");
    scrollMessages();
    return $chip;
  }

  function finishToolChip(step, name, ok, resultSummary, durationMs) {
    var $chip = $('#ai-chat-messages .ai-tool-chip[data-step="' + step + '"]').last();
    if (!$chip.length) return;
    $chip.addClass(ok ? "ok" : "fail");
    $chip.find(".ai-tool-status").text(ok ? "✓ " + durationMs + "ms" : "✗");
    $chip.find(".ai-tool-detail").text((ok ? "结果：" : "失败：") + (resultSummary || ""));
    if (!ok) $chip.find(".ai-tool-status").attr("title", resultSummary || "");
    scrollMessages();
  }

  function scrollMessages() {
    var box = document.getElementById("ai-chat-messages");
    if (box) box.scrollTop = box.scrollHeight;
  }

  function loadHistory(conversationId) {
    if (!conversationId) return;
    $.getJSON("/ai/agent/history", { conversationId: conversationId })
      .then(function (raw) {
        var messages;
        try { messages = unwrap(raw) || []; } catch (e) { messages = []; }
        clearMessages();
        messages.forEach(function (m) {
          if (m.role !== "user" && m.role !== "assistant") return;
          appendMessage(m.role, m.content || "");
        });
        scrollMessages();
      });
  }

  // ------------------------------------------------------------------
  // 发送 + SSE 分型事件消费
  // ------------------------------------------------------------------
  function sendMessage() {
    if (sending) return;
    var $input = $("#ai-chat-input");
    var text = $input.val().trim();
    if (!text || !BOOK_ID) return;

    appendMessage("user", text);
    $input.val("");

    window.AICompanion.getPageContextAsync().then(function (pageCtx) {
      streamChat(text, pageCtx);
    });
  }

  function streamChat(message, pageContext) {
    sending = true;
    $("#ai-chat-send").prop("disabled", true);

    var $msg = $('<div class="ai-chat-msg assistant"><span class="ai-chat-typing">...</span></div>')
      .appendTo("#ai-chat-messages");
    scrollMessages();
    var fullText = "";
    var conversationIdFromFinal = null;

    var companion = window.AICompanion || {};
    fetch("/ai/agent/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        conversationId: currentConversationId,
        message: message,
        bookId: BOOK_ID,
        bookTitle: BOOK_META.title,
        authors: BOOK_META.authors || [],
        chapter: typeof companion.getChapter === "function" ? (companion.getChapter() || "") : "",
        pageText: pageContext,
        unfamiliarWords:
          typeof companion.getUnfamiliarWords === "function" ? companion.getUnfamiliarWords() : [],
      }),
    }).then(function (resp) {
      if (!resp.ok) {
        return resp.text().then(function (t) {
          throw new Error(errMessageFrom(t, resp.status));
        });
      }
      var reader = resp.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";

      function pump() {
        reader.read().then(function (result) {
          if (result.done) { finishMessage(); return; }
          buffer += decoder.decode(result.value, { stream: true });
          // SSE 帧：event: <name>\n data: <json>\n\n —— event 行可能先于 data 出现，
          // 也可能没有 event 行（降级兼容旧裸文本流）
          var blocks = buffer.split("\n\n");
          buffer = blocks.pop();
          for (var i = 0; i < blocks.length; i++) {
            handleBlock(blocks[i]);
          }
          pump();
        }).catch(function (err) {
          finishMessage("Error: " + err.message);
        });
      }

      function handleBlock(block) {
        var eventName = null;
        var dataLines = [];
        block.split("\n").forEach(function (line) {
          var trimmed = line.trim();
          if (trimmed.indexOf("event:") === 0) {
            eventName = trimmed.slice(6).trim();
          } else if (trimmed.indexOf("data:") === 0) {
            dataLines.push(trimmed.slice(5).trim());
          }
        });
        if (!dataLines.length) return;
        var payloadText = dataLines.join("\n");
        if (payloadText === "[DONE]") { finishMessage(); return; }
        var obj = null;
        try { obj = JSON.parse(payloadText); } catch (e) { return; }
        var type = eventName || (obj.type || (obj.delta ? "delta" : null));

        switch (type) {
          case "delta":
            var piece = obj.text !== undefined ? obj.text : (obj.data !== undefined ? obj.data : obj.delta);
            fullText += piece || "";
            $msg.html(renderMarkdown(fullText));
            scrollMessages();
            break;
          case "tool_call":
            appendToolChip(obj.step, obj.name, obj.argsSummary, obj.requireConfirm);
            break;
          case "tool_result":
            finishToolChip(obj.step, obj.name, obj.ok, obj.resultSummary, obj.durationMs);
            break;
          case "final":
            conversationIdFromFinal = obj.conversationId || null;
            if (obj.usage && (obj.usage.promptTokens || obj.usage.completionTokens)) {
              var $usage = $('<span class="ai-chat-usage"></span>');
              $usage.text("tokens " + (obj.usage.promptTokens || 0) + "/" + (obj.usage.completionTokens || 0));
              $usage.appendTo($msg);
            }
            break;
          case "error":
            fullText += (fullText ? "\n" : "") + "⚠ " + (obj.message || "AI 服务出错");
            $msg.html(renderMarkdown(fullText));
            scrollMessages();
            break;
          default:
            break;
        }
      }

      pump();
    }).catch(function (err) {
      finishMessage(err.message);
    });

    function finishMessage(errMsg) {
      if (errMsg) {
        var prefix = fullText ? "\n" : "";
        fullText += prefix + "⚠ " + errMsg;
        $msg.html(renderMarkdown(fullText));
      } else if (!fullText) {
        $msg.html('<span class="ai-chat-typing">(no response)</span>');
      }
      sending = false;
      $("#ai-chat-send").prop("disabled", false);
      if (conversationIdFromFinal) {
        var changed = conversationIdFromFinal !== currentConversationId;
        currentConversationId = conversationIdFromFinal;
        persistSelection();
        // 新会话首问：final 带回会话 id，刷新下拉让它出现并选中
        if (changed) loadConversations();
      }
    }
  }

  // ------------------------------------------------------------------
  // 记忆面板 + book 学情
  // ------------------------------------------------------------------
  function toggleMemoryPanel() {
    var $panel = $("#ai-memory-panel");
    $panel.toggleClass("open");
    if ($panel.hasClass("open")) loadMemoryPanel();
  }

  function loadMemoryPanel() {
    loadBookProfile();
    loadMemories();
  }

  function loadBookProfile() {
    var $profile = $("#ai-memory-profile").text("学情加载中…");
    $.getJSON("/ai/agent/book-profile", { bookId: BOOK_ID })
      .then(function (raw) {
        var profile;
        try { profile = unwrap(raw); } catch (e) {
          $profile.text("学情暂不可用：" + e.message);
          return;
        }
        if (!profile || !profile.summary) {
          var base = profile && profile.questionCount
            ? "本书已提问 " + profile.questionCount + " 次，学情摘要待生成。"
            : "本书暂无学情记录。";
          $profile.text(base);
          return;
        }
        $profile.empty();
        $('<div class="ai-profile-summary"></div>').text(profile.summary).appendTo($profile);
        var bits = [];
        if (profile.difficulty) bits.push("难度：" + profile.difficulty);
        if (profile.topics && profile.topics.length) bits.push("主题：" + profile.topics.join("、"));
        if (profile.hotWords && profile.hotWords.length) bits.push("高频词：" + profile.hotWords.join("、"));
        if (bits.length) $('<div class="ai-profile-meta"></div>').text(bits.join(" ｜ ")).appendTo($profile);
        if (profile.questionCount) {
          $('<div class="ai-profile-meta"></div>')
            .text("累计提问 " + profile.questionCount + " 次 · 工具调用 " + profile.toolUseCount + " 次")
            .appendTo($profile);
        }
      })
      .fail(function (xhr) {
        $profile.text("学情暂不可用：" + errText(xhr));
      });
  }

  function loadMemories() {
    var $list = $("#ai-memory-list").empty().text("记忆加载中…");
    $.getJSON("/ai/agent/memory")
      .then(function (raw) {
        var memories;
        try { memories = unwrap(raw) || []; } catch (e) {
          $list.text("记忆加载失败：" + e.message);
          return;
        }
        $list.empty();
        if (!memories.length) {
          $list.text("（暂无长期记忆——对话里说「记住…」或在下方面板手动添加）");
          return;
        }
        memories.forEach(function (m) {
          var $item = $('<div class="ai-memory-item"></div>');
          $('<span class="ai-memory-scope"></span>')
            .text(m.bookId && m.bookId !== 0 ? "[本书]" : "[通用]")
            .appendTo($item);
          $('<span class="ai-memory-text"></span>').text(m.memory).appendTo($item);
          var $actions = $('<span class="ai-memory-actions"></span>').appendTo($item);
          $('<button type="button" title="编辑">✎</button>')
            .on("click", function () { editMemory(m); }).appendTo($actions);
          $('<button type="button" title="删除">🗑</button>')
            .on("click", function () { deleteMemory(m); }).appendTo($actions);
          $item.appendTo($list);
        });
      })
      .fail(function (xhr) {
        $list.text("记忆加载失败：" + errText(xhr));
      });
  }

  function addMemory() {
    var $input = $("#ai-memory-input");
    var text = ($input.val() || "").trim();
    if (!text) { window.alert("先写一条要记住的内容"); return; }
    $.ajax({
      url: "/ai/agent/memory/save",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ bookId: BOOK_ID, memory: text }),
    }).then(function (raw) {
      try { unwrap(raw); } catch (e) { window.alert(e.message); return; }
      $input.val("");
      loadMemories();
    }).fail(function (xhr) {
      window.alert("保存失败: " + errText(xhr));
    });
  }

  function editMemory(m) {
    var newText = window.prompt("编辑记忆（清空则取消）", m.memory);
    if (newText === null) return;
    newText = (newText || "").trim();
    if (!newText || newText === m.memory) return;
    $.ajax({
      url: "/ai/agent/memory/save",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ id: m.id, memory: newText }),
    }).then(loadMemories)
      .fail(function (xhr) { window.alert("保存失败: " + errText(xhr)); });
  }

  function deleteMemory(m) {
    if (!window.confirm("删除这条记忆？\n" + m.memory)) return;
    $.ajax({
      url: "/ai/agent/memory/delete",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ id: m.id }),
    }).then(loadMemories)
      .fail(function (xhr) { window.alert("删除失败: " + errText(xhr)); });
  }

  function errMessageFrom(body, status) {
    try {
      var data = JSON.parse(body);
      return data.message || data.error || ("HTTP " + status);
    } catch (e) { return "HTTP " + status; }
  }

  $(init);
})(jQuery);
