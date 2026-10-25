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

  /** 朗读正文取自渲染后的 DOM：工具芯片、tokens 计数、思考占位、告警行都不是回答。 */
  function speechTextOf($msg) {
    var $clone = $msg.clone();
    $clone.find(".ai-tool-chip, .ai-chat-usage, .ai-chat-typing, .ai-chat-speak").remove();
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
      if ($("#ai-companion-drawer").hasClass("open")) closeDrawer();
      else openDrawer();
    });
    initBuddyFabDrag();
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

    applyFormatPlaceholder();
    initFabLabel();
    initBubbles();
    initVoiceInput();
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
  function openDrawer() {
    $("#ai-companion-drawer").addClass("open");
    markFabLabelSeen();
    closeBubbles();
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
      $("#ai-companion-fab").trigger("click");
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
            conversationIdFromFinal = obj.conversationId || null;
            if (obj.usage && (obj.usage.promptTokens || obj.usage.completionTokens)) {
              var $usage = $('<span class="ai-chat-usage"></span>');
              $usage.text("tokens " + (obj.usage.promptTokens || 0) + "/" + (obj.usage.completionTokens || 0));
              $usage.appendTo($msg);
            }
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
    if (BOOK_ID) loadBookProfile();
    else $("#ai-memory-profile").empty();
    loadMemories();
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
