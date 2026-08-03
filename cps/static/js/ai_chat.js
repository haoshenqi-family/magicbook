/* AI Companion chat panel logic — multi-conversation.
   - Lists the current book's conversations in a dropdown
   - "+" button creates a new conversation
   - Switching conversations loads that thread's history
   - Sends messages via fetch (streaming SSE) and renders markdown
   - Includes current page context extracted by ai_page_extract.js
   Depends on: jQuery (loaded by reader pages), ai_page_extract.js */
(function ($) {
  "use strict";
  if (!window.AICompanion) return;

  var BOOK_ID = null;
  var BOOK_FORMAT = null;
  var BOOK_META = null;
  var currentConversationId = null;
  var sending = false;

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

  function init() {
    var info = getBookIdFromUrl();
    BOOK_ID = info.id;
    BOOK_FORMAT = info.format;
    BOOK_META = window.AICompanionBookMeta || {};

    $("#ai-companion-fab").on("click", toggleDrawer);
    $("#ai-companion-close").on("click", closeDrawer);
    $("#ai-chat-send").on("click", sendMessage);
    $("#ai-chat-new").on("click", newConversation);
    $("#ai-chat-conversations").on("change", function () {
      selectConversation(parseInt($(this).val(), 10));
    });
    $("#ai-chat-input").on("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    loadConversations();
  }

  function toggleDrawer() {
    $("#ai-companion-drawer").toggleClass("open");
  }
  function closeDrawer() {
    $("#ai-companion-drawer").removeClass("open");
  }

  function loadConversations() {
    if (!BOOK_ID) return;
    $.getJSON("/ai/conversations/" + BOOK_ID, function (data) {
      var convs = data.conversations || [];
      var $sel = $("#ai-chat-conversations").empty();
      convs.forEach(function (c) {
        $sel.append($("<option>").val(c.id).text(c.title + (c.message_count ? " (" + c.message_count + ")" : "")));
      });
      if (!convs.length) {
        newConversation();
        return;
      }
      // Prefer the previously active conversation, else the newest one.
      var preferred = parseInt(localStorage.getItem(storageKey()) || "", 10);
      var target = convs.some(function (c) { return c.id === preferred; }) ? preferred : convs[0].id;
      selectConversation(target);
    });
  }

  function newConversation() {
    if (!BOOK_ID) return;
    $.ajax({
      url: "/ai/conversations/" + BOOK_ID,
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ book_format: BOOK_FORMAT }),
    }).then(function (res) {
      var id = res.conversation_id;
      // Insert the fresh thread at the top of the dropdown and select it.
      var $sel = $("#ai-chat-conversations");
      $sel.prepend($("<option>").val(id).text(res.title || "新会话"));
      $sel.val(id);
      currentConversationId = id;
      persistSelection();
      clearMessages();
    });
  }

  function selectConversation(conversationId) {
    if (!conversationId) return;
    currentConversationId = conversationId;
    persistSelection();
    $("#ai-chat-conversations").val(conversationId);
    loadHistory(conversationId);
  }

  function persistSelection() {
    try { localStorage.setItem(storageKey(), String(currentConversationId)); } catch (e) {}
  }

  function clearMessages() {
    $("#ai-chat-messages").empty();
  }

  function loadHistory(conversationId) {
    if (!conversationId) return;
    $.getJSON("/ai/history/" + conversationId, function (data) {
      clearMessages();
      (data.messages || []).forEach(function (m) {
        appendMessage(m.role, m.content);
      });
      scrollMessages();
    });
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

  function scrollMessages() {
    var box = document.getElementById("ai-chat-messages");
    if (box) box.scrollTop = box.scrollHeight;
  }

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

    fetch("/ai/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        book_id: BOOK_ID,
        book_format: BOOK_FORMAT,
        conversation_id: currentConversationId,
        message: message,
        page_context: pageContext,
        book_title: BOOK_META.title,
        book_authors: BOOK_META.authors,
        book_description: BOOK_META.description,
        book_tags: BOOK_META.tags,
      }),
    }).then(function (resp) {
      if (!resp.ok) {
        return resp.text().then(function (t) {
          throw new Error("HTTP " + resp.status + ": " + t);
        });
      }
      var reader = resp.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";

      function pump() {
        reader.read().then(function (result) {
          if (result.done) { finishMessage(); return; }
          buffer += decoder.decode(result.value, { stream: true });
          var lines = buffer.split("\n");
          buffer = lines.pop();
          for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (line.indexOf("data:") !== 0) continue;
            var payload = line.slice(5).trim();
            if (payload === "[DONE]") { finishMessage(); return; }
            try {
              var obj = JSON.parse(payload);
              if (obj.delta) {
                fullText += obj.delta;
                $msg.html(renderMarkdown(fullText));
                scrollMessages();
              }
              if (obj.error) {
                fullText += "\n[Error: " + obj.error + "]";
                $msg.html(renderMarkdown(fullText));
              }
            } catch (e) { /* ignore parse errors on partial chunks */ }
          }
          pump();
        }).catch(function (err) {
          finishMessage("Error: " + err.message);
        });
      }
      pump();
    }).catch(function (err) {
      finishMessage("Error: " + err.message);
    });

    function finishMessage(errMsg) {
      if (errMsg && !fullText) {
        $msg.html('<span class="ai-chat-typing">' + errMsg + '</span>');
      } else if (!fullText) {
        $msg.html('<span class="ai-chat-typing">(no response)</span>');
      }
      sending = false;
      $("#ai-chat-send").prop("disabled", false);
      // Refresh the dropdown (the active thread title may have changed).
      loadConversations();
    }
  }

  $(init);
})(jQuery);
