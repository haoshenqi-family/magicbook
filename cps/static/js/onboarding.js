/* magicbook 前端引导模式（R109）——spotlight 逐步导览。
   Why: 新用户打开 magicbook 面对的是 Calibre 派生界面，找不到主流程在哪。
        本脚本用「蒙层挖孔 + 气泡」指向真实控件，让用户在真界面上学，而不是读文档。
        不引入第三方 tour 库（js/libs 无同类资产，为单页挂载新增依赖不划算）。
        状态持久化复用既有 POST /ajax/view → User.view_settings['onboarding']，
        因此零 Python 改动、零数据库迁移。
   How: 两段导览——main（浏览/详情/设置，挂在 layout.html）与 reader（阅读器/AI 伴读，
        挂在 read.html）。步骤只在锚点存在的页面上生效，锚点缺失（角色门控、书库为空、
        单格式书）自动跳过而不是卡死。进度写 localStorage 以支持跨页面与新标签页续览。 */
(function ($) {
  "use strict";

  var LS_PREFIX = "calibre.onboarding.";
  var PROGRESS_TTL_MS = 24 * 3600 * 1000;
  var cfg = window.MagicbookOnboarding || {};
  var GUIDE_BOOK_ID = cfg.guideBookId || 0;
  // R112：文案走 i18n_seed.html 注入的 MB_I18N（英文 msgid → 用户 locale 译文），
  // 种子缺失时回退 msgid 本身，保证纯静态调试页不炸
  var mbT = window.mbT || function (id) { return id; };

  /* ---------------- 步骤表 ----------------
     sel 为 null → 渲染居中卡（收尾卡）。
     act: "goto" → 洞上盖点击捕获，由 gotoTarget 统一决定怎么跳（见 holeCatcher）。
     handoff: 跳转后把进度落到「另一段导览」的某步——阅读器是新标签，
              若沿用本段下一步会在无关页面上错误续览。
     文案（R112）：title/body 都是英文 msgid，经 mbT 按用户 locale 单语言渲染，
     中文译文在 i18n_seed.html + zh_Hans_CN po——替代旧的「中英双写」方案。
     */

  var STEPS_MAIN = [
    { id: "browse", sel: "#scnd-nav",
      title: "Browse",
      body: "Switch library views by newest / trending / top rated / read / unread / random — your first stop for finding books." },
    { id: "search", sel: "#query",
      title: "Search",
      body: "Search the whole library by title or author; the results page keeps the same sorting and shelf actions." },
    { id: "advsearch", sel: "#advanced_search",
      title: "Advanced search",
      body: "Use it to combine filters by author / series / publisher / language / rating." },
    { id: "wall", sel: ".book.session",
      title: "Book wall",
      body: "The cover grid is your library. Click a cover for details; hover for quick actions." },
    { id: "sort", sel: ".filterheader",
      title: "Sort",
      body: "Sort by age, title, author or publisher; your choice is saved to your account." },
    { id: "openbook", sel: ".book.session a", act: "goto",
      title: "Open a book",
      body: "Pick any book to open its detail page; the tour continues there." },
    { id: "meta", sel: "#detailcover",
      title: "Details",
      body: "Right of the cover: title, authors, series, tags, rating and publisher." },
    // 单格式书渲染的是 #Download，多格式才是 #btnGroupDrop1（detail.html:26/39）
    { id: "download", sel: "#btnGroupDrop1, #Download",
      title: "Download",
      body: "Download EPUB / PDF / TXT, or send straight to your Kindle email." },
    { id: "read_online", sel: "#readbtn, #read-in-browser", act: "goto",
      handoff: { segment: "reader", step: "toc" },
      title: "Read in browser",
      body: "Open the reader without downloading; the second tour takes over inside." },
    { id: "shelf", sel: "#shelf-actions",
      title: "Shelves",
      body: "Shelves are your own curated lists (want-to-read / reading / favorites), switchable in the sidebar." },
    { id: "have_read", sel: "#have_read_cb",
      title: "Mark as read",
      body: "Tick it when you finish; read/unread filters and stats rely on it." },
    { id: "settings_menu", sel: "#top_mb_settings",
      title: "Settings",
      body: "Reading settings, achievements and credits all live in this dropdown." },
    { id: "finish", sel: null, guide: true,
      title: "Done",
      body: "Leave the rest to habit. A second tour awaits inside the reader." }
  ];

  var STEPS_READER = [
    { id: "toc", sel: "#show-Toc",
      title: "Contents",
      body: "The sidebar switches between table of contents, bookmarks and in-book search." },
    { id: "paging", sel: "#next",
      title: "Paging",
      body: "Click the arrows or use the left/right arrow keys; progress is saved automatically." },
    { id: "theme", sel: "#setting",
      title: "Reading Settings",
      body: "Colors, font size, layout and read-aloud all live here." },
    { id: "translate", sel: "#immersive-translate",
      title: "Translate",
      body: "Turn on bilingual paragraphs. Word lookups live in the MagicLens browser extension now." },
    { id: "bookmark", sel: "#bookmark",
      title: "Bookmark",
      body: "Mark key spots and jump back with one click from the sidebar." },
    { id: "fullscreen", sel: "#fullscreen",
      title: "Fullscreen",
      body: "Hide the browser chrome and keep only the reading area." },
    { id: "ai", sel: "#ai-companion-fab",
      title: "AI Companion",
      body: "Ask questions about this book; it remembers your preferences." },
    { id: "reader-finish", sel: null,
      title: "Happy reading",
      body: "Tap the “?” at the bottom-left any time to replay the tour." }
  ];

  /* ---------------- 存储 ---------------- */

  function lsGet(key, fallback) {
    try {
      var raw = window.localStorage.getItem(LS_PREFIX + key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch (e) {
      return fallback;
    }
  }

  function lsSet(key, value) {
    try {
      window.localStorage.setItem(LS_PREFIX + key, JSON.stringify(value));
    } catch (e) { /* 隐私模式写不进：退化为「本页面内可用」即可 */ }
  }

  function lsDel(key) {
    try {
      window.localStorage.removeItem(LS_PREFIX + key);
    } catch (e) { /* ignore */ }
  }

  /** 服务端种子取自 view_settings['onboarding']（{main:bool, reader:bool}）；匿名为空。 */
  function serverSeen() {
    return cfg.seen && typeof cfg.seen === "object" ? cfg.seen : {};
  }

  function localSeen() {
    var v = lsGet("seen", {});
    return v && typeof v === "object" ? v : {};
  }

  function isSeen(segment) {
    // 服务端为权威（跨设备）；本地镜像兜住匿名访客——Anonymous.set_view_property
    // 写的是 flask_session（cps/ub.py:338），而模板读的是共享行的 view_settings，
    // 服务端那条写入对匿名既不会生效也没有意义，所以匿名只用 localStorage。
    return !!serverSeen()[segment] || !!localSeen()[segment];
  }

  function markSeen(segment) {
    var seen = localSeen();
    seen[segment] = true;
    lsSet("seen", seen);
    clearProgress();
    if (!cfg.anonymous) {
      $.ajax({
        method: "POST",
        url: appPath() + "/ajax/view",
        contentType: "application/json; charset=utf-8",
        headers: { "X-CSRFToken": $("input[name='csrf_token']").val() || "" },
        data: JSON.stringify({ onboarding: seen })
        // 写失败不影响体验：下次进页面会重新邀请，最多重看一次导览
      });
    }
  }

  // 「以后再说」按段记录：主流程说以后再不要，不该连带屏蔽阅读器导览
  function isLater(segment) {
    var v = lsGet("later", {});
    return !!(v && typeof v === "object" && v[segment]);
  }

  function setLater(segment) {
    var v = lsGet("later", {});
    if (!v || typeof v !== "object") v = {};
    v[segment] = 1;
    lsSet("later", v);
  }

  /** 主动开启导览 = 撤回该段的「以后再说」，但不动另一段。 */
  function clearLater(segment) {
    var v = lsGet("later", {});
    if (!v || typeof v !== "object") return;
    delete v[segment];
    lsSet("later", v);
  }

  function appPath() {
    // 与 main.js getPath() 同源：从 jquery 的 src 反推应用根路径，兼容子路径部署
    var src = $("script[src*='jquery']").attr("src") || "";
    var m = src.search(/\/static\/js\/libs\/jquery\.min\.js/);
    return m > -1 ? src.substring(0, m) : "";
  }

  /* ---------------- 断点续览 ---------------- */

  function saveProgress(segment, stepId) {
    lsSet("progress", { segment: segment, step: stepId, at: Date.now() });
  }

  function loadProgress() {
    var p = lsGet("progress", null);
    if (!p || !p.segment || !p.step) return null;
    if (!p.at || Date.now() - p.at > PROGRESS_TTL_MS) {
      lsDel("progress");
      return null;
    }
    return p;
  }

  function clearProgress() {
    lsDel("progress");
  }

  /* ---------------- 导览引擎 ---------------- */

  var current = null;  // {segment, index}

  function stepsFor(segment) {
    return segment === "reader" ? STEPS_READER : STEPS_MAIN;
  }

  function isReaderPage() {
    return !!document.querySelector("#show-Toc, #viewerContainer, #viewer");
  }

  function detectSegment() {
    return isReaderPage() ? "reader" : "main";
  }

  function findStepIndex(segment, stepId) {
    var list = stepsFor(segment);
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === stepId) return i;
    }
    return -1;
  }

  function findStep(segment, stepId) {
    var i = findStepIndex(segment, stepId);
    return i > -1 ? stepsFor(segment)[i] : null;
  }

  function findVisible(selector) {
    if (!selector) return $();
    return $(selector).filter(function () {
      return $(this).is(":visible") && this.getBoundingClientRect().width > 0;
    }).first();
  }

  /** 高于视口的目标（侧栏导航）若按 center 对齐，元素顶部会被推到视口外，
      高亮框上下边都看不见；这类元素改为顶对齐。 */
  function scrollTargetIntoView(el) {
    var tall = el.getBoundingClientRect().height > window.innerHeight;
    var opts = { block: tall ? "start" : "center", inline: "nearest" };
    try { el.scrollIntoView(opts); } catch (e) { el.scrollIntoView(); }
  }

  /** 换步必须先摘掉上一步的 onb-step-*：CSS 用它在「AI 伴读」一步放行 FAB，
      残留会让 FAB 在后续步骤上继续盖住蒙层。 */
  function clearStepClass() {
    $("body").removeClass(function (i, cls) {
      return (cls.match(/onb-step-\S+/g) || []).join(" ");
    });
  }

  /** 两段导览的视觉分开（R111）：main 在书库页，整屏压暗无妨；reader 压在用户正在
      读的书页上，蒙层必须更轻、工具条整条留亮。样式全靠这两个类作用域。 */
  function setSegmentScope(segment) {
    $("body").removeClass("onb-seg-main onb-seg-reader")
      .addClass(segment === "reader" ? "onb-seg-reader" : "onb-seg-main");
  }

  /** 只有阅读器段跟着主题走（R111）：书库页的气泡本来就浮在蒙层上，不存在压住正文
      的问题；read.html 却有 5 套主题（含可任取颜色的 customTheme），白卡落在深色主题
      上很刺眼。按 #main 的实际底色算亮度，而不是再抄一份主题对照表——查表必漏 customTheme。 */
  function applyChromePalette() {
    var dark = false;
    if (isReaderPage()) {
      var rgb = pageBackground();
      dark = !!rgb && (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114) < 140;
    }
    $("body").toggleClass("onb-chrome-dark", dark);
  }

  /** #main 是主题色的落点（selectTheme 直接写它的内联背景）。
      取到透明值说明主题还没应用、走的是 CSS 默认，退到 body；仍是透明就按亮底处理。 */
  function pageBackground() {
    var nodes = [document.getElementById("main"), document.body];
    for (var i = 0; i < nodes.length; i++) {
      if (!nodes[i]) continue;
      var m = /rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.]+))?\s*\)/
        .exec(window.getComputedStyle(nodes[i]).backgroundColor);
      if (!m) continue;
      if (m[4] !== undefined && parseFloat(m[4]) === 0) continue;
      return [Number(m[1]), Number(m[2]), Number(m[3])];
    }
    return null;
  }

  function teardown() {
    // #onb-help 不删：它是阅读器段的常驻入口，导览期间靠 body 类隐藏
    $("body").removeClass("onboarding-active onb-seg-main onb-seg-reader onb-chrome-dark");
    clearStepClass();
    $("#onb-mask, #onb-bubble").remove();
    current = null;
  }

  function esc(text) {
    return $("<i>").text(text == null ? "" : String(text)).html();
  }

  function buildBubble(step, index, total) {
    var isLast = index >= total - 1;
    var html = '<div class="onb-card">'
      + '<div class="onb-head"><span class="onb-title" id="onb-title">' + esc(mbT(step.title)) + '</span>'
      + '<span class="onb-count">' + (index + 1) + ' / ' + total + '</span></div>'
      + '<div aria-live="polite">'
      + '<p class="onb-text">' + esc(mbT(step.body)) + '</p>'
      + (step.guide && GUIDE_BOOK_ID ? '<p class="onb-guide"><a href="' + appPath() + '/book/' + GUIDE_BOOK_ID
          + '">' + esc(mbT("Further reading: Magicbook User Guide")) + '</a></p>' : '')
      + '</div>'
      // 按钮走自己的类，不带 Bootstrap 的 .btn：read.html 没有引入 bootstrap，
      // 原来那几个 .btn 在阅读器里根本没样式，渲染成浏览器的原生灰按钮
      + '<div class="onb-actions">'
      + (index > 0 ? '<button type="button" class="onb-btn onb-back">' + esc(mbT("Previous step")) + '</button>' : '')
      + '<button type="button" class="onb-btn onb-skip">' + esc(mbT("Skip")) + '</button>'
      + '<span class="onb-spacer"></span>'
      + '<button type="button" class="onb-btn onb-primary onb-next">'
      + esc(step.act === "goto" ? mbT("Try it") : (isLast ? mbT("Done") : mbT("Next step")))
      + '</button></div></div>';

    var bubble = $('<div id="onb-bubble" role="dialog" aria-modal="true" aria-labelledby="onb-title"></div>').html(html);

    bubble.on("click", ".onb-next", function () {
      if (step.act === "goto") {
        var el = findVisible(step.sel);
        if (el.length) { gotoTarget(step, el.get(0)); return; }
      }
      if (isLast) { finish(current.segment); return; }
      render(index + 1);
    });
    bubble.on("click", ".onb-back", function () { render(Math.max(0, index - 1)); });
    bubble.on("click", ".onb-skip", function () { finish(current.segment); });
    return bubble;
  }

  function nextStepId(index) {
    var list = stepsFor(current.segment);
    return index + 1 < list.length ? list[index + 1].id : null;
  }

  /** 跳转类步骤：进度落到 handoff 指定的段/步（跨段交给新标签），否则本段下一步。 */
  function gotoTarget(step, el) {
    if (!el) return;
    var $el = $(el), href = $el.attr("href");
    if (step.handoff) {
      saveProgress(step.handoff.segment, step.handoff.step);
    } else {
      saveProgress(current.segment, nextStepId(current.index));
    }
    teardown();
    if (href) {
      if ($el.attr("target") === "_blank") { window.open(href); }
      else { window.location.href = href; }
      return;
    }
    // 无 href（多格式「在浏览器里读」是 dropdown-toggle）：交给原生行为展开菜单，
    // 用户自选格式 → 新标签里按 handoff 进度续览阅读器段
    el.click();
  }

  /** 气泡贴高亮洞：下方优先，空间不足依次上方 / 右侧 / 垂直居中，并夹在视口内。
      rect 必须是 drawMask 返回的「洞」而非目标原始 rect：侧栏导航这类高于视口的
      元素，原始 rect 的 top 是负值，直接拿来定位会把气泡推到屏幕外。 */
  function position(bubble, rect) {
    if (!bubble.length) return;
    bubble.css({ visibility: "hidden", display: "block" });
    var bw = bubble.outerWidth(), bh = bubble.outerHeight();
    var gap = 14, pad = 12, vw = window.innerWidth, vh = window.innerHeight;
    var top, left;

    if (rect.bottom + bh + gap + pad < vh) { top = rect.bottom + gap; }
    else if (rect.top - bh - gap - pad > 0) { top = rect.top - bh - gap; }
    else if (rect.right + bw + gap < vw) { top = rect.top; left = rect.right + gap; }
    else { top = (vh - bh) / 2; }

    if (left === undefined) {
      var wanted = rect.left + rect.width / 2 - bw / 2;
      left = Math.min(Math.max(pad, wanted), Math.max(pad, vw - bw - pad));
    }
    top = Math.min(Math.max(pad, top), Math.max(pad, vh - bh - pad));
    bubble.css({ top: top, left: left, visibility: "visible" });
  }

  /** 4 块遮罩围出「亮区」(protect)，环 (ring) 单独勾出真正的目标。
      Why: 两段视觉不同——main 段亮区就是目标外扩 12px（整屏压暗没问题）；reader 段
      把整条工具条留给用户看清（见 protectFor），只压暗工具条之外的区域，正在读的
      书页不再被黑幕盖住，同时目标仍靠环指出来。
      返回亮区（与视口求交后）的矩形，供气泡贴着它定位。 */
  function drawMask(protect, ring) {
    var l = Math.max(0, protect.left), t = Math.max(0, protect.top);
    var r = Math.min(window.innerWidth, protect.right);
    var b = Math.min(window.innerHeight, protect.bottom);
    var h = Math.max(0, b - t);
    var mask = $("#onb-mask").empty();
    [
      { left: 0, top: 0, width: "100%", height: t },
      { left: 0, top: b, width: "100%", height: Math.max(0, window.innerHeight - b) },
      { left: 0, top: t, width: l, height: h },
      { left: r, top: t, width: Math.max(0, window.innerWidth - r), height: h }
    ].forEach(function (p) {
      mask.append($('<div class="onb-side"></div>').css(p));
    });
    if (ring) {
      // 环也要跟视口求交：高于视口的目标（侧栏导航）原始 rect 的 top 是负值，
      // 不夹就会画成一个只露出底边的残缺框
      var rl = Math.max(0, ring.left), rt = Math.max(0, ring.top);
      var rw = Math.min(window.innerWidth, ring.right) - rl;
      var rh = Math.min(window.innerHeight, ring.bottom) - rt;
      if (rw > 0 && rh > 0) {
        mask.append($('<div class="onb-ring"></div>').css({ left: rl, top: rt, width: rw, height: rh }));
      }
    }
    return { left: l, top: t, width: Math.max(0, r - l), height: h, right: r, bottom: b };
  }

  /** 目标矩形外扩 pad（left/top/width/height/right/bottom 都补齐，
      原始 DOMRect 不能直接改，且后续求交要用到 right/bottom）。 */
  function expand(rect, pad) {
    return {
      left: rect.left - pad, top: rect.top - pad,
      width: rect.width + pad * 2, height: rect.height + pad * 2,
      right: rect.right + pad, bottom: rect.bottom + pad
    };
  }

  /** 阅读器段的亮区＝目标所在的那一条工具带（标题栏 / 侧栏 / 底部页码条）：
      整条留亮，用户能看到目标旁边的兄弟控件，书页只吃一层薄纱。
      目标不在工具带里（翻页箭头、AI 悬浮球）就退化为按元素外扩。 */
  function protectFor(el, segment, rect) {
    if (segment !== "reader") return expand(rect, 12);
    var band = $(el).closest("#titlebar, #sidebar, .read-footer");
    if (!band.length) return expand(rect, 18);
    return expand(band.get(0).getBoundingClientRect(), 0);
  }

  /** 目标矩形：去掉「不可见的点击热区」。
      Why: 翻页箭头 .arrow 带 160px 上下、80px 左右内边距（main.css:115-141），
      照 border-box 挖洞会圈出一大块空白，环看起来像画错了。
      只在元素自身没有背景时才按 padding 内缩——按钮的底色铺在自己的 padding 上，
      内缩会把「控件」高亮成「控件里的几个字」。 */
  function visualRect(el) {
    var rect = el.getBoundingClientRect();
    var cs = window.getComputedStyle(el);
    var bg = cs.backgroundColor;
    if (bg && bg !== "transparent" && !/rgba\(0,\s*0,\s*0,\s*0(\.\d+)?\)/.test(bg)) return rect;
    if (cs.backgroundImage && cs.backgroundImage !== "none") return rect;
    var l = parseFloat(cs.paddingLeft) || 0, r = parseFloat(cs.paddingRight) || 0;
    var t = parseFloat(cs.paddingTop) || 0, b = parseFloat(cs.paddingBottom) || 0;
    return {
      left: rect.left + l, top: rect.top + t,
      width: Math.max(0, rect.width - l - r), height: Math.max(0, rect.height - t - b),
      right: rect.right - r, bottom: rect.bottom - b
    };
  }

  /** 跳转类步骤盖在洞上的点击捕获：原生点击会开出 modal / 新标签，
      Bootstrap modal（z≈1050）会被蒙层压暗，所以由脚本统一接管跳转。 */
  function holeCatcher(hole, step, el) {
    var catcher = $('<div class="onb-catch"></div>').css(
      { left: hole.left, top: hole.top, width: hole.width, height: hole.height });
    catcher.on("click", function () { gotoTarget(step, el); });
    $("#onb-mask").append(catcher);
  }

  /** 画蒙层：亮区按段规则取（protectFor），环只勾目标本身（外扩 4px）。
      返回亮区矩形，气泡定位与点击捕获都以它为准。 */
  function paintMask(el, rect) {
    return drawMask(protectFor(el, current.segment, rect), expand(rect, 4));
  }

  function render(index) {
    var list = stepsFor(current.segment);
    if (index >= list.length) { finish(current.segment); return; }

    var step = list[index];
    var narrow = window.innerWidth < 768;
    var target = narrow ? $() : findVisible(step.sel);

    // 锚点缺失（角色门控 / 单格式书 / 主题差异）→ 跳过该步，绝不停在空白气泡上
    if (!narrow && step.sel && !target.length) {
      render(index + 1);
      return;
    }

    current.index = index;
    saveProgress(current.segment, step.id);
    // onb-step-<id>：AI 按钮的 z-index 高于蒙层，只有「AI 伴读」这一步才让它亮着
    $("body").addClass("onboarding-active");
    clearStepClass();
    $("body").addClass("onb-step-" + step.id);
    applyChromePalette();
    $("#onb-mask, #onb-bubble").remove();

    if (!target.length) {
      // 居中卡 + 整体压暗（窄屏同样走这条路径）
      $("body").append('<div id="onb-mask" class="onb-dim"></div>');
      var centered = buildBubble(step, index, list.length).addClass("onb-centered");
      $("body").append(centered);
      // 必须先入树再给 display：jQuery 3 的 .show() 对未插入文档的元素不生效
      // （isHiddenWithinTree 依赖在树内判定），#onb-bubble 默认 display:none，
      // 于是完成卡会挂在 DOM 里但完全不可见
      centered.css("display", "block");
      if (step.guide) verifyGuideLink(centered);
      centered.find(".onb-next").trigger("focus");
      return;
    }

    var el = target.get(0);
    scrollTargetIntoView(el);
    $("body").append('<div id="onb-mask"></div>');
    var hole = paintMask(el, visualRect(el));
    if (step.act === "goto") holeCatcher(hole, step, el);
    var bubble = buildBubble(step, index, list.length);
    $("body").append(bubble);
    position(bubble, hole);
    bubble.find(".onb-next").trigger("focus");
  }

  function onViewportChange() {
    if (!current) return;
    var step = stepsFor(current.segment)[current.index];
    if (!step || !step.sel) return;
    var target = findVisible(step.sel);
    if (!target.length) return;  // 该步已划出视野：保持原位，滚回来即可
    var el = target.get(0);
    var hole = paintMask(el, visualRect(el));  // 清空蒙层，点击捕获需重贴
    if (step.act === "goto") holeCatcher(hole, step, el);
    position($("#onb-bubble"), hole);
  }

  // scroll 事件密度高，合并到一帧一次，避免导览期间持续重排
  var viewportTick = null;
  function onViewportEvent() {
    if (viewportTick) return;
    viewportTick = window.setTimeout(function () {
      viewportTick = null;
      onViewportChange();
    }, 120);
  }

  function startTour(segment, fromStepId) {
    $("#onb-invite").remove();
    // AI 抽屉 z-index 高于气泡，开着会盖住气泡；导览一律从关闭态开始
    $("#ai-companion-drawer").removeClass("open");
    current = { segment: segment, index: 0 };
    setSegmentScope(segment);
    render(fromStepId ? Math.max(0, findStepIndex(segment, fromStepId)) : 0);
  }

  function finish(segment) {
    markSeen(segment);
    teardown();
    showEntryAgainIfNeeded(segment);
  }

  /** ESC 只是「收起」，不等于「学完了」：不写 seen，只按以后再说处理。 */
  function dismiss(segment) {
    setLater(segment);
    clearProgress();
    teardown();
    showEntryAgainIfNeeded(segment);
  }

  function showEntryAgainIfNeeded(segment) {
    if (segment === "reader") showReaderHelp();
  }

  /* ---------------- 邀请卡与常驻入口 ---------------- */

  function showInvite(segment) {
    applyChromePalette();
    var isReader = segment === "reader";
    var card = $('<div id="onb-invite" role="dialog" aria-label="' + esc(mbT("Onboarding Tour")) + '"><div class="onb-invite-card">'
      + '<button type="button" class="onb-invite-x" title="' + esc(mbT("Close")) + '" aria-label="' + esc(mbT("Close")) + '">×</button>'
      + '<div class="onb-invite-title">' + esc(mbT("Learn magicbook in 2 minutes")) + '</div>'
      + '<p class="onb-invite-text">'
      + esc(isReader ? mbT("Flip pages, switch themes and use the AI companion, right inside the reader.")
                     : mbT("Walk through finding books, shelves, download and reading on the real interface."))
      + '</p><div class="onb-invite-actions">'
      + '<button type="button" class="onb-btn onb-invite-never">' + esc(mbT("Never show again")) + '</button>'
      + '<span class="onb-spacer"></span>'
      + '<button type="button" class="onb-btn onb-invite-later">' + esc(mbT("Later")) + '</button>'
      + '<button type="button" class="onb-btn onb-primary onb-invite-start">' + esc(mbT("Start Tour")) + '</button>'
      + '</div></div></div>');

    card.on("click", ".onb-invite-start", function () { card.remove(); startTour(segment); });
    card.on("click", ".onb-invite-later", function () { setLater(segment); card.remove(); });
    card.on("click", ".onb-invite-never", function () { setLater(segment); markSeen(segment); card.remove(); });
    // × 与「以后再说」同义：否则每次翻页都重弹，等于没关
    card.on("click", ".onb-invite-x", function () { setLater(segment); card.remove(); });
    $("body").append(card);
  }

  /** 阅读器页没有 layout 的「设置」下拉，用常驻「?」代替手动入口。 */
  function showReaderHelp() {
    // 配色要在「已存在就直接 return」之前算：teardown 会摘掉 onb-chrome-dark，
    // 导览结束后不重算，那个「?」会从暗色卡回跳成浮在深色主题上的白按钮
    applyChromePalette();
    if (!isReaderPage()) return;
    // 去重要在 DOM 里查，不能用 $("#onb-help").length：jQuery 的 ID 选择器走
    // getElementById 只返回第一个节点，重复追加时它仍数到 1，守卫形同失效
    if (document.getElementById("onb-help")) return;
    // 监听绑在建好的节点上，不靠 #id 反查：71d126cb（R111 提交，正与 R112 会话同文件
    // 并发写入）把这行 append 写了两遍，两个同位置按钮只有第一个拿到监听，
    // 点到的永远是盖在上层的空壳（R113 线上事故）
    var help = $('<button type="button" id="onb-help" title="' + esc(mbT("Onboarding Tour")) + '" aria-label="' + esc(mbT("Onboarding Tour")) + '">?</button>');
    help.on("click", function () { clearLater("reader"); showInvite("reader"); });
    $("body").append(help);
  }

  /** 指南书可能已不在书库里：探一次，非 200（或被登录页 302 兜走）就摘掉链接。 */
  function verifyGuideLink(bubble) {
    var para = bubble.find(".onb-guide");
    if (!para.length) return;
    $.ajax({ method: "GET", url: para.find("a").attr("href") })
      .done(function (data, status, xhr) {
        var toLogin = xhr && xhr.responseURL && xhr.responseURL.indexOf("/login") > -1;
        if (!xhr || xhr.status !== 200 || toLogin) para.remove();
      })
      .fail(function () { para.remove(); });
  }

  /* ---------------- 入口 ---------------- */

  function bindLayoutEntry() {
    $("#top_onboarding").on("click", function (e) {
      e.preventDefault();
      var segment = detectSegment();
      clearLater(segment);
      startTour(segment);
    });
  }

  function init() {
    bindLayoutEntry();

    var segment = detectSegment();
    var progress = loadProgress();
    if (progress && progress.segment === segment && findStep(segment, progress.step)) {
      // 跨页面/新标签续览：该步锚点不在本页时保持安静，不打断用户也不再自动推进
      var step = findStep(segment, progress.step);
      if (!step.sel || findVisible(step.sel).length) {
        startTour(segment, progress.step);
      }
      return;
    }
    if (progress && progress.segment === segment) {
      clearProgress();  // 步骤已从表里移除
    }
    if (!isSeen(segment) && !isLater(segment)) {
      showInvite(segment);
      return;
    }
    showReaderHelp();
  }

  $(document).on("keydown.onboarding", function (e) {
    if (e.key !== "Escape" || !current) return;
    // 阻止 ai_chat.js 的同键监听一起把抽屉关掉（它比我们早注册）
    e.stopImmediatePropagation();
    dismiss(current.segment);
  });
  $(window).on("resize.onboarding", onViewportEvent);
  // scroll 不冒泡：caliBlur 主题下真正滚动的是 .col-sm-10（overflow:auto），
  // 挂在 window 上的普通监听收不到内部容器滚动，高亮洞会钉在原地跟目标脱钩，
  // 只有捕获阶段能拿到
  window.addEventListener("scroll", onViewportEvent, true);

  $(init);
})(jQuery);
