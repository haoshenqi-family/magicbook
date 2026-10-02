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

  /* ---------------- 步骤表 ----------------
     sel 为 null → 渲染居中卡（收尾卡）。
     act: "goto" → 洞上盖点击捕获，由 gotoTarget 统一决定怎么跳（见 holeCatcher）。
     handoff: 跳转后把进度落到「另一段导览」的某步——阅读器是新标签，
              若沿用本段下一步会在无关页面上错误续览。 */

  var STEPS_MAIN = [
    { id: "browse", sel: "#scnd-nav",
      zh: "浏览分类", en: "Browse categories",
      body: "这里按「最新 / 热门 / 高分 / 已读 / 未读 / 随机」等维度切换书库视图，是找书的第一站。",
      bodyEn: "Switch the library by newest, hot, rated, read, unread, random, author, series and more." },
    { id: "search", sel: "#query",
      zh: "搜索书库", en: "Search the library",
      body: "输入书名或作者即可全库检索，结果页沿用同样的排序与书架操作。",
      bodyEn: "Type a title or author to search the whole library." },
    { id: "advsearch", sel: "#advanced_search",
      zh: "高级搜索", en: "Advanced search",
      body: "需要按作者 / 系列 / 出版社 / 语言 / 评分多条件组合过滤时用这里。",
      bodyEn: "Combine author, series, publisher, language and rating filters here." },
    { id: "wall", sel: ".book.session",
      zh: "书墙", en: "Book wall",
      body: "封面网格就是书库（首页那排是随机推荐）。点封面看详情，鼠标悬停可快速操作。",
      bodyEn: "The cover grid is the library (the home row is a random pick). Click a cover for details." },
    { id: "sort", sel: ".filterheader",
      zh: "排序", en: "Sort",
      body: "按新旧、书名、作者、出版社排序；选择会被记住，下次进来还是这个顺序。",
      bodyEn: "Sort by date, title, author or publisher. The choice is remembered per account." },
    { id: "openbook", sel: ".book.session a", act: "goto",
      zh: "进入一本书", en: "Open a book",
      body: "点这里任选一本书进入详情页，导览会在详情页接着讲。",
      bodyEn: "Pick any book to open its detail page — the tour continues there." },
    { id: "meta", sel: "#detailcover",
      zh: "详情与元数据", en: "Details and metadata",
      body: "封面右侧是书名、作者、系列、标签、评分与出版社等 Calibre 元数据。",
      bodyEn: "Beside the cover: title, authors, series, tags, rating and publisher." },
    // 单格式书渲染的是 #Download，多格式才是 #btnGroupDrop1（detail.html:26/39）
    { id: "download", sel: "#btnGroupDrop1, #Download",
      zh: "下载与传书", en: "Download and send",
      body: "下载 EPUB / PDF / TXT 等已有格式；配了 Kindle 邮箱还能一键传书。",
      bodyEn: "Download available formats, or send the book to your Kindle e-reader." },
    { id: "read_online", sel: "#readbtn, #read-in-browser", act: "goto",
      handoff: { segment: "reader", step: "toc" },
      zh: "在浏览器里读", en: "Read in browser",
      body: "点开阅读器无需下载；进阅读器后由第二段导览接手，讲翻页、主题与 AI 伴读。",
      bodyEn: "Read without downloading. A second tour takes over inside the reader." },
    { id: "shelf", sel: "#shelf-actions",
      zh: "书架", en: "Shelves",
      body: "书架是你自己组织的书单（想读 / 在读 / 收藏），左侧栏可随时切换。",
      bodyEn: "Shelves are your own booklists — want-to-read, reading, favorites." },
    { id: "have_read", sel: "#have_read_cb",
      zh: "标记已读完", en: "Mark as read",
      body: "读完勾一下，「未读 / 已读」筛选、统计与成就都依赖它。",
      bodyEn: "Tick it when you finish — read/unread filters, stats and achievements rely on it." },
    { id: "settings_menu", sel: "#top_mb_settings",
      zh: "设置入口", en: "Settings menu",
      body: "阅读设置、成就、积分都收在这个下拉里；管理员还能看到外观设置。",
      bodyEn: "Reading settings, achievements and credits live in this dropdown." },
    { id: "finish", sel: null, guide: true,
      zh: "导览完成", en: "Tour complete",
      body: "剩下的交给习惯。打开阅读器时还有第二段导览（翻页 / 主题 / AI 伴读）。",
      bodyEn: "Explore from here. A second tour waits inside the reader." }
  ];

  var STEPS_READER = [
    { id: "toc", sel: "#show-Toc",
      zh: "目录面板", en: "Table of contents",
      body: "左侧栏可切目录、书签与搜索，长书靠它跳转章节。",
      bodyEn: "The sidebar holds contents, bookmarks and in-book search." },
    { id: "paging", sel: "#next",
      zh: "翻页", en: "Page turning",
      body: "点左右箭头或用键盘方向键翻页，进度会自动记忆。",
      bodyEn: "Use the arrows or the keyboard; your position is saved automatically." },
    { id: "theme", sel: "#setting",
      zh: "阅读设置", en: "Reading settings",
      body: "主题配色、字号字体、版式与段落朗读（TTS）都在这里。",
      bodyEn: "Themes, font size and family, layout and read-aloud live here." },
    { id: "translate", sel: "#immersive-translate",
      zh: "沉浸式翻译与划词", en: "Immersive translation",
      body: "开沉浸式翻译看双语段落；选中任意词句可直接查释义、加生词。",
      bodyEn: "Toggle bilingual paragraphs, or select text for instant definition and vocabulary." },
    { id: "bookmark", sel: "#bookmark",
      zh: "书签", en: "Bookmarks",
      body: "在关键处打个书签，之后从目录面板一键回到这里。",
      bodyEn: "Mark important spots and jump back to them from the sidebar." },
    { id: "fullscreen", sel: "#fullscreen",
      zh: "全屏", en: "Fullscreen",
      body: "全屏去掉浏览器 chrome，只留阅读区。",
      bodyEn: "Hide browser chrome and keep only the reading area." },
    { id: "ai", sel: "#ai-companion-fab",
      zh: "AI 伴读", en: "AI reading companion",
      body: "蓝色按钮打开伴读抽屉：就当前这本书提问、切换多个会话、查看它为你记下的长期记忆。",
      bodyEn: "The blue button opens the companion drawer: ask about this book, switch conversations, review its memory of you." },
    { id: "reader-finish", sel: null,
      zh: "阅读愉快", en: "Happy reading",
      body: "导览到此结束。想重看可随时点左下角的「?」。",
      bodyEn: "That's it. Tap the “?” at the bottom left to run this tour again." }
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

  function teardown() {
    // #onb-help 不删：它是阅读器段的常驻入口，导览期间靠 body 类隐藏
    $("body").removeClass("onboarding-active");
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
      + '<div class="onb-head"><span class="onb-title" id="onb-title" lang="zh-Hans">' + esc(step.zh) + '</span>'
      + ' <small class="onb-title-en" lang="en">' + esc(step.en) + '</small>'
      + '<span class="onb-count">' + (index + 1) + ' / ' + total + '</span></div>'
      + '<div aria-live="polite">'
      + '<p class="onb-text" lang="zh-Hans">' + esc(step.body) + '</p>'
      + '<p class="onb-text-en" lang="en">' + esc(step.bodyEn) + '</p></div>'
      + (step.guide && GUIDE_BOOK_ID ? '<p class="onb-guide"><a href="' + appPath() + '/book/' + GUIDE_BOOK_ID
          + '">延伸阅读：《Magicbook User Guide》</a></p>' : '')
      + '<div class="onb-actions">'
      + (index > 0 ? '<button type="button" class="btn btn-link btn-xs onb-back">上一步 Back</button>' : '')
      + '<button type="button" class="btn btn-link btn-xs onb-skip">跳过 Skip</button>'
      + '<span class="onb-spacer"></span>'
      + '<button type="button" class="btn btn-primary btn-xs onb-next">'
      + (step.act === "goto" ? '点我试试 Go' : (isLast ? '完成 Done' : '下一步 Next'))
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

  /** 4 块遮罩围出中间的「洞」：比 SVG mask 简单，滚动时只改尺寸不重建 path。
      返回洞的矩形，供跳转类步骤在上面盖一层点击捕获（见 holeCatcher）。 */
  function drawMask(rect) {
    var pad = 8;
    var l = Math.max(0, rect.left - pad), t = Math.max(0, rect.top - pad);
    var r = Math.min(window.innerWidth, rect.right + pad);
    var b = Math.min(window.innerHeight, rect.bottom + pad);
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
    mask.append($('<div class="onb-ring"></div>').css({
      left: l, top: t, width: Math.max(0, r - l), height: h
    }));
    return { left: l, top: t, width: Math.max(0, r - l), height: h, right: r, bottom: b };
  }

  /** 跳转类步骤盖在洞上的点击捕获：原生点击会开出 modal / 新标签，
      Bootstrap modal（z≈1050）会被蒙层压暗，所以由脚本统一接管跳转。 */
  function holeCatcher(hole, step, el) {
    var catcher = $('<div class="onb-catch"></div>').css(
      { left: hole.left, top: hole.top, width: hole.width, height: hole.height });
    catcher.on("click", function () { gotoTarget(step, el); });
    $("#onb-mask").append(catcher);
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
    var rect = el.getBoundingClientRect();
    $("body").append('<div id="onb-mask"></div>');
    var hole = drawMask(rect);
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
    var rect = target.get(0).getBoundingClientRect();
    var hole = drawMask(rect);   // drawMask 会清空蒙层，点击捕获需重贴
    if (step.act === "goto") holeCatcher(hole, step, target.get(0));
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
    var isReader = segment === "reader";
    var card = $('<div id="onb-invite" role="dialog" aria-label="使用引导"><div class="onb-invite-card">'
      + '<button type="button" class="onb-invite-x" title="关闭 Close" aria-label="关闭">×</button>'
      + '<div class="onb-invite-title" lang="zh-Hans">花 2 分钟学会 magicbook'
      + ' <small lang="en">2-min tour</small></div>'
      + '<p class="onb-invite-text" lang="zh-Hans">'
      + (isReader ? "带你在阅读器里翻页、换主题、用 AI 伴读。"
                  : "带你在真实界面上走一遍找书、加书架、下载与阅读。")
      + '<small lang="en">'
      + (isReader ? "Learn paging, themes and the AI companion."
                  : "Walk the real UI: find, shelve, download, read.")
      + '</small></p><div class="onb-invite-actions">'
      + '<button type="button" class="btn btn-xs btn-link onb-invite-never">不再提示 Never</button>'
      + '<span class="onb-spacer"></span>'
      + '<button type="button" class="btn btn-xs btn-default onb-invite-later">以后再说 Later</button> '
      + '<button type="button" class="btn btn-xs btn-primary onb-invite-start">开始引导 Start</button>'
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
    if (!isReaderPage() || $("#onb-help").length) return;
    $("body").append('<button type="button" id="onb-help" title="使用引导 Onboarding" aria-label="使用引导">?</button>');
    $("#onb-help").on("click", function () { clearLater("reader"); showInvite("reader"); });
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
