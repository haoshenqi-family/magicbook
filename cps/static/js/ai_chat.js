/* AI Companion chat panel logic — agent 模式（moon-well 宿主）。
   - 会话列表/历史/改名/删除走 /ai/agent/* 薄代理（数据源 moon-well MySQL）
   - SSE 分型事件：delta 正文打字机 / tool_call+tool_result 工具芯片 / final 收尾 / error 错误条
   - 降级兼容：事件无 event: 行（旧裸文本流）时按 delta 渲染
   - 记忆面板：查/改/删本人长期记忆 + book 学情摘要
   Depends on: jQuery (loaded by reader pages), ai_page_extract.js */
(function ($) {
  "use strict";
  // R112: i18n 取词（种子缺失时回退 msgid 本身）
  var mbT = window.mbT || function (id) { return id; };
  // R227：上面的 mbT 在脚本载入时就被固定成恒等函数——layout.html 的 i18n_seed
  // 在本文件之后 include，读模块时 window.mbT 还不存在。既有文案因此恒回英文
  //（见 LLD 遗留项，单独一轮处理）。新加的语音文案必须调用时取词，否则新词条
  // 等于没加：用户点「朗读」得到的还是英文。
  function t(id) {
    return typeof window.mbT === "function" ? window.mbT(id) : id;
  }
  if (!window.AICompanion) return;

  var BOOK_ID = null;
  var BOOK_META = null;
  var currentConversationId = null;
  var sending = false;
  var deleting = false;
  // R227：语音输入（麦克风按钮）与朗读（每条回复）的页面级状态
  var micBtnEl = null;
  var voiceStatusTimer = null;
  // R254：邮件是伙伴的独立弹层，只做最近 5 封的轻量预览；正文没有独立接口，
  // 展开状态留在本页内存，避免重复打开时重复触发已读或丢失已展开卡片。
  var mailPeekLoading = false;
  var mailPeekRecords = [];
  var mailOpenIds = {};
  var mailReadRequested = {};

  function getCsrfToken() {
    // R177：CSRF 单点迁 common/api.js（三形态链式探测，read.html 的隐藏域为第 3 形态）
    return window.MBApi.csrfToken();
  }

  // ------------------------------------------------------------------
  // R227 语音播放基元（伴读工具朗读 + 每条回复朗读共用）
  //
  // Why 不用 <audio src=blob:>：media-src 目前只在阅读页与口语页放行 blob:
  //（R181 / R221 刻意保持的窄面），而 Buddy 面板自 R220 起在全站挂载
  //（layout.html + 三个 read 模板）。用 blob 音频要么改 CSP 全站放行 blob:，
  // 要么「全站可用」在非阅读页静默无声——两个都不对。
  // AudioContext.decodeAudioData 的字节来自 fetch（default-src 已含 'self'），
  // 不受 media-src 约束，播放能力与页面无关，也不再依赖 CSP 放行面。
  // ------------------------------------------------------------------
  var speech = { ctx: null, source: null, btn: null, token: 0 };

  function speechContext() {
    if (!speech.ctx) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      speech.ctx = new Ctx();
    }
    // 点击手势链里创建/恢复：无手势时浏览器把上下文留在 suspended，
    // 届时播不出声，调用方按「被浏览器拦截」提示（与旧 Audio 路径同口径）。
    if (speech.ctx.state === "suspended" && speech.ctx.resume) speech.ctx.resume();
    return speech.ctx;
  }

  function stopSpeech() {
    speech.token += 1;
    if (speech.source) {
      try { speech.source.onended = null; speech.source.stop(); } catch (e) { /* 已结束 */ }
      speech.source = null;
    }
    if (speech.btn) markSpeakButton(speech.btn, false);
    speech.btn = null;
  }

  function fetchSpeechBytes(url, text) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ text: text }),
    }).then(function (response) {
      // 失败体是 moon-well 的 Result 信封（HTTP 500 + {success:false,message}），
      // 典型是「积分不足，无法使用AI功能」。不带出 message 的话前端只能拿到
      // 一段 JSON 字节去 decode，用户看到的是「解码失败」——把计费拒绝伪装成
      // 播放器坏了，比不说更糟（R227）。
      if (response.ok && isAudioResponse(response)) return response.arrayBuffer();
      return response.text().then(function (raw) {
        throw new Error(jsonMessage(raw) || t("Read-aloud audio is unavailable"));
      });
    });
  }

  function isAudioResponse(response) {
    var type = (response.headers.get("Content-Type") || "").toLowerCase();
    return type.indexOf("audio/") === 0 || type.indexOf("application/octet-stream") === 0;
  }

  function jsonMessage(raw) {
    try {
      var data = JSON.parse(raw);
      if (!data) return "";
      return String(data.message || (data.result && data.result.message) || "").trim();
    } catch (e) {
      return "";
    }
  }

  function decodeSpeech(ctx, bytes) {
    return new Promise(function (resolve, reject) {
      // 老 Safari 只有回调形态的 decodeAudioData，Promise 形态会被当成 undefined
      var maybe = ctx.decodeAudioData(bytes, resolve, reject);
      if (maybe && typeof maybe.then === "function") maybe.then(resolve, reject);
    });
  }

  /**
   * R170：播放伴读工具（synthesize_tts）已合成好的朗读。
   *
   * 音频字节不走 SSE：工具在 moon-well 侧已扣过那 1 积分，这里按原文回读**不计费**的缓存
   * 端点取字节。text 必须原样发送——它就是缓存键（trim 后 SHA-256）的输入，前端做任何
   * 「顺手清洗/截断」都会 miss。
   *
   * 失败一律交给 onError 显示，绝不静默：用户听到的「AI 说读了但没声音」和被吞掉的
   * 自动播放拒绝，都只会变成一句「功能坏了」的报障，排查成本远高于这里多打一行提示。
   */
  function playCachedSpeech(text, onError) {
    if (!text) {
      if (onError) onError(mbT("Nothing to read"));
      return;
    }
    stopSpeech();
    var ctx = speechContext();
    if (!ctx) {
      if (onError) onError(t("Read-aloud audio is unavailable"));
      return;
    }
    var token = speech.token;
    fetchSpeechBytes("/ajax/reading-tts-cached", text).then(function (bytes) {
      if (token !== speech.token) return null;
      return decodeSpeech(ctx, bytes);
    }).then(function (buffer) {
      if (!buffer || token !== speech.token) return;
      if (ctx.state === "suspended") {
        if (onError) onError(mbT("Browser blocked auto-play, interact with the page first"));
        return;
      }
      var source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      speech.source = source;
      source.start(0);
    }).catch(function (err) {
      if (onError) onError(err.message || String(err));
    });
  }

  // ------------------------------------------------------------------
  // R227 每条回复朗读：/tts/speak（1 积分/次）按段合成，顺序播放
  // ------------------------------------------------------------------
  // /tts/speak 单次上限 2000 字（magicbook 代理与 moon-well 双端校验），1800 留余量。
  // 先按空行分段，段仍超长再按句末标点切，最后才硬切——不把半句话读成两条。
  var SPEECH_SEGMENT_MAX = 1800;

  function splitForSpeech(text) {
    var normalized = String(text || "").replace(/\r\n/g, "\n").trim();
    if (!normalized) return [];
    var out = [];
    normalized.split(/\n{2,}/).forEach(function (para) {
      para = para.trim();
      if (!para) return;
      if (para.length <= SPEECH_SEGMENT_MAX) { out.push(para); return; }
      var sentences = para.match(/[^.!?。！？；;]+[.!?。！？；;]*/g) || [para];
      var current = "";
      sentences.forEach(function (sentence) {
        if (sentence.length > SPEECH_SEGMENT_MAX) {
          if (current) { out.push(current); current = ""; }
          for (var i = 0; i < sentence.length; i += SPEECH_SEGMENT_MAX) {
            out.push(sentence.slice(i, i + SPEECH_SEGMENT_MAX));
          }
          return;
        }
        if (current && (current + sentence).length > SPEECH_SEGMENT_MAX) {
          out.push(current);
          current = "";
        }
        current += sentence;
      });
      if (current) out.push(current);
    });
    return out;
  }

  /** 朗读正文取自渲染后的 DOM：工具芯片、思考占位、朗读按钮都不是回答。 */
  function speechTextOf($msg) {
    var $clone = $msg.clone();
    $clone.find(".ai-tool-chip, .ai-chat-typing, .ai-chat-speak").remove();
    // renderMarkdown 把换行渲染成 <br>、代码块渲染成 <pre>；直接 text() 会把它们
    // 拼成一整行（"line oneLine two"），TTS 既没有停顿还会粘词，故先还原成换行。
    $clone.find("br").replaceWith("\n");
    $clone.find("p, pre, li, blockquote, h1, h2, h3, h4, h5, h6, tr").each(function () {
      $(this).append("\n");
    });
    var text = ($clone.text() || "").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
    return text.split("\n").filter(function (line) {
      return line.trim().indexOf("⚠") !== 0;
    }).join("\n").trim();
  }

  function markSpeakButton(btn, playing) {
    if (!btn) return;
    var label = btn.querySelector(".ai-speak-label");
    var text = playing ? t("Stop reading aloud") : t("Read reply aloud");
    btn.classList.toggle("is-playing", !!playing);
    if (label) label.textContent = text;
    btn.setAttribute("aria-label", text);
    btn.title = text;
  }

  function attachSpeakButton($msg) {
    if (!$msg || !$msg.length) return;
    $msg.find(".ai-chat-speak").remove();
    var text = speechTextOf($msg);
    if (!text) return;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ai-chat-speak";
    var icon = document.createElement("span");
    icon.className = "ai-speak-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "🔊";
    var label = document.createElement("span");
    label.className = "ai-speak-label";
    btn.appendChild(icon);
    btn.appendChild(label);
    markSpeakButton(btn, false);
    btn.addEventListener("click", function () {
      if (btn.classList.contains("is-playing")) { stopSpeech(); return; }
      playReply(text, btn);
    });
    $msg.append(btn);
  }

  function playReply(text, btn) {
    stopSpeech();
    var segments = splitForSpeech(text);
    if (!segments.length) { setVoiceStatus(t("Nothing to read")); return; }
    var ctx = speechContext();
    if (!ctx) { setVoiceStatus(t("Read-aloud audio is unavailable")); return; }

    var token = speech.token;
    speech.btn = btn;
    markSpeakButton(btn, true);

    (function playAt(index) {
      if (token !== speech.token) return;
      if (index >= segments.length) { stopSpeech(); return; }
      if (segments.length > 1) {
        setVoiceStatus(t("Reading… {{n}}/{{m}}")
          .replace("{{n}}", index + 1).replace("{{m}}", segments.length));
      }
      // 走 /ajax/reading-tts（/tts/speak）：不带 bookName/chapter，让 moon-well 把音频
      // 落「AI 临时语音」档（7 天清理），不污染书籍段落的永久缓存。
      fetchSpeechBytes("/ajax/reading-tts", segments[index]).then(function (bytes) {
        if (token !== speech.token) return null;
        return decodeSpeech(ctx, bytes);
      }).then(function (buffer) {
        if (!buffer || token !== speech.token) return;
        var source = ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(ctx.destination);
        speech.source = source;
        source.onended = function () { playAt(index + 1); };
        source.start(0);
      }).catch(function (err) {
        if (token !== speech.token) return;
        stopSpeech();
        setVoiceStatus("⚠ " + (err.message || String(err)));
      });
    })(0);
  }

  /** 语音/朗读状态行：屏幕可见，不在控制台里烂掉。 */
  function setVoiceStatus(text) {
    var node = document.getElementById("ai-chat-voice-status");
    if (!node) return;
    node.textContent = text || "";
    if (voiceStatusTimer) { clearTimeout(voiceStatusTimer); voiceStatusTimer = null; }
    if (text) {
      voiceStatusTimer = setTimeout(function () {
        node.textContent = "";
        voiceStatusTimer = null;
      }, 6000);
    }
  }

  function initVoiceInput() {
    var api = window.MBLearningVoice;
    micBtnEl = document.getElementById("ai-chat-mic");
    if (!micBtnEl || !api) return;
    api.attach({
      micBtn: micBtnEl,
      statusEl: document.getElementById("ai-chat-voice-status"),
      // 本站代理路由（与学习页同一条），面板不载 learningUrls，显式给死值
      asrUrl: "/ajax/learning/asr/transcribe",
      onRecording: function (recording) {
        if (sending) return;   // 发送中不接受新转写，避免和上一条的落库打架
        var text = String((recording && recording.text) || "").trim();
        if (!text) return;
        var $input = $("#ai-chat-input");
        var current = String($input.val() || "").replace(/\s+$/, "");
        // 有草稿时追加而不是覆盖：用户常常先打一半再补一句口头描述
        $input.val(current ? current + " " + text : text);
        var el = $input.get(0);
        if (el) {
          el.focus();
          try { el.setSelectionRange(el.value.length, el.value.length); } catch (e) {}
        }
        setVoiceStatus(t("Transcript ready — edit it before sending"));
      },
    });
  }

  function getBookIdFromUrl() {
    var m = window.location.pathname.match(/\/read\/(\d+)\/([A-Za-z0-9]+)/);
    if (m) return { id: parseInt(m[1], 10), format: m[2] };
    return { id: null, format: null };
  }

  function storageKey() {
    return "calibre.ai.conv." + (BOOK_ID || "site");
  }

  /** moon-well Result 包装解包：{success, result, message} → result（失败时抛错）。 */
  // R177（架构评审 B5）：解包/CSRF 单点迁至 common/api.js。unwrapResult 为原
  // unwrap 的容错超集——非信封响应（登录页/网关错误）不再误入解包分支；失败
  // message 仍必须经调用方 catch 呈现（下方各 alert/面板错误行）。
  function unwrap(data) {
    return window.MBApi.unwrapResult(data);
  }

  function init() {
    var info = getBookIdFromUrl();
    BOOK_ID = info.id;
    BOOK_META = window.AICompanionBookMeta || {};

    $("#ai-companion-fab").on("click", function () {
      var target = chooseFabTarget(
        $("#ai-companion-drawer").hasClass("open") || buddyMailIsOpen(),
        currentMailUnreadForRouting());
      if (target === "mail") {
        openBuddyMail();
      } else if (target === "chat") {
        openDrawer();
      } else {
        closeBuddyMail();
        closeDrawer();
      }
    });
    initBuddyFabDrag();
    $("#ai-companion-close").on("click", closeDrawer);
    $("#buddy-mail-close").on("click", closeBuddyMail);
    $("#ai-chat-send").on("click", sendMessage);
    $("#ai-chat-new").on("click", newConversation);
    $("#ai-chat-rename").on("click", renameConversation);
    $("#ai-chat-delete").on("click", deleteConversation);
    $("#ai-chat-memory").on("click", toggleMemoryPanel);
    $("#ai-memory-close").on("click", function () { $("#ai-memory-panel").removeClass("open"); });
    $("#ai-user-profile-save").on("click", saveUserProfile);
    $("#ai-user-profile-clear").on("click", clearUserProfile);
    $("#ai-user-profile-input").on("input", updateUserProfileCount);
    $("#ai-memory-add").on("click", addMemory);
    $("#buddy-mail-mark-all").on("click", markAllBuddyMailRead);
    $("#buddy-mail-retry").on("click", function () { loadBuddyMailPeek(true); });
    if (window.MBMail && typeof window.MBMail.subscribe === "function") {
      window.MBMail.subscribe(syncBuddyMailActions);
    }
    $("#ai-chat-conversations").on("change", function () {
      selectConversation(parseInt($(this).val(), 10));
    });
    $("#ai-chat-input").on("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    // ESC 逐层关闭伙伴浮层。EPUB 划词气泡打开时优先只关气泡（epub.js 的
    // ESC 监听负责）；邮件弹层优先于 AI 抽屉。
    $(document).on("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (window.ReaderTranslation && window.ReaderTranslation.isOpen()) return;
      if (buddyMailIsOpen()) {
        closeBuddyMail();
        return;
      }
      if ($("#ai-companion-drawer").hasClass("open")) closeDrawer();
    });

    applyFormatPlaceholder();
    initFabLabel();
    initBubbles();
    initVoiceInput();
    initBuddyVisibility();
    initRollingReview();
    loadConversations();
    loadBuddyFab();
  }

  function markFabLabelSeen() {
    try { localStorage.setItem("calibre.ai.fabLabelSeen", "1"); } catch (e) {}
    $("#ai-companion-fab").addClass("fab-label-seen");
  }

  function initFabLabel() {
    try {
      if (localStorage.getItem("calibre.ai.fabLabelSeen") === "1") {
        $("#ai-companion-fab").addClass("fab-label-seen");
      }
    } catch (e) {}
  }

  function applyFormatPlaceholder() {
    var fmt = window.AICompanion && window.AICompanion.detectFormat
      ? window.AICompanion.detectFormat()
      : "epub";
    var key = fmt === "pdf" ? "Ask about the current page..."
      : (fmt === "txt" ? "Ask about this text..."
      : (fmt === "site" ? "Ask about this page..." : "Ask about this chapter..."));
    $("#ai-chat-input").attr("placeholder", mbT(key));
  }

  // R215 验收回滚（2026-10-23）：AI 面板恢复为覆盖式抽屉——
  // 桌面 420px 右侧浮层、移动全屏；不再缩正文、不再与译文栏互斥。
  function currentMailUnreadForRouting() {
    return window.MBMail && typeof window.MBMail.getUnreadForRouting === "function"
      ? window.MBMail.getUnreadForRouting() : 0;
  }

  /** 纯函数供真实点击与 Node 守卫共用：null 表示应关闭当前伙伴浮层。 */
  function chooseFabTarget(panelOpen, unread) {
    if (panelOpen) return null;
    return Number(unread) > 0 ? "mail" : "chat";
  }

  function showBuddyMailState(mode, message) {
    $("#buddy-mail-loading").prop("hidden", mode !== "loading");
    $("#buddy-mail-empty").prop("hidden", mode !== "empty");
    $("#buddy-mail-error").prop("hidden", mode !== "error");
    $("#buddy-mail-list").prop("hidden", mode !== "list");
    $("#buddy-mail-footer").prop("hidden", mode === "loading");
    if (mode === "error") {
      $("#buddy-mail-error .buddy-mail-error-text").text(message || t("Failed to load mail"));
    }
    syncBuddyMailActions();
  }

  function syncBuddyMailActions() {
    var mailState = window.MBMail && typeof window.MBMail.getState === "function"
      ? window.MBMail.getState() : null;
    var canMarkAll = !mailPeekLoading && mailState && mailState.status === "ready" &&
      Number(mailState.unreadCount) > 0;
    $("#buddy-mail-mark-all").prop("disabled", !canMarkAll);
  }

  function renderBuddyMailPeek() {
    var host = document.getElementById("buddy-mail-list");
    if (!host) return;
    host.textContent = "";
    if (!mailPeekRecords.length) {
      showBuddyMailState("empty");
      return;
    }
    mailPeekRecords.forEach(function (mail) {
      var card = window.MBMail.buildMailItem(mail, {
        compact: true,
        expanded: !!mailOpenIds[String(mail.id)],
        onOpen: function (mailData, itemApi) {
          var id = String(mailData.id);
          mailOpenIds[id] = true;
          if (!window.MBMail.isUnread(mailData) || mailReadRequested[id]) return;
          mailReadRequested[id] = true;
          window.MBMail.markRead(mailData.id).then(function (result) {
            itemApi.setRead(result.readAt);
            mailPeekRecords.forEach(function (row) {
              if (row.id === mailData.id && !row.readAt) row.readAt = result.readAt || Date.now();
            });
          }).catch(function (error) {
            delete mailReadRequested[id];
            itemApi.setError(error && error.message ? error.message : String(error));
          });
        }
      });
      host.appendChild(card.element);
    });
    showBuddyMailState("list");
  }

  function loadBuddyMailPeek(force) {
    if (!window.MBMail) {
      showBuddyMailState("error", t("Mail is temporarily unavailable"));
      return;
    }
    if (mailPeekLoading && !force) return;
    mailPeekLoading = true;
    showBuddyMailState("loading");
    window.MBMail.refreshUnread().catch(function () { /* count state renders its own error */ });
    window.MBMail.loadPage(1, 5).then(function (page) {
      mailPeekLoading = false;
      mailPeekRecords = (page && page.records) || [];
      renderBuddyMailPeek();
    }).catch(function (error) {
      mailPeekLoading = false;
      showBuddyMailState("error", error && error.message ? error.message : String(error));
    });
  }

  function markAllBuddyMailRead() {
    if (!window.MBMail) return;
    $("#buddy-mail-mark-all").prop("disabled", true);
    window.MBMail.markAllRead().then(function () {
      var now = Date.now();
      mailPeekRecords.forEach(function (mail) {
        if (!mail.readAt && !mail.resolvedAt) mail.readAt = now;
      });
      renderBuddyMailPeek();
    }).catch(function (error) {
      showBuddyMailState("error", error && error.message ? error.message : String(error));
    });
  }

  function buddyMailIsOpen() {
    return $("#buddy-mail-popover").hasClass("open");
  }

  function openBuddyMail(force) {
    var $popover = $("#buddy-mail-popover");
    if (!$popover.length) {
      openDrawer();
      return;
    }
    closeDrawer();
    $popover.prop("hidden", false)
      .attr("aria-hidden", "false")
      .addClass("open");
    markFabLabelSeen();
    closeBubbles();
    clearLetterBadge();
    loadBuddyMailPeek(!!force);
  }

  function closeBuddyMail() {
    $("#buddy-mail-popover")
      .removeClass("open")
      .attr("aria-hidden", "true")
      .prop("hidden", true);
  }

  function openDrawer() {
    closeBuddyMail();
    $("#ai-companion-drawer").addClass("open");
    markFabLabelSeen();
    closeBubbles();
    clearLetterBadge();
    if ($("#ai-memory-panel").hasClass("open")) loadMemoryPanel();
  }

  function closeDrawer() {
    $("#ai-companion-drawer").removeClass("open");
    // 抽屉关掉还在念，用户找不到停止入口——关即停（R227）
    stopSpeech();
  }

  // ------------------------------------------------------------------
  // R206 伙伴头像：把 AI 悬浮按钮换成当前装备伙伴头像（MinIO 匿名直读）。
  // R220 验收现场：个别浏览器扩展会拦跨站图片子资源（ERR_BLOCKED_BY_CLIENT），
  //   页内直连 MinIO 全裂图；改走本站同源代理 /ajax/buddy/image（登录可读）。
  // Why 先探测再切换：图片可能尚未上传到 MinIO（资产上传在部署期），直接设 src
  //   会裂图；用 new Image() 预载成功才加 has-buddy，失败/未装备一律保留「AI」文字兜底。
  // ------------------------------------------------------------------
  var fabIdleTimer = null;
  function buddyImageProxyUrl(url) {
    if (!url) { return ""; }
    return "/ajax/buddy/image?src=" + encodeURIComponent(url);
  }

  function loadBuddyFab() {
    $.getJSON("/ajax/buddy/catalog")
      .then(function (raw) {
        var list;
        try { list = unwrap(raw) || []; } catch (e) { return; }
        var equipped = null;
        (list || []).forEach(function (b) { if (b.equipped) { equipped = b; } });
        var imageUrl = equipped && (equipped.fullImageUrl || equipped.imageUrl);
        var proxiedUrl = buddyImageProxyUrl(imageUrl);
        if (!proxiedUrl) { return; }
        var probe = new Image();
        probe.onload = function () {
          $("#ai-companion-fab-img").attr("src", proxiedUrl);
          $("#ai-companion-fab").addClass("has-buddy");
          startFabIdle();
        };
        probe.onerror = function () { /* 图片未就绪：保留文字兜底 */ };
        probe.src = proxiedUrl;
      })
      .fail(function () { /* 代理不可达：静默保留文字兜底 */ });
  }

  // Keep the floating buddy reachable on small screens and remember its position per browser.
  function initBuddyFabDrag() {
    // R223 定位/拖拽迁到 wrap：按钮本体透明化后仍需一块固定命中区。
    var button = document.getElementById("ai-companion-fab-wrap");
    if (!button || !window.PointerEvent) return;
    var key = "calibre.ai.buddy.position";
    var edgeGap = 10;
    // 头像 img 的原生拖拽会中断 pointer 流；draggable=false 为主，这里兜底旧缓存。
    button.addEventListener("dragstart", function (event) {
      event.preventDefault();
    });
    var saved;
    try { saved = JSON.parse(localStorage.getItem(key) || "null"); } catch (e) { saved = null; }
    if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) {
      var initial = snapFabPosition(button, saved.x, saved.y, edgeGap);
      button.style.left = initial.x + "px";
      button.style.top = initial.y + "px";
      button.style.right = "auto";
      button.style.bottom = "auto";
    }
    var startX, startY, originX, originY, moved = false;
    button.addEventListener("pointerdown", function (event) {
      if (event.button !== 0) return;
      button.classList.remove("buddy-snapping");
      closeBubbles();
      var rect = button.getBoundingClientRect();
      startX = event.clientX; startY = event.clientY;
      originX = rect.left; originY = rect.top; moved = false;
      // 不能在 pointerdown 就捕获：捕获会把后续 click 重定向到 wrap，
      // FAB 与气泡的 click 全部失效；捕获延迟到真正开始拖动时设置。
    });
    button.addEventListener("pointermove", function (event) {
      if (!(event.buttons & 1)) return; // 未按住左键的移动（含悬停）不拖拽
      var dx = event.clientX - startX, dy = event.clientY - startY;
      if (!moved) {
        if (Math.hypot(dx, dy) < 6) return;
        moved = true;
        button.setPointerCapture(event.pointerId);
      }
      var x = Math.max(0, Math.min(window.innerWidth - button.offsetWidth, originX + dx));
      var y = Math.max(0, Math.min(window.innerHeight - button.offsetHeight, originY + dy));
      button.style.left = x + "px"; button.style.top = y + "px";
      button.style.right = "auto"; button.style.bottom = "auto";
    });
    button.addEventListener("pointerup", function (event) {
      if (button.hasPointerCapture(event.pointerId)) button.releasePointerCapture(event.pointerId);
      if (moved) {
        event.preventDefault();
        var rect = button.getBoundingClientRect();
        var snapped = snapFabPosition(button, rect.left, rect.top, edgeGap);
        button.classList.add("buddy-snapping");
        button.style.left = snapped.x + "px";
        button.style.top = snapped.y + "px";
        try { localStorage.setItem(key, JSON.stringify(snapped)); } catch (e) {}
        button.dataset.dragged = "1";
        setTimeout(function () { delete button.dataset.dragged; }, 0);
      }
    });
    button.addEventListener("click", function (event) {
      if (button.dataset.dragged) { event.stopImmediatePropagation(); event.preventDefault(); }
    }, true);
  }

  function snapFabPosition(button, x, y, gap) {
    var maxX = Math.max(gap, window.innerWidth - button.offsetWidth - gap);
    var maxY = Math.max(gap, window.innerHeight - button.offsetHeight - gap);
    return {
      x: x + button.offsetWidth / 2 < window.innerWidth / 2 ? gap : maxX,
      y: Math.max(gap, Math.min(maxY, y)),
    };
  }

  // ------------------------------------------------------------------
  // R223 hover 快捷气泡（类 iPhone 悬浮球）：动作集 /buddy 可配置；
  // 阅读页动作直接转发到顶栏同 ID 工具（原节点监听仍生效），站点页为导航；
  // 「对话」恒在最内圈，点击即开抽屉。配置加载失败回落默认四项。
  // 展开方向按 FAB 吸附位置自适应（iPhone 悬浮球同款）：朝屏幕内侧展开，
  // 顶/底边距不足时整体下/上偏，保证气泡不伸出屏幕。
  // ------------------------------------------------------------------
  var BUBBLE_ICONS = {
    chat: "💬", "immersive-translate": "译", "tts-book": "▶",
    bookmark: "🔖", learning: "🎓", library: "📚", me: "👤",
  };
  // 延迟关闭定时器：FAB 与气泡间有空隙，鼠标穿越时会短暂 mouseleave。
  var bubbleCloseTimer = null;

  function bubbleHost() { return document.getElementById("ai-companion-bubbles"); }

  function closeBubbles() {
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (wrap) wrap.classList.remove("bubbles-open");
  }

  // 朗读气泡是「播放/停止」双态，而非只有起播。状态唯一源是顶栏按钮：
  // 阅读器 ttsButtonsRender 在播放中给 #tts-book 加 active 并显示 #tts-book-stop，
  // 起播、暂停、自然播完、点停止都会更新它——不另建一份本地状态，避免与播放器漂移。
  function readingAloudActive() {
    var tool = document.getElementById("tts-book");
    var stopBtn = document.getElementById("tts-book-stop");
    if (!tool) return false;
    return tool.classList.contains("active")
      || !!(stopBtn && stopBtn.style.display !== "none");
  }

  function syncTtsBubble() {
    var bubble = document.querySelector('.ai-bubble[data-action="tts-book"]');
    if (!bubble) return;
    var playing = readingAloudActive();
    var icon = bubble.querySelector(".ai-bubble-icon");
    var tip = bubble.querySelector(".ai-bubble-tip");
    bubble.classList.toggle("is-playing", playing);
    if (icon) icon.textContent = playing ? "■" : (BUBBLE_ICONS["tts-book"] || "▶");
    var label = playing ? (window.mbT ? mbT("Stop reading aloud") : "Stop reading aloud")
                        : (window.mbT ? mbT("Read aloud") : "Read aloud");
    if (tip) tip.textContent = label;
    bubble.setAttribute("aria-label", label);
    bubble.title = label;
  }

  function dispatchBubbleAction(id) {
    if (id === "chat") {
      // 快捷气泡的语义固定是“对话”。有未读时也不能复用 FAB 的 Mail 分流。
      openDrawer("chat");
      return;
    }
    // 朗读中直接停止：顶栏的 ▶ 在播放时是「暂停」，用户要的是一键停掉。
    if (id === "tts-book" && readingAloudActive()) {
      var stopBtn = document.getElementById("tts-book-stop");
      if (stopBtn) { stopBtn.click(); return; }
    }
    var tool = document.getElementById(id);
    if (tool) { tool.click(); return; }
    var routes = { learning: "/learning", library: "/", me: "/me" };
    if (routes[id]) { window.location.href = routes[id]; }
  }

  function renderBubbles(selected, available) {
    var host = bubbleHost();
    if (!host) return;
    host.innerHTML = "";
    var labels = {};
    (available || []).forEach(function (a) { labels[a.id] = a.label; });
    var ordered = ["chat"].concat((selected || []).filter(function (a) { return a !== "chat"; }));
    ordered.forEach(function (id, i) {
      var bubble = document.createElement("button");
      bubble.type = "button";
      bubble.className = "ai-bubble";
      bubble.dataset.action = id;
      bubble.setAttribute("aria-label", labels[id] || id);
      var tip = document.createElement("span");
      tip.className = "ai-bubble-tip";
      tip.textContent = labels[id] || id;
      bubble.appendChild(tip);
      var icon = document.createElement("span");
      icon.className = "ai-bubble-icon";
      icon.textContent = BUBBLE_ICONS[id] || "•";
      bubble.appendChild(icon);
      bubble.addEventListener("click", function (event) {
        event.stopPropagation();
        closeBubbles();
        dispatchBubbleAction(id);
      });
      host.appendChild(bubble);
    });
    syncTtsBubble();
  }

  function openBubbles() {
    if (bubbleCloseTimer) { clearTimeout(bubbleCloseTimer); bubbleCloseTimer = null; }
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (!wrap) return;
    var host = bubbleHost();
    if (host && host.children.length) {
      var rect = wrap.getBoundingClientRect();
      var centerX = rect.left + rect.width / 2;
      var centerY = rect.top + rect.height / 2;
      var clearRadius = 94; // 气泡半径 + 展开半径的余量
      var inward = centerX > window.innerWidth / 2 ? -1 : 1;
      var vertical = centerY < clearRadius ? -1 : (window.innerHeight - centerY < clearRadius ? 1 : 0);
      // 顶/底空间不足时往反方向让位。屏幕方向向量 (dx,dy)=(inward,-vertical)；
      // 气泡位移按 (cos a, -sin a) 存（数学角），故 a = -atan2(dy, dx)。
      var baseDeg = vertical
        ? -Math.atan2(-vertical, inward) * 180 / Math.PI
        : (inward < 0 ? 180 : 0);
      var spread = vertical ? 90 : 120;
      var count = host.children.length;
      Array.prototype.forEach.call(host.children, function (bubble, i) {
        var off = count > 1 ? (i / (count - 1) - 0.5) * spread : 0;
        var angle = (baseDeg + off) * Math.PI / 180;
        bubble.style.setProperty("--bx", Math.round(Math.cos(angle) * 74) + "px");
        bubble.style.setProperty("--by", Math.round(-Math.sin(angle) * 74) + "px");
      });
      wrap.classList.toggle("bubbles-left", inward > 0);
      syncTtsBubble();
    }
    wrap.classList.add("bubbles-open");
  }

  function initBubbles() {
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (!wrap) return;
    $.getJSON("/ajax/buddy/quick-actions")
      .then(function (raw) {
        var data = unwrap(raw) || {};
        renderBubbles(data.selected, data.available);
      })
      .fail(function () {
        renderBubbles(["chat", "immersive-translate", "tts-book", "bookmark"], []);
      });
    wrap.addEventListener("mouseenter", openBubbles);
    function scheduleClose() {
      if (bubbleCloseTimer) clearTimeout(bubbleCloseTimer);
      bubbleCloseTimer = setTimeout(function () {
        bubbleCloseTimer = null; closeBubbles();
      }, 350);
    }
    wrap.addEventListener("mouseleave", scheduleClose);
    wrap.addEventListener("focusin", openBubbles);
    wrap.addEventListener("focusout", closeBubbles);
    document.addEventListener("click", function (event) {
      if (wrap.classList.contains("bubbles-open") && !wrap.contains(event.target)) {
        closeBubbles();
      }
    });
    // 播放状态由阅读器更新，气泡只在开启期间巡检；离开阅读页无 #tts-book 时为空转。
    var ttsSyncTimer = setInterval(syncTtsBubble, 250);
    window.addEventListener("pagehide", function () { clearInterval(ttsSyncTimer); });
  }

  function startFabIdle() {
    if (fabIdleTimer) { return; }
    function resetIdle() {
      if (fabIdleTimer) { clearTimeout(fabIdleTimer); }
      fabIdleTimer = setTimeout(function () {
        if (!$("#ai-companion-fab").hasClass("buddy-thinking")) {
          $("#ai-companion-fab").addClass("buddy-sleep");
        }
      }, 45000);
    }
    $(document).on("mousemove keydown click", function () {
      $("#ai-companion-fab").removeClass("buddy-sleep");
      resetIdle();
    });
    resetIdle();
  }

  // ------------------------------------------------------------------
  // R244 伙伴消失/复原动画 + 收信动画钩子。
  // 消失＝用户点悬浮球上的隐藏 ✕，播一段金光消散后收起，右缘留一枚唤回小标签（可逆）；
  // 隐藏态记进 localStorage，跨页保持。收信＝纯展示层：金色信封飞入球心、球轻 peek、
  // 落一个未读角标（开抽屉即清）。本轮不接数据源，暴露 window.AICompanion.showLetter()
  // 与自定义事件 'mb:buddy-letter'，供未来站内信（R243）在有信时调用。
  // ------------------------------------------------------------------
  var BUDDY_HIDDEN_KEY = "calibre.ai.buddy.hidden";
  var BUDDY_ANIM_MS = 700;   // 动画时长兜底：reduced-motion 或 animationend 丢失时仍能落定

  function buddyReducedMotion() {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function setRestoreTab(on) {
    var tab = document.getElementById("ai-companion-restore");
    if (tab) tab.hidden = !on;
  }

  function hideBuddy() {
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (!wrap || wrap.classList.contains("buddy-hidden")) return;
    closeBubbles();
    var done = function () {
      wrap.classList.remove("buddy-vanishing");
      wrap.classList.add("buddy-hidden");
      setRestoreTab(true);
      syncLetterBadge();
      try { localStorage.setItem(BUDDY_HIDDEN_KEY, "1"); } catch (e) {}
    };
    if (buddyReducedMotion()) { done(); return; }
    wrap.classList.add("buddy-vanishing");
    var fired = false;
    var finish = function () { if (!fired) { fired = true; done(); } };
    var fab = document.getElementById("ai-companion-fab");
    fab.addEventListener("animationend", finish, { once: true });
    setTimeout(finish, BUDDY_ANIM_MS);
  }

  function restoreBuddy() {
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (!wrap) return;
    setRestoreTab(false);
    clearLetterBadge();
    wrap.classList.remove("buddy-hidden");
    try { localStorage.setItem(BUDDY_HIDDEN_KEY, "0"); } catch (e) {}
    if (buddyReducedMotion()) return;
    wrap.classList.add("buddy-appearing");
    var cleared = false;
    var clr = function () { if (!cleared) { cleared = true; wrap.classList.remove("buddy-appearing"); } };
    var fab = document.getElementById("ai-companion-fab");
    fab.addEventListener("animationend", clr, { once: true });
    setTimeout(clr, BUDDY_ANIM_MS);
  }

  function initBuddyVisibility() {
    var hidden = false;
    try { hidden = localStorage.getItem(BUDDY_HIDDEN_KEY) === "1"; } catch (e) {}
    if (hidden) {
      var wrap = document.getElementById("ai-companion-fab-wrap");
      if (wrap) wrap.classList.add("buddy-hidden");
      setRestoreTab(true);
    }
    $("#ai-companion-hide").on("click", function (e) { e.stopPropagation(); hideBuddy(); });
    $("#ai-companion-restore").on("click", restoreBuddy);
  }

  // ------------------------------------------------------------------
  // R285 滚动复习：FAB 头顶的纯文字词卡轮播（不出声、不计费）。
  // R289 演进：正文从「义项+原句」升级为单词详情分页轮播——每词只显示一部分，
  // 每页钳在 3 行内；数据只来自已缓存详解（REVIEW_DETAILS_URL，零计费零等待），
  // 没有缓存的词保持 R285 简卡。计费红线沿用 R285（见下）。
  //
  // Why 取 SRS 到期队列而不是「最近划词」：用户 2026-11-06 拍板——复习对象以
  // learning_review_schedule 的 due_at <= now 为准（含历史积压），20 个词前端洗牌；
  // 查词历史 vocabulary_study_history 不属本轮范围，不新建表、不写查词记录。
  // Why 不调 /vocabulary/detail/{word}：队列 VO 自带 meaning（中文首义项，上游
  // shortMeanings 只读 ES 缓存）与 contextSentence（阅读原句），两者都不触发 LLM；
  // 详解端点缓存 miss 会现场生成（15~30s 且计费），与「不出声、不计费」冲突。
  // R289 的详情走 /ajax/vocabulary/detail-cached-batch（moon-well R248 只读缓存
  // 批量端点，miss 不出现在结果里），这是唯一与详解沾边的调用，绝不逐词拉详解。
  // Why 不调 /learning/srs/answer：点「认识」复用划词气泡已有的
  // /ajax/reading-word-mark → GET /vocabulary/known/{word}，语义是「毕业/移出队列」，
  // 不写复习日志、不计 x/20；用户确认「算复习」= 这条从轮播里移除。
  // Why 卡片挂在 root 而不是 wrap 内：wrap 上有 mouseenter→openBubbles 与
  // pointerdown→拖拽，放进去会出现「鼠标移到卡片上卡片反而被快捷气泡遮住」，
  // 也会抢走伙伴的拖拽命中区。fixed + 按 FAB rect 算位置可完全解耦。
  // ------------------------------------------------------------------
  var REVIEW_QUEUE_URL = "/ajax/learning/srs/queue"; // 代理不透传 ?limit=，上游默认 20
  var REVIEW_MARK_URL = "/ajax/reading-word-mark";
  // R289 详情分页的数据源：只读缓存批量端点（对端 moon-well R248）。缓存 miss 的词
  // 不在结果里——绝不调 /ajax/reading-word-detail（R123 逐词详解，miss 现场生成
  // 计费 + 15~30s），也不调 /vocabulary/detail/ 逐词路径：轮播翻页不许变成隐藏下单。
  var REVIEW_DETAILS_URL = "/ajax/vocabulary/detail-cached-batch";
  var REVIEW_MAX = 20;
  var REVIEW_INTERVAL_MS = 8000;
  var REVIEW_PAUSED_KEY = "calibre.ai.review.paused";
  var REVIEW_COLLAPSED_KEY = "calibre.ai.review.collapsed";
  // 与 cps/web.py 的 _READING_WORD_RE 同形：不合法词不给一个必然 400 的「认识」按钮。
  var REVIEW_WORD_RE = /^[A-Za-z](?:[A-Za-z'\u2019-]*[A-Za-z])?$/;
  var review = {
    items: [], index: 0, timer: null, loading: false, inFlight: false,
    paused: false, collapsed: false, failed: false, markError: "",
    // R289 详情分页：pages = 归一词 → 页数组（每页 {label, text}，渲染钳在 3 行内），
    // page = 当前词内的页下标。pages 为空 = 简卡回退（ 义项 + 原句 + 出处）。
    pages: {}, page: 0,
  };

  function reviewRoot() { return document.getElementById("ai-companion-review"); }
  function reviewWrap() { return document.getElementById("ai-companion-fab-wrap"); }

  function reviewReadFlag(key) {
    try { return localStorage.getItem(key) === "1"; } catch (e) { return false; }
  }
  function reviewWriteFlag(key, on) {
    try { localStorage.setItem(key, on ? "1" : "0"); } catch (e) {}
  }
  function reviewMessage(raw, fallback) { return jsonMessage(raw) || t(fallback); }
  function reviewSetText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value == null ? "" : String(value);
  }
  function reviewCurrent() {
    return review.items.length ? review.items[review.index % review.items.length] : null;
  }
  function reviewShuffled(list) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  // ------------------------------------------------------------------
  // R289 详情分页：词卡正文从「义项+原句」升级为单词详情，但每次只显示一页、
  // 页面钳在 3 行内（CSS line-clamp 兜底）。数据只来自已缓存详解（零计费）。
  //
  // Why 每词只展示「基本意思 + 一个随机模块」（用户 2026-11-08 拍板）：六板块全上
  // 一个词要停 30~60 秒，滚动复习是路过瞄一眼的被动卡片，太长就成了阅读任务。
  // 随机在队列加载时定一次，同一轮内稳定，下次拉队列重新洗。
  // Why 页宽按 ~60 个中文字切：280px 卡约 21 中文字/行，3 行 ≈ 63 字；超宽由
  // line-clamp 兜底截断，正常内容不会被切字。
  // ------------------------------------------------------------------
  function reviewWordKey(word) {
    // 与代理/上游的归一口径一致（trim → 弯撇号转直撇号 → 小写），pages 按此键存取。
    return String(word || "").trim().replace(/\u2019/g, "'").toLowerCase();
  }

  function reviewModuleLabel(kind) {
    var labels = {
      etymology: t("Etymology"), phrases: t("Collocations"), forms: t("Word forms"),
      synonyms: t("Synonyms"), antonyms: t("Antonyms"), slang: t("Slang"),
      funFacts: t("Fun facts"),
    };
    return labels[kind] || "";
  }

  function reviewPushModulePage(pages, kind, text) {
    var body = String(text || "").trim();
    if (!body) return;
    pages.push({ label: reviewModuleLabel(kind), text: body });
  }

  // 词源是一整段：按句切、约 60 字装一页，最多 2 页（避免长词源霸屏）。
  function reviewAppendEtymologyPages(pages, etymology) {
    var sentences = String(etymology).match(/[^。！？!?]+[。！？!?]?/g) || [];
    var buf = "";
    var count = 0;
    for (var i = 0; i < sentences.length && count < 2; i++) {
      var s = sentences[i].trim();
      if (!s) continue;
      if (buf && (buf + s).length > 60) {
        reviewPushModulePage(pages, "etymology", buf);
        count += 1;
        buf = "";
      }
      buf = buf ? buf + s : s;
    }
    if (buf && count < 2) reviewPushModulePage(pages, "etymology", buf);
  }

  // 从非空板块里随机挑一个，装配 ≤2 页。各板块的取材口径见 R289 LLD。
  function reviewAppendModulePages(pages, kind, detail) {
    if (kind === "etymology") {
      reviewAppendEtymologyPages(pages, detail.etymology);
      return;
    }
    if (kind === "phrases" || kind === "slang") {
      var items = (detail[kind] || []).slice(0, 2);
      for (var i = 0; i < items.length; i++) {
        var it = items[i] || {};
        var text = kind === "phrases"
          ? [it.phrase, it.meaning].filter(Boolean).join("　")
          : [it.meaning, it.example].filter(Boolean).join("\n");
        reviewPushModulePage(pages, kind, text);
      }
      return;
    }
    if (kind === "forms") {
      var lines = (detail.forms || []).slice(0, 6).map(function (f) {
        if (!f || !f.form) return "";
        return f.form + (f.type ? "（" + f.type + "）" : "");
      }).filter(Boolean);
      if (lines.length) reviewPushModulePage(pages, "forms", lines.join("\n"));
      return;
    }
    if (kind === "synonyms" || kind === "antonyms") {
      var names = (detail[kind] || []).slice(0, 8).map(function (w) {
        return w && w.word;
      }).filter(Boolean);
      if (names.length) reviewPushModulePage(pages, kind, names.join("、"));
      return;
    }
    if (kind === "funFacts") {
      var facts = (detail.funFacts || []).slice(0, 2);
      for (var j = 0; j < facts.length; j++) reviewPushModulePage(pages, "funFacts", facts[j]);
    }
  }

  // 页装配总入口：基本意思（前 2 个义项）+ 随机模块（≤2 页），单词总数 ≤4。
  function reviewDetailPages(detail) {
    var pages = [];
    if (!detail || typeof detail !== "object") return pages;
    var meanings = Array.isArray(detail.meaning) ? detail.meaning : [];
    for (var i = 0; i < meanings.length && pages.length < 2; i++) {
      var m = meanings[i] || {};
      var line = (m.pos ? m.pos + ". " : "") + String(m.sense || "").trim();
      if (!line) continue;
      if (m.example) line += "\n" + String(m.example).trim();
      pages.push({ label: "", text: line });
    }
    var pool = [];
    if (detail.etymology && String(detail.etymology).trim()) pool.push("etymology");
    if (Array.isArray(detail.phrases) && detail.phrases.length) pool.push("phrases");
    if (Array.isArray(detail.forms) && detail.forms.length) pool.push("forms");
    if (Array.isArray(detail.synonyms) && detail.synonyms.length) pool.push("synonyms");
    if (Array.isArray(detail.antonyms) && detail.antonyms.length) pool.push("antonyms");
    if (Array.isArray(detail.slang) && detail.slang.length) pool.push("slang");
    if (Array.isArray(detail.funFacts) && detail.funFacts.length) pool.push("funFacts");
    if (pool.length) {
      reviewAppendModulePages(pages, pool[Math.floor(Math.random() * pool.length)], detail);
    }
    return pages;
  }

  function reviewPagesFor(item) {
    return review.pages[reviewWordKey(item && item.word)] || null;
  }

  // 队列拉到后批量补详情。失败/空结果都静默回退简卡：详情是增强层，
  // 卡片的核心功能（轮播 + 认识）不依赖它——失败在此处不可见是设计口径，
  // 可观测性由代理端日志承担（vocabulary detail cached batch）。
  function reviewLoadDetails() {
    var api = window.MBApi;
    if (!api || typeof api.postJson !== "function" || !review.items.length) return;
    var words = review.items.map(function (it) { return String(it.word || ""); })
      .filter(Boolean).slice(0, REVIEW_MAX);
    if (!words.length) return;
    api.postJson(REVIEW_DETAILS_URL, { words: words }).then(function (resp) {
      if (!resp.ok) throw new Error("details unavailable");
      var data = unwrap(resp.data);  // Result 信封：success=false 抛上游 message
      if (!data || typeof data !== "object") throw new Error("details unavailable");
      var pages = {};
      review.items.forEach(function (it) {
        var key = reviewWordKey(it.word);
        var built = reviewDetailPages(data[key]);
        if (built.length) pages[key] = built;
      });
      review.pages = pages;
      review.page = 0;
    }).catch(function () {
      review.pages = {};
    }).then(function () { reviewRender(); });
  }

  // 纯展示：任一「用户不在看」或「已有浮层」态都只跳过本次 tick，不重置计时器、
  // 不发请求。页面生命周期内队列只在初始化拉一次，不轮询（R243 口径同源）。
  function reviewPageActive() {
    if (document.visibilityState === "hidden") return false;
    if (document.hasFocus()) return true;
    // EPUB 正文渲染在 iframe 里：焦点进 iframe 后顶层 hasFocus() 可能返回 false，
    // 但用户明明还在读这一页。activeElement 是 IFRAME 就仍算页面内活跃，
    // 只有切到别的窗口/地址栏（activeElement 不是 iframe）才真的暂停。
    var el = document.activeElement;
    return !!(el && el.tagName === "IFRAME");
  }

  function reviewShouldPause() {
    var wrap = reviewWrap();
    var drawer = document.getElementById("ai-companion-drawer");
    var mail = document.getElementById("buddy-mail-popover");
    // inFlight 必须算暂停：标记请求在途时若让 tick 推进 index，回来会删错词（S1）。
    return review.loading || review.failed || review.inFlight || review.paused ||
      review.collapsed || review.items.length === 0 || !reviewPageActive() ||
      (wrap && (wrap.classList.contains("buddy-hidden") ||
                wrap.classList.contains("bubbles-open"))) ||
      (drawer && drawer.classList.contains("open")) ||
      (mail && !mail.hidden);
  }

  // FAB 可拖拽吸附到四边：卡片按 FAB rect 贴右上，左缘吸附时改贴左，
  // 上方空间不足时翻到球下方，避免被视口裁掉或压住伙伴头像。
  function reviewPosition() {
    var root = reviewRoot(), wrap = reviewWrap();
    if (!root || !wrap || root.hidden) return;
    var rect = wrap.getBoundingClientRect();
    var w = root.offsetWidth || 280, h = root.offsetHeight || 150;
    var leftSide = rect.left + rect.width / 2 < window.innerWidth / 2;
    var left = leftSide ? rect.left : rect.right - w;
    left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
    var top = rect.top - h - 12;
    var below = top < 8;
    if (below) top = rect.bottom + 12;
    root.classList.toggle("is-left", leftSide);
    root.classList.toggle("is-below", below);
    root.style.left = Math.round(left) + "px";
    root.style.top = Math.round(top) + "px";
  }

  function reviewShowError(message) {
    review.failed = true;
    reviewSetText("ai-review-error-text", message);
    var err = document.getElementById("ai-review-error");
    if (err) err.hidden = false;
    var body = document.getElementById("ai-review-body");
    if (body) body.hidden = true;
  }

  function reviewClearError() {
    review.failed = false;
    var err = document.getElementById("ai-review-error");
    if (err) err.hidden = true;
    var body = document.getElementById("ai-review-body");
    if (body) body.hidden = false;
  }

  function reviewRender() {
    var root = reviewRoot(), wrap = reviewWrap();
    if (!root) return;
    root.hidden = !!(wrap && wrap.classList.contains("buddy-hidden"));
    if (root.hidden) return;
    root.classList.toggle("is-collapsed", review.collapsed);
    var peek = document.getElementById("ai-review-peek");
    if (peek) {
      peek.hidden = !review.collapsed;
      peek.textContent = review.collapsed ? String(review.items.length) : "";
      peek.title = t("Show review");
      peek.setAttribute("aria-label", t("Show review"));
    }
    if (review.collapsed) { reviewPosition(); return; }

    var toggle = document.getElementById("ai-review-toggle");
    if (toggle) {
      var label = review.paused ? t("Resume review") : t("Pause review");
      toggle.textContent = review.paused ? "▶" : "❚❚";
      toggle.title = label;
      toggle.setAttribute("aria-label", label);
    }
    var collapse = document.getElementById("ai-review-collapse");
    if (collapse) {
      collapse.title = t("Collapse review");
      collapse.setAttribute("aria-label", t("Collapse review"));
    }
    reviewSetText("ai-review-title", t("Rolling review"));
    reviewSetText("ai-review-next", t("Next word"));
    reviewSetText("ai-review-known", t("I know this"));
    reviewSetText("ai-review-retry", t("Retry"));

    var item = reviewCurrent();
    if (!item) {
      reviewSetText("ai-review-progress", "");
      reviewSetText("ai-review-word", "");
      reviewSetText("ai-review-meaning", "");
      reviewSetText("ai-review-context", "");
      reviewSetText("ai-review-source", "");
      reviewSetText("ai-review-detail", "");
      reviewSetText("ai-review-status", review.loading
        ? t("Loading review words…") : t("No words to review right now"));
      var known0 = document.getElementById("ai-review-known");
      var next0 = document.getElementById("ai-review-next");
      if (known0) known0.disabled = true;
      if (next0) next0.disabled = true;
      reviewPosition();
      return;
    }
    // R289 详情页模式：词面常驻，正文显示当前页（≤3 行）；进度带页码。
    // 无详情页的词回退简卡（义项 + 原句 + 出处），两态互斥由 detail 空/非空表达。
    var pages = reviewPagesFor(item);
    var pageNo = 0;
    if (pages && pages.length) {
      pageNo = Math.min(review.page, pages.length - 1);
    }
    reviewSetText("ai-review-progress", (review.index + 1) + "/" + review.items.length +
      (pages && pages.length > 1 ? " · " + (pageNo + 1) + "/" + pages.length : ""));
    // 服务端内容一律 textContent：meaning / contextSentence / 详解六板块都来自 ES，不能拼 HTML。
    reviewSetText("ai-review-word", item.word);
    if (pages && pages.length) {
      var page = pages[pageNo];
      reviewSetText("ai-review-detail", page.label ? page.label + "：" + page.text : page.text);
      reviewSetText("ai-review-meaning", "");
      reviewSetText("ai-review-context", "");
      reviewSetText("ai-review-source", "");
    } else {
      reviewSetText("ai-review-detail", "");
      reviewSetText("ai-review-meaning", item.meaning || "");
      reviewSetText("ai-review-context", item.contextSentence || "");
      reviewSetText("ai-review-source", item.contextBook || "");
    }
    // 「认识」失败的原因要留到用户下一次操作；reviewRender 每次都会重画状态行，
    // 所以错误文案存在 review.markError 里，而不是直接写进 DOM。
    reviewSetText("ai-review-status", review.markError);
    var status = document.getElementById("ai-review-status");
    if (status) status.classList.toggle("is-error", !!review.markError);
    var known = document.getElementById("ai-review-known");
    if (known) {
      var word = String(item.word || "");
      // 后端先归一再校验（strip → 弯撇号转直撇号 → lower），前端照做才不会误禁用。
      var normalized = word.trim().replace(/\u2019/g, "'").toLowerCase();
      var ok = REVIEW_WORD_RE.test(normalized) && normalized.length <= 64;
      known.disabled = !ok || review.inFlight;
      known.title = ok ? t("I know this") : t("This word cannot be marked here");
    }
    var next = document.getElementById("ai-review-next");
    if (next) next.disabled = review.inFlight;
    reviewPosition();
  }

  function reviewTick() {
    if (reviewShouldPause()) return;
    // R289：先在当前词内翻页（若有），翻完才换词。markError 只在换词时清——
    // 「认识」失败的原因属于这个词，翻它的下一页时仍应可见（M3 口径不变）。
    var pages = reviewPagesFor(reviewCurrent());
    if (pages && pages.length && review.page < pages.length - 1) {
      review.page += 1;
    } else {
      review.markError = "";  // 换词就清掉上一条的「认识」失败原因（M3）
      review.index = (review.index + 1) % review.items.length;
      review.page = 0;
    }
    reviewRender();
  }

  function reviewLoad() {
    var root = reviewRoot(), api = window.MBApi;
    if (!root || !api || typeof api.getJson !== "function" || review.loading) return;
    review.loading = true;
    review.markError = "";
    reviewClearError();
    reviewRender();
    api.getJson(REVIEW_QUEUE_URL).then(function (resp) {
      if (!resp.ok) throw new Error(reviewMessage(resp.raw, "Could not load review words"));
      var data = unwrap(resp.data);  // Result 信封：success=false 抛上游 message
      if (!Array.isArray(data)) {
        throw new Error(reviewMessage(resp.raw, "Could not load review words"));
      }
      review.items = reviewShuffled(data.filter(function (it) {
        return it && typeof it.word === "string" && it.word.trim();
      })).slice(0, REVIEW_MAX);
      review.index = 0;
      review.pages = {};  // 新队列 = 新随机模块选择，旧页表全部作废
      review.page = 0;
      if (review.items.length) reviewLoadDetails();
    }).catch(function (err) {
      reviewShowError(err && err.message ? err.message : t("Could not load review words"));
    }).then(function () {
      review.loading = false;
      reviewRender();
    });
  }

  function reviewAdvance() {
    if (!review.items.length) return;
    review.markError = "";
    review.index = (review.index + 1) % review.items.length;
    review.page = 0;
    reviewRender();
  }

  function reviewMarkKnown() {
    var item = reviewCurrent(), api = window.MBApi;
    if (!item || !api || typeof api.postJson !== "function" || review.inFlight) return;
    // 请求可能跨过一个 8s tick；删词只能按点击瞬间的下标，不能用回来时的 index。
    var markedIndex = review.index;
    review.inFlight = true;
    reviewRender();
    api.postJson(REVIEW_MARK_URL, { word: String(item.word), unknown: false })
      .then(function (resp) {
        if (!resp.ok) {
          throw new Error(reviewMessage(resp.raw, "Could not mark this word as known"));
        }
        // 解包单点委托 MBApi（R177）：非信封 / success:false 一律抛，
        // 失败原因优先取上游 message，不在页面里重写一份解包判读。
        try {
          api.unwrapStrict(resp.data);
        } catch (e) {
          throw new Error(reviewMessage(resp.raw, "Could not mark this word as known"));
        }
        // 上游把 SRS 行异步毕业；本地先移除，避免 8 秒后它又滚回来。
        // 失败时什么都不改，卡片留在原地并显出上游原因。
        review.items.splice(markedIndex, 1);
        delete review.pages[reviewWordKey(item.word)];  // R289：页表随词一起移除
        review.page = 0;
        if (review.index > markedIndex) review.index -= 1;
        if (review.index >= review.items.length) review.index = 0;
        review.markError = "";
        reviewClearError();
      })
      .catch(function (err) {
        review.markError = err && err.message
          ? err.message : t("Could not mark this word as known");
      })
      .then(function () { review.inFlight = false; reviewRender(); });
  }

  function reviewSetPaused(on) {
    review.paused = !!on;
    reviewWriteFlag(REVIEW_PAUSED_KEY, review.paused);
    reviewRender();
  }
  function reviewSetCollapsed(on) {
    review.collapsed = !!on;
    reviewWriteFlag(REVIEW_COLLAPSED_KEY, review.collapsed);
    reviewRender();
  }

  function initRollingReview() {
    var root = reviewRoot();
    if (!root) return;   // 匿名/登录页不渲染容器 → 不发任何请求
    review.paused = reviewReadFlag(REVIEW_PAUSED_KEY);
    review.collapsed = reviewReadFlag(REVIEW_COLLAPSED_KEY);

    $("#ai-review-toggle").on("click", function (e) { e.stopPropagation(); reviewSetPaused(!review.paused); });
    $("#ai-review-collapse").on("click", function (e) { e.stopPropagation(); reviewSetCollapsed(true); });
    $("#ai-review-peek").on("click", function (e) { e.stopPropagation(); reviewSetCollapsed(false); });
    $("#ai-review-next").on("click", function (e) { e.stopPropagation(); reviewAdvance(); });
    $("#ai-review-known").on("click", function (e) { e.stopPropagation(); reviewMarkKnown(); });
    $("#ai-review-retry").on("click", function (e) { e.stopPropagation(); reviewLoad(); });
    // 卡片上的点击/按下都不该穿透成 FAB 的点击或拖拽。
    root.addEventListener("click", function (e) { e.stopPropagation(); });
    root.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
    // 伙伴隐藏/复原后重算可见性（tick 在隐藏态会暂停，不会自己刷新）。
    // 隐藏要等 R244 的 700ms 消散动画走完才落 .buddy-hidden，0ms 读不到该状态；
    // 复原是同步 remove class，0ms 即可。
    $("#ai-companion-hide").on("click", function () {
      setTimeout(reviewRender, BUDDY_ANIM_MS + 50);
    });
    $("#ai-companion-restore").on("click", function () {
      setTimeout(reviewRender, 0);               // 立刻恢复可见
      setTimeout(reviewPosition, BUDDY_ANIM_MS); // 等缩放动画落定再校正位置
    });
    window.addEventListener("resize", reviewPosition);
    var wrap = reviewWrap();
    if (wrap) {
      // .buddy-snapping 有 0.22s left/top 过渡，pointerup 当帧读到的是插值位置。
      wrap.addEventListener("transitionend", function (e) {
        if (e.propertyName === "left" || e.propertyName === "top") reviewPosition();
      });
      wrap.addEventListener("pointerup", function () { setTimeout(reviewPosition, 260); });
    }
    function reviewStartTimer() {
      if (!review.timer) review.timer = setInterval(reviewTick, REVIEW_INTERVAL_MS);
    }
    window.addEventListener("pagehide", function () {
      if (review.timer) { clearInterval(review.timer); review.timer = null; }
    });
    // bfcache 返回时 pagehide 已清掉 timer，必须重建，否则轮播永久停摆。
    window.addEventListener("pageshow", function (event) {
      if (event && event.persisted) { reviewStartTimer(); reviewRender(); }
    });

    reviewStartTimer();
    reviewLoad();
  }

  function clearLetterBadge() {
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (wrap) wrap.classList.remove("buddy-has-letter");
    var badge = document.querySelector("#ai-companion-restore .ai-letter-badge");
    if (badge) badge.hidden = true;
  }

  function showLetter() {
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (!wrap) return;
    wrap.classList.add("buddy-has-letter");
    // 伙伴已隐藏：不演飞信，只在唤回标签上打角标，避免用户看不到主体动画却以为没到信。
    if (wrap.classList.contains("buddy-hidden")) {
      var badge = document.querySelector("#ai-companion-restore .ai-letter-badge");
      if (badge) badge.hidden = false;
      return;
    }
    if (buddyReducedMotion()) return;
    wrap.classList.remove("buddy-lettering");
    void wrap.offsetWidth;   // 强制重排，连发两封也能重播动画
    wrap.classList.add("buddy-lettering");
    setTimeout(function () { wrap.classList.remove("buddy-lettering"); }, 1600);
  }

  // R243/R244 交界：站内信负责“到底有没有未读”，R244 只负责伙伴隐藏后的
  // 唤回标签提示与一次性收信动画。可见的 FAB 继续用 R243 自己的信封，
  // 不在这里重复渲染红点；伙伴隐藏时才把同一未读态映射到唤回标签。
  function syncLetterBadge() {
    var mailBadge = document.getElementById("ai-companion-mail-badge");
    var hasMail = !!(mailBadge && !mailBadge.hidden);
    if (!hasMail) {
      clearLetterBadge();
      return;
    }
    var wrap = document.getElementById("ai-companion-fab-wrap");
    if (wrap && wrap.classList.contains("buddy-hidden")) showLetter();
  }

  window.AICompanion.showLetter = showLetter;
  window.AICompanion.clearLetter = clearLetterBadge;
  window.AICompanion.syncLetterBadge = syncLetterBadge;
  // Partner pages can open the shared drawer without creating a second chat UI.
  window.AICompanion.openChat = function () { openDrawer("chat"); };
  window.addEventListener("mb:buddy-letter", function () { showLetter(); });

  // 阅读器划词右键菜单入口：把选中文本以「」引用形式追加到输入框（不发送），
  // 打开抽屉并把光标放到末尾——用户接着补提示词，写完自己按发送
  function insertIntoInput(text) {
    var quoted = String(text || "").trim();
    if (!quoted) return false;
    var $input = $("#ai-chat-input");
    if (!$input.length) return false;
    var current = $input.val();
    $input.val(current ? current.replace(/\s+$/, "") + "\n\n「" + quoted + "」\n" : "「" + quoted + "」\n");
    openDrawer("chat");
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
    $.getJSON("/ai/agent/conversations", BOOK_ID ? { bookId: BOOK_ID } : {})
      .then(function (raw) {
        var convs;
        try { convs = unwrap(raw) || []; } catch (e) { convs = []; }
        var $sel = $("#ai-chat-conversations").empty();
        if (!convs.length) {
          newConversation();
          return;
        }
        convs.forEach(function (c) {
          $sel.append($("<option>").val(c.id).text(c.title || mbT('New conversation')));
        });
        var preferred = parseInt(localStorage.getItem(storageKey()) || "", 10);
        var scoped = convs.filter(function (c) {
          return BOOK_ID ? c.bookId === BOOK_ID : (!c.bookId || c.bookId === 0);
        });
        var visible = scoped.length ? scoped : convs;
        var target = visible.some(function (c) { return c.id === preferred; }) ? preferred : visible[0].id;
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
    stopSpeech();
    currentConversationId = null;
    persistSelection();
    $("#ai-chat-conversations").val(null);
    clearMessages();
    appendHint(mbT('New conversation ready: it will be created once you send your first question.'));
  }

  function selectConversation(conversationId) {
    if (!conversationId) return;
    stopSpeech();
    currentConversationId = conversationId;
    persistSelection();
    $("#ai-chat-conversations").val(conversationId);
    loadHistory(conversationId);
  }

  function renameConversation() {
    var id = currentConversationId;
    if (!id) { window.alert(mbT('Please select an existing conversation first')); return; }
    var $opt = $("#ai-chat-conversations").find("option:selected");
    var newTitle = window.prompt(mbT('Rename conversation'), ($opt.text() || "").trim());
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
      window.alert(mbT('Rename failed: ') + errText(xhr));
    });
  }

  function deleteConversation() {
    var id = currentConversationId;
    if (!id || deleting) return;
    var title = $("#ai-chat-conversations").find("option:selected").text() || "";
    // 会话名用户可自取，含 $&/$1 时 String.replace 的第二参会做特殊展开，故走回调
    if (!window.confirm(mbT('Delete conversation “{t}”? This cannot be undone.')
        .replace('{t}', function () { return title; }))) return;
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
      window.alert(mbT('Delete failed: ') + errText(xhr));
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
    var $msg = $('<div class="ai-chat-msg ' + cls + '"></div>').html(safe).appendTo("#ai-chat-messages");
    // R227：历史里的助手消息同样可朗读（只给助手侧——读自己的提问没有意义）
    if (cls === "assistant") attachSpeakButton($msg);
    scrollMessages();
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function decodeEscapedText(value) {
    return String(value || "").replace(/&(amp|lt|gt|quot|#39);/g, function (_, name) {
      return { amp: "&", lt: "<", gt: ">", quot: '"', "#39": "'" }[name];
    });
  }

  /**
   * R233：只把当前站点内的路径变成链接。
   *
   * Why 不复用 new URL 的 origin 判断就结束：`//evil.example` 与含用户名密码的
   * 绝对 URL 也会被 URL 解析器接受。这里先拒绝控制字符/反斜杠，再要求输入以
   * 单斜杠或当前 origin 开头，最后仍比对规范化后的 origin。
   */
  function normalizeSiteHref(raw) {
    var value = decodeEscapedText(raw).trim();
    var origin = window.location.origin;
    if (!value || /[\u0000-\u001f\u007f\\]/.test(value)) return "";
    if (value !== origin && value.indexOf(origin + "/") !== 0 && value.charAt(0) !== "/") return "";
    if (value.indexOf("//") === 0) return "";
    var url;
    try { url = new URL(value, origin); } catch (e) { return ""; }
    if (url.origin !== origin || url.username || url["password"]) return "";
    if (url.protocol !== "http:" && url.protocol !== "https:") return "";
    return url.pathname + url.search + url.hash;
  }

  function siteLink(href, labelHtml) {
    return '<a class="ai-chat-site-link" href="' + escapeHtml(href) +
      '" target="_blank" rel="noopener noreferrer">' + labelHtml + "</a>";
  }

  function renderMarkdown(text) {
    if (!text) return "";
    var esc = escapeHtml(text); // escape HTML before any markup is introduced
    var held = [];
    var marker = "\u0000";
    while (esc.indexOf(marker) !== -1) marker += "\u0000";

    // Hold code and Markdown links first: a URL-looking token inside code must
    // never reach the bare-link pass, and an invalid link target must stay text.
    // Plain-held text is restored before the final inline passes so bold that
    // wraps a link still becomes one <strong> rather than two adjacent tags.
    function hold(html, isFinal) {
      held.push({ html: html, final: !!isFinal });
      return marker + (held.length - 1) + marker;
    }
    function restore(finalOnly) {
      for (var pass = 0; pass < held.length; pass += 1) {
        held.forEach(function (item, index) {
          if (!!item.final === finalOnly) esc = esc.split(marker + index + marker).join(item.html);
        });
      }
    }

    esc = esc.replace(/```([\s\S]*?)```/g, function (_, code) {
      return hold("<pre><code>" + code.replace(/^\n/, "") + "</code></pre>", true);
    });
    esc = esc.replace(/`([^`\n]+)`/g, function (_, code) {
      var href = normalizeSiteHref(code);
      return hold(href ? siteLink(href, "<code>" + code + "</code>") : "<code>" + code + "</code>", true);
    });
    esc = esc.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, function (whole, label, target) {
      var href = normalizeSiteHref(target);
      if (!href) return hold(whole, true);
      var labelHtml = label.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
      return hold(siteLink(href, labelHtml), true);
    });

    // Bare site paths / same-origin absolute URLs. Trailing prose punctuation
    // stays outside the anchor; external URLs never match normalizeSiteHref.
    esc = esc.replace(/(^|[\s(（\[【:：,，;；、])(\/[^\s<>"'`、（）【】《》]+|https?:\/\/[^\s<>"'`、（）【】《》]+)/g,
      function (_, prefix, target) {
        var chain = target.match(/(?:[.,;:!?，。；：！？、）)\]}>】》]+)$/);
        var trailing = chain ? chain[0] : "";
        var trimmed = trailing ? target.slice(0, -trailing.length) : target;
        var href = normalizeSiteHref(trimmed);
        if (!href) return prefix + target;
        return prefix + siteLink(href, escapeHtml(href)) + trailing;
      });
    restore(false);
    esc = esc.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    esc = esc.replace(/\n/g, "<br>");
    restore(true);
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
    $chip.find(".ai-tool-detail").text((ok ? mbT("Result: ") : mbT("Failed: ")) + (resultSummary || ""));
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
  var activeThinking = null;

  /**
   * R215：思考中气泡必须在发送的同一帧出现。
   * Why：原实现先 await getPageContextAsync() 再进 streamChat，PDF 取页文本慢时
   * 用户看到的是「点了没反应」的空白期（QA 截图 d1-ai-15s）。气泡、计时器、
   * FAB 动效都前移到点击同步路径，上下文提取改为带超时的竞速。
   */
  function beginThinking() {
    sending = true;
    $("#ai-chat-send").prop("disabled", true);
    // 发送期间禁止录音：转写结果无处安放（输入框已清空、上一条正在落库）
    if (micBtnEl) micBtnEl.disabled = true;
    $("#ai-companion-fab").addClass("buddy-thinking").removeClass("buddy-sleep");
    var started = Date.now();
    var $msg = $('<div class="ai-chat-msg assistant"><span class="ai-chat-typing">' + mbT("Thinking") +
      ' · <span class="ai-thinking-elapsed">0s</span></span></div>')
      .appendTo("#ai-chat-messages");
    scrollMessages();
    activeThinking = {
      $msg: $msg,
      timer: setInterval(function () {
        var seconds = Math.max(0, Math.floor((Date.now() - started) / 1000));
        $msg.find(".ai-thinking-elapsed").text(seconds + "s");
      }, 1000)
    };
    return activeThinking;
  }

  function stopThinking(thinking) {
    if (!thinking) return;
    if (thinking.timer) {
      clearInterval(thinking.timer);
      thinking.timer = null;
    }
    if (activeThinking === thinking) activeThinking = null;
    $("#ai-companion-fab").removeClass("buddy-thinking");
  }

  function sendMessage() {
    if (sending) return;
    var $input = $("#ai-chat-input");
    var text = $input.val().trim();
    if (!text) return;

    appendMessage("user", text);
    $input.val("");

    // 同步出「思考中 · 0s」；页面上下文最多等 1200ms，超时按空上下文继续发送
    var thinking = beginThinking();
    var contextPromise = window.AICompanion && window.AICompanion.getPageContextAsync
      ? window.AICompanion.getPageContextAsync().catch(function () { return ""; })
      : Promise.resolve("");
    var timeout = new Promise(function (resolve) {
      setTimeout(function () { resolve(""); }, 1200);
    });
    Promise.race([contextPromise, timeout]).then(function (pageCtx) {
      streamChat(text, pageCtx, thinking);
    });
  }

  function streamChat(message, pageContext, thinking) {
    var $msg = thinking.$msg;
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
        bookTitle: BOOK_META.title || document.title,
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
        // 首个真实事件到达即停表；气泡本身由 delta 覆盖、由 final/error 收尾
        if (type) stopThinking(thinking);

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
          case "audio":
            // 顺序固定：tool_result 之后才到 audio，芯片先收尾再出声
            playCachedSpeech(obj.text, function (why) {
              fullText += (fullText ? "\n" : "") + "⚠ " + why;
              $msg.html(renderMarkdown(fullText));
              scrollMessages();
            });
            break;
          case "final":
            // R232：final 事件里的 usage 只用来收尾，**不再渲染**——用量是账务信息，
            // 只在【设置】【积分】的消耗明细里看（moon-well 仍按 token 记流水并落
            // total_tokens，记录侧一行未改）。聊天界面里逐轮浮一行 "tokens 8123/456"
            // 对读者是噪音：它既不解释这条回答为什么好，也不影响下一次提问。
            conversationIdFromFinal = obj.conversationId || null;
            break;
          case "error":
            fullText += (fullText ? "\n" : "") + "⚠ " + (obj.message || mbT('AI service error'));
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
      stopThinking(thinking);
      if (errMsg) {
        var prefix = fullText ? "\n" : "";
        fullText += prefix + "⚠ " + errMsg;
        $msg.html(renderMarkdown(fullText));
      } else if (!fullText) {
        $msg.html('<span class="ai-chat-typing">(no response)</span>');
      }
      // 流式期间每帧都在重写 $msg 内容，按钮必须等收尾后再挂（否则下一个 delta 就抹掉）
      attachSpeakButton($msg);
      sending = false;
      $("#ai-chat-send").prop("disabled", false);
      if (micBtnEl) micBtnEl.disabled = false;
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
    loadUserProfile();
    if (BOOK_ID) loadBookProfile();
    else $("#ai-memory-profile").empty();
    loadMemories();
  }

  var USER_PROFILE_MAX = 2000;

  function updateUserProfileCount() {
    var length = ($("#ai-user-profile-input").val() || "").length;
    $("#ai-user-profile-count")
      .text(length + " / " + USER_PROFILE_MAX)
      .toggleClass("at-limit", length >= USER_PROFILE_MAX);
  }

  function setUserProfileStatus(message, isError) {
    $("#ai-user-profile-status")
      .text(message || "")
      .toggleClass("is-error", !!isError);
  }

  function loadUserProfile() {
    var $input = $("#ai-user-profile-input");
    setUserProfileStatus(t("Loading your profile…"), false);
    $.getJSON("/ai/agent/profile")
      .then(function (raw) {
        var profile;
        try { profile = unwrap(raw) || {}; } catch (e) {
          setUserProfileStatus(t("Profile unavailable: ") + e.message, true);
          return;
        }
        $input.val(profile.selfIntroduction || "");
        updateUserProfileCount();
        setUserProfileStatus("", false);
      })
      .fail(function (xhr) {
        setUserProfileStatus(t("Profile unavailable: ") + errText(xhr), true);
      });
  }

  function saveUserProfile() {
    var $input = $("#ai-user-profile-input");
    var text = ($input.val() || "").trim();
    if (!text) {
      setUserProfileStatus(t("Write something about yourself first"), true);
      $input.trigger("focus");
      return;
    }
    setUserProfileStatus(t("Saving…"), false);
    $("#ai-user-profile-save, #ai-user-profile-clear").prop("disabled", true);
    $.ajax({
      url: "/ai/agent/profile/save",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ selfIntroduction: text }),
    }).then(function (raw) {
      var profile;
      try { profile = unwrap(raw) || {}; } catch (e) {
        setUserProfileStatus(t("Save failed: ") + e.message, true);
        return;
      }
      $input.val(profile.selfIntroduction || text);
      updateUserProfileCount();
      setUserProfileStatus(t("Profile saved"), false);
    }).fail(function (xhr) {
      setUserProfileStatus(t("Save failed: ") + errText(xhr), true);
    }).always(function () {
      $("#ai-user-profile-save, #ai-user-profile-clear").prop("disabled", false);
    });
  }

  function clearUserProfile() {
    if (!window.confirm(t("Clear your AI profile? AI will no longer use this background."))) return;
    setUserProfileStatus(t("Clearing…"), false);
    $("#ai-user-profile-save, #ai-user-profile-clear").prop("disabled", true);
    $.ajax({
      url: "/ai/agent/profile/save",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ selfIntroduction: "" }),
    }).then(function (raw) {
      try { unwrap(raw); } catch (e) {
        setUserProfileStatus(t("Clear failed: ") + e.message, true);
        return;
      }
      $("#ai-user-profile-input").val("");
      updateUserProfileCount();
      setUserProfileStatus(t("Profile cleared"), false);
    }).fail(function (xhr) {
      setUserProfileStatus(t("Clear failed: ") + errText(xhr), true);
    }).always(function () {
      $("#ai-user-profile-save, #ai-user-profile-clear").prop("disabled", false);
    });
  }

  function loadBookProfile() {
    var $profile = $("#ai-memory-profile").text(mbT('Loading learning profile…'));
    $.getJSON("/ai/agent/book-profile", { bookId: BOOK_ID })
      .then(function (raw) {
        var profile;
        try { profile = unwrap(raw); } catch (e) {
          $profile.text(mbT('Learning profile unavailable: ') + e.message);
          return;
        }
        if (!profile || !profile.summary) {
          var base = profile && profile.questionCount
            ? mbT("Asked {n} questions for this book; learning summary pending.").replace("{n}", profile.questionCount)
            : mbT("No learning records for this book yet.");
          $profile.text(base);
          return;
        }
        $profile.empty();
        $('<div class="ai-profile-summary"></div>').text(profile.summary).appendTo($profile);
        var bits = [];
        if (profile.difficulty) bits.push(mbT("Difficulty: ") + profile.difficulty);
        if (profile.topics && profile.topics.length) bits.push(mbT("Topics: ") + profile.topics.join("、"));
        if (profile.hotWords && profile.hotWords.length) bits.push(mbT("Frequent words: ") + profile.hotWords.join("、"));
        if (bits.length) $('<div class="ai-profile-meta"></div>').text(bits.join(" ｜ ")).appendTo($profile);
        if (profile.questionCount) {
          $('<div class="ai-profile-meta"></div>')
            .text(mbT("Total questions: {q} · tool calls: {t}").replace("{q}", profile.questionCount).replace("{t}", profile.toolUseCount))
            .appendTo($profile);
        }
      })
      .fail(function (xhr) {
        $profile.text(mbT('Learning profile unavailable: ') + errText(xhr));
      });
  }

  function loadMemories() {
    var $list = $("#ai-memory-list").empty().text(mbT('Loading memories…'));
    $.getJSON("/ai/agent/memory")
      .then(function (raw) {
        var memories;
        try { memories = unwrap(raw) || []; } catch (e) {
          $list.text(mbT('Failed to load memories: ') + e.message);
          return;
        }
        $list.empty();
        if (!memories.length) {
          $list.text(mbT('(No long-term memories yet — say "remember…" in the chat or add one below)'));
          return;
        }
        memories.forEach(function (m) {
          var $item = $('<div class="ai-memory-item"></div>');
          $('<span class="ai-memory-scope"></span>')
            .text(m.bookId && m.bookId !== 0 ? mbT("[This book]") : mbT("[General]"))
            .appendTo($item);
          $('<span class="ai-memory-text"></span>').text(m.memory).appendTo($item);
          var $actions = $('<span class="ai-memory-actions"></span>').appendTo($item);
          $('<button type="button" title="' + mbT("Edit memory") + '">✎</button>')
            .on("click", function () { editMemory(m); }).appendTo($actions);
          $('<button type="button" title="' + mbT("Delete memory") + '">🗑</button>')
            .on("click", function () { deleteMemory(m); }).appendTo($actions);
          $item.appendTo($list);
        });
      })
      .fail(function (xhr) {
        $list.text(mbT('Failed to load memories: ') + errText(xhr));
      });
  }

  function addMemory() {
    var $input = $("#ai-memory-input");
    var text = ($input.val() || "").trim();
    if (!text) { window.alert(mbT('Write something to remember first')); return; }
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
      window.alert(mbT('Save failed: ') + errText(xhr));
    });
  }

  function editMemory(m) {
    var newText = window.prompt(mbT('Edit memory (clear to cancel)'), m.memory);
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
      .fail(function (xhr) { window.alert(mbT('Save failed: ') + errText(xhr)); });
  }

  function deleteMemory(m) {
    if (!window.confirm(mbT('Delete this memory?') + '\n' + m.memory)) return;
    $.ajax({
      url: "/ai/agent/memory/delete",
      method: "POST",
      contentType: "application/json",
      headers: { "X-CSRFToken": getCsrfToken() },
      data: JSON.stringify({ id: m.id }),
    }).then(loadMemories)
      .fail(function (xhr) { window.alert(mbT('Delete failed: ') + errText(xhr)); });
  }

  function errMessageFrom(body, status) {
    try {
      var data = JSON.parse(body);
      return data.message || data.error || ("HTTP " + status);
    } catch (e) { return "HTTP " + status; }
  }

  $(init);
})(jQuery);
