// 每日学习中枢（R166）：功能 banner 轮播 + 今日计划 + 复习摘要 + 四股周视图。
// R208：banner 勾选管理——齿轮抽屉决定哪些功能卡进轮播；勾选真相存 moon-well
// （随 plan/today 顺路带回，不破首屏零上游调用），localStorage 只作消除闪现的镜像。
//
// Why 轮播自己写而不用 Bootstrap carousel：仓内 libs/bootstrap.min.js 虽带
// carousel 插件，但它要 jQuery + 一套 .item/.active 结构，而本页所有学习模块
// 都是原生 JS（learning-* 同纪律）；七张卡的诉求还要「按今日缺口排序 + 徽章
// 注入 + 减动效」，自写 ~90 行比分叉两套范式更省事。
//
// 卡片本身是 <a>（无 JS 也能点进子页面），轮播只做显隐与顺序，不改语义。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, getJson = MB.getJson, clear = MB.clear;
  var urls = window.learningUrls || {};

  var banner = $('lh-banner');
  if (!banner) return;

  var els = {};
  ['ln-error', 'ln-error-text', 'ln-retry', 'ln-plan', 'ln-strand-line',
   'ln-new-words-line', 'ln-review-summary', 'ln-today-review', 'ln-due-tomorrow',
   'ln-mastered', 'ln-retention', 'ln-due-line', 'ln-week', 'ln-week-bars',
   'ln-week-legend', 'lh-dots', 'lh-prev', 'lh-next',
   'lh-manage-btn', 'lh-manage', 'lh-manage-save', 'lh-manage-close',
   'lh-manage-error', 'lh-guide', 'lh-guide-open',
  ].forEach(function (id) { els[id] = $(id); });

  // R208：主列表固定七张（锚定 a.lh-card——引导卡无 lh-card 类不混入）；
  // visible 是勾选过滤后的轮播列表，轮播/圆点/缺口排序全部只看 visible。
  var cards = Array.prototype.slice.call(banner.querySelectorAll('a.lh-card'));
  var visible = cards.slice();
  var boxes = els['lh-manage']
    ? Array.prototype.slice.call(els['lh-manage'].querySelectorAll('input[type=checkbox][data-key]'))
    : [];
  var hiddenKeys = {};
  var MIRROR_KEY = 'ln-banner-hidden-v1';
  var AUTO_MS = 6000;
  var index = 0;
  var timer = null;
  var paused = false;
  var ordered = false;      // 缺口排序只在首份计划到手时做一次，之后用户手动翻页不再被打断
  var lastPlan = null;      // 供卡片徽章复用
  var lastStats = null;

  function reduceMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // ---------- 轮播 ----------

  function renderDots() {
    clear(els['lh-dots']);
    visible.forEach(function (card, i) {
      var dot = document.createElement('button');
      dot.type = 'button';
      dot.className = 'lh-dot' + (i === index ? ' lh-on' : '');
      dot.setAttribute('role', 'tab');
      dot.setAttribute('aria-label', card.querySelector('.lh-card-title').textContent);
      dot.addEventListener('click', function () { goTo(i, true); });
      els['lh-dots'].appendChild(dot);
    });
  }

  function paint() {
    visible.forEach(function (card, i) {
      if (i === index) card.classList.add('lh-on');
      else card.classList.remove('lh-on');
    });
    renderDots();
  }

  function goTo(next, manual) {
    if (!visible.length) return; // 全不勾时轮播静默（引导卡接管），不再取模
    index = (next + visible.length) % visible.length;
    paint();
    if (manual) restart();
  }

  function tick() {
    if (!paused && document.visibilityState !== 'hidden') goTo(index + 1, false);
  }

  function restart() {
    // 只重排定时器节奏，不动 paused：悬停/聚焦期间手动翻页后不该偷偷恢复自动播
    if (timer) clearInterval(timer);
    timer = reduceMotion() ? null : setInterval(tick, AUTO_MS);
  }

  banner.addEventListener('mouseenter', function () { paused = true; });
  banner.addEventListener('mouseleave', function () { paused = false; });
  banner.addEventListener('focusin', function () { paused = true; });
  banner.addEventListener('focusout', function () { paused = false; });
  banner.addEventListener('keydown', function (event) {
    if (event.key === 'ArrowLeft') { event.preventDefault(); goTo(index - 1, true); }
    else if (event.key === 'ArrowRight') { event.preventDefault(); goTo(index + 1, true); }
  });
  els['lh-prev'].addEventListener('click', function () { goTo(index - 1, true); });
  els['lh-next'].addEventListener('click', function () { goTo(index + 1, true); });

  // 移动端横滑（无 hover/focus 可用）
  var touchX = null;
  banner.addEventListener('touchstart', function (event) {
    touchX = event.touches.length === 1 ? event.touches[0].clientX : null;
    paused = true;
  }, { passive: true });
  banner.addEventListener('touchend', function (event) {
    if (touchX == null) return;
    var dx = event.changedTouches[0].clientX - touchX;
    touchX = null;
    paused = false;
    if (Math.abs(dx) > 40) goTo(index + (dx < 0 ? 1 : -1), true);
  });

  // ---------- 卡片徽章与排序 ----------

  function strandDeficit(key) {
    // 缺数（旧后端/ES 降级）按 0 处理：宁可不提前，也不把没数据的卡顶到第一位
    if (!lastPlan || !lastPlan.strands) return 0;
    var field = MB.STRANDS[key];
    if (!field) return 0;
    var budget = lastPlan.strands[field.budget];
    var earned = lastPlan.strands[field.earned];
    if (budget == null || earned == null) return 0;
    return Math.max(0, budget - earned);
  }

  function applyBadges() {
    cards.forEach(function (card) {
      var badge = card.querySelector('.lh-card-badge');
      if (!badge) return;
      var key = card.getAttribute('data-strand');
      var text = '';
      if (card.getAttribute('data-key') === 'review') {
        text = reviewBadge();
      } else if (key && key !== 'none' && lastPlan && lastPlan.strands) {
        var field = MB.STRANDS[key];
        var earned = lastPlan.strands[field.earned];
        var budget = lastPlan.strands[field.budget];
        if (earned != null && budget != null) {
          text = mbT('{{earned}}/{{budget}} min today')
            .replace('{{earned}}', earned).replace('{{budget}}', budget);
        }
      }
      badge.textContent = text;
      show(badge, !!text);
    });
  }

  function reviewBadge() {
    if (!lastStats || lastStats.todayReviewed == null || lastStats.todayTarget == null) return '';
    var done = Math.min(lastStats.todayReviewed, lastStats.todayTarget);
    var text = mbT('{{done}}/{{target}} reviewed').replace('{{done}}', done)
      .replace('{{target}}', lastStats.todayTarget);
    if (lastStats.dueNow != null && lastStats.dueNow > 0) {
      text += ' · ' + mbT('{{n}} due').replace('{{n}}', lastStats.dueNow);
    }
    return text;
  }

  // 今日欠账最多的那股排到 banner 前面（打开中枢先看见自己缺的那门课）；
  // 缺口相同按模板顺序（写作→口语→复述→重读→听写→复习→选书）稳定排列，
  // 无股卡片（选书）缺口恒为 0 自然垫底。Array#sort 在旧引擎不保证稳定，
  // 显式带原索引次键。R208：只在可见卡里排——被勾掉的卡不占位。
  function orderByDeficit() {
    if (ordered) return;
    ordered = true;
    if (!lastPlan || !lastPlan.strands || !visible.length) return;
    var ranked = visible.map(function (card, i) { return [card, i]; }).sort(function (a, b) {
      var gap = strandDeficit(b[0].getAttribute('data-strand')) -
        strandDeficit(a[0].getAttribute('data-strand'));
      return gap !== 0 ? gap : a[1] - b[1];
    }).map(function (pair) { return pair[0]; });
    if (ranked[0] === visible[0]) return;
    var viewport = banner.querySelector('.lh-banner-viewport');
    ranked.forEach(function (card) { viewport.appendChild(card); });
    visible = ranked;
    index = 0;
    paint();
  }

  // ---------- 勾选过滤（R208）：banner 只显示用户勾选的功能卡 ----------

  function applyVisibility() {
    visible = cards.filter(function (card) {
      return !hiddenKeys[card.getAttribute('data-key')];
    });
    // 可见卡按当前数组顺序重挂到 viewport 末尾（appendChild 即移动节点）：
    // 被勾掉的卡停在原地 display:none，轮播语义只属于 visible；
    // 缺口排序后数组已是排序序，这里重挂不会打乱它。
    var viewport = banner.querySelector('.lh-banner-viewport');
    visible.forEach(function (card) { viewport.appendChild(card); });
    if (index >= visible.length) index = 0;
    show(els['lh-guide'], visible.length === 0);
    show(els['lh-prev'], visible.length > 1);
    show(els['lh-next'], visible.length > 1);
    paint();
  }

  function loadMirror() {
    // 镜像只为消除「plan 回来前先全显再隐藏」的闪现；坏数据直接当未配置。
    // Why 不校验未知 key：过滤到主列表已知 key，防串镜像页互相污染。
    try {
      var raw = window.localStorage.getItem(MIRROR_KEY);
      if (!raw) return;
      var list = JSON.parse(raw);
      if (!Array.isArray(list)) return;
      var known = {};
      cards.forEach(function (card) { known[card.getAttribute('data-key')] = true; });
      list.forEach(function (key) {
        if (typeof key === 'string' && known[key]) hiddenKeys[key] = true;
      });
    } catch (error) { /* localStorage 不可用/损坏：按全显 */ }
  }

  function saveMirror() {
    try {
      window.localStorage.setItem(MIRROR_KEY, JSON.stringify(Object.keys(hiddenKeys)));
    } catch (error) { /* 隐私模式写不进就算了，真相在 moon-well */ }
  }

  function reconcileHidden(serverKeys) {
    // 服务端是真相：过滤到已知 key，与当前态不一致才应用并回写镜像——
    // 另一台设备改过勾选时，本机打开中枢会被对齐。
    var next = {};
    serverKeys.forEach(function (key) {
      if (typeof key === 'string' &&
          cards.some(function (card) { return card.getAttribute('data-key') === key; })) {
        next[key] = true;
      }
    });
    if (Object.keys(hiddenKeys).sort().join(',') === Object.keys(next).sort().join(',')) return;
    hiddenKeys = next;
    saveMirror();
    applyVisibility();
  }

  // ---------- 今日计划 ----------

  function renderPlan(result) {
    if (!result || !result.strands) return;
    lastPlan = result;
    var budget = result.strands;
    var parts = MB.STRAND_ORDER.map(function (key) {
      var field = MB.STRANDS[key];
      var earned = budget[field.earned];
      return mbT(field.label) + ' ' + (earned == null ? '–' : earned) + '/' +
        budget[field.budget] + 'min';
    });
    els['ln-strand-line'].textContent = mbT('Time budget by strand') + '（' +
      mbT('{{minutes}} minutes a day')
        .replace('{{minutes}}', result.settings && result.settings.dailyMinutes) +
      '）：' + parts.join(' · ');
    if (result.newWords && result.newWords.length) {
      var names = result.newWords.slice(0, 8).map(function (item) { return item.word; });
      els['ln-new-words-line'].textContent = mbT('New words today') + '（' +
        result.newWords.length + '）：' + names.join(', ') +
        (result.newWords.length > 8 ? ' …' : '');
      show(els['ln-new-words-line'], true);
    } else {
      els['ln-new-words-line'].textContent = mbT('No fresh words yet — mark unknown words while reading.');
      show(els['ln-new-words-line'], true);
    }
    show(els['ln-plan'], true);
    // R208：勾选随 plan/today 顺路带回（不破首屏零上游调用）。字段缺失=旧后端，
    // 保留镜像不做对账；空数组是合法值（显式全显），不能当 falsy 漏掉。
    var serverKeys = result.settings && result.settings.bannerHiddenKeys;
    if (serverKeys) reconcileHidden(serverKeys);
    applyBadges();
    orderByDeficit();
    if (result.settings && result.settings.dailyMinutes) loadWeek(result.settings.dailyMinutes);
  }

  // ---------- 复习摘要（R166：原统计头四格收进这张卡）----------

  function renderStats(result) {
    if (!result) return;
    lastStats = result;
    // R144 口径：今日进度 min 封顶；dueNow 只作为「现在就能练」的召唤，不刷欠账数字
    els['ln-today-review'].textContent =
      result.todayReviewed == null || result.todayTarget == null ? '–'
        : Math.min(result.todayReviewed, result.todayTarget) + '/' + result.todayTarget;
    els['ln-due-tomorrow'].textContent = result.dueTomorrow == null ? '–' : result.dueTomorrow;
    els['ln-mastered'].textContent = result.mastered == null ? '–' : result.mastered;
    els['ln-retention'].textContent =
      result.retention7d == null ? '–' : result.retention7d + '%';
    els['ln-due-line'].textContent = result.dueNow
      ? mbT('{{n}} words are due now.').replace('{{n}}', result.dueNow)
      : mbT('Nothing due right now. Keep reading — new words will find their way here.');
    show(els['ln-review-summary'], true);
    applyBadges();
  }

  // ---------- 四股周视图（R153）：近 7 天入账 vs 当日预算 ----------

  function loadWeek(dailyBudget) {
    getJson(urls.week).then(function (response) {
      if (!response.ok || !response.data || !response.data.success) throw new Error('week');
      var days = response.data.result || [];
      if (!days.length) throw new Error('week empty');
      renderWeek(days, dailyBudget);
    }).catch(function () {
      // ES 降级 / 旧后端：面板保持隐藏（周视图是增强，绝不挡计划页）
      show(els['ln-week'], false);
    });
  }

  function renderWeek(days, dailyBudget) {
    var box = els['ln-week-bars'];
    clear(box);
    days.forEach(function (day) {
      // 字段口径两套不同源：/plan 的 inputMinutes 是预算、inputEarnedMinutes 是入账；
      // /strands/summary 每天一行，inputMinutes 直接就是当日入账分钟（moon-well R150）。
      var earned = MB.STRAND_ORDER.map(function (key) {
        return day[MB.STRANDS[key].budget] || 0;
      });
      var row = document.createElement('div');
      row.className = 'ln-week-row';
      var label = document.createElement('span');
      label.className = 'ln-week-day';
      label.textContent = String(day.date || '').slice(5);
      row.appendChild(label);
      var bar = document.createElement('div');
      bar.className = 'ln-week-bar';
      earned.forEach(function (minutes, i) {
        var seg = document.createElement('span');
        // 段宽 = 该股入账 / 当日预算 × 预算占比；超额封顶在段内（诚实数字看 title 与右侧合计）
        var budgetMinutes = Math.max(1, dailyBudget);
        seg.style.width = Math.min(100, minutes / budgetMinutes * 100) + '%';
        seg.style.background = MB.STRAND_COLORS[i];
        seg.title = mbT(MB.STRANDS[MB.STRAND_ORDER[i]].label) + ' ' + minutes + '/' +
          Math.round(dailyBudget * 0.25) + 'min';
        bar.appendChild(seg);
      });
      row.appendChild(bar);
      var total = earned.reduce(function (a, b) { return a + b; }, 0);
      var right = document.createElement('span');
      right.className = 'ln-week-total';
      right.textContent = mbT('{{x}} min').replace('{{x}}', total);
      row.appendChild(right);
      box.appendChild(row);
    });
    var legend = els['ln-week-legend'];
    clear(legend);
    MB.STRAND_ORDER.forEach(function (key, i) {
      var dot = document.createElement('span');
      dot.className = 'ln-legend-dot';
      dot.style.background = MB.STRAND_COLORS[i];
      legend.appendChild(dot);
      legend.appendChild(document.createTextNode(mbT(MB.STRANDS[key].label)));
    });
    show(els['ln-week'], true);
  }

  // ---------- 管理抽屉（R208）----------

  var manageBtn = els['lh-manage-btn'];
  var manageErrorText = els['lh-manage-error'].textContent;

  function syncBoxes() {
    boxes.forEach(function (box) {
      box.checked = !hiddenKeys[box.getAttribute('data-key')];
    });
  }

  function openManage() {
    syncBoxes();
    MB.esc(els['lh-manage-error'], manageErrorText);
    show(els['lh-manage-error'], false);
    show(els['lh-manage'], true);
    manageBtn.setAttribute('aria-expanded', 'true');
  }

  function closeManage() {
    show(els['lh-manage'], false);
    manageBtn.setAttribute('aria-expanded', 'false');
  }

  if (manageBtn) {
    manageBtn.addEventListener('click', function () {
      if (els['lh-manage'].hidden) openManage();
      else closeManage();
    });
  }
  els['lh-manage-close'].addEventListener('click', closeManage);
  els['lh-guide-open'].addEventListener('click', openManage);
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && !els['lh-manage'].hidden) closeManage();
  });

  function settingsPayload() {
    // 保存必须带全四股数值（上游是全量替换接口）；缺任一字段就不敢拼——
    // 宁可报错也不拿猜的默认值盖掉用户已存的四股配比。
    var settings = lastPlan && lastPlan.settings;
    if (!settings || settings.dailyNewLimit == null || settings.dailyMinutes == null ||
        settings.strandInputPct == null || settings.strandLanguagePct == null ||
        settings.strandOutputPct == null || settings.strandFluencyPct == null) return null;
    return {
      dailyNewLimit: settings.dailyNewLimit, dailyMinutes: settings.dailyMinutes,
      strandInputPct: settings.strandInputPct, strandLanguagePct: settings.strandLanguagePct,
      strandOutputPct: settings.strandOutputPct, strandFluencyPct: settings.strandFluencyPct,
    };
  }

  function saveManage() {
    var hiddenList = boxes.filter(function (box) { return !box.checked; })
      .map(function (box) { return box.getAttribute('data-key'); });

    function proceed(base) {
      if (!base) {
        // 四股设置没到手（上游挂了/尚未返回）：没有底稿就没有合法 payload，
        // 报错必须可见、抽屉留着让用户重试。
        show(els['lh-manage-error'], true);
        return;
      }
      var payload = Object.assign({}, base, { bannerHiddenKeys: hiddenList });
      MB.busy(els['lh-manage-save'], true, els['lh-manage-save'].textContent);
      postJson(urls.settings, payload).then(function (response) {
        MB.busy(els['lh-manage-save'], false);
        if (!response.ok || !response.data || !response.data.success) {
          // 失败必须可见：优先上游业务文案，否则保留模板预填的兜底文案
          var message = response.data && response.data.message;
          if (message) MB.esc(els['lh-manage-error'], message);
          show(els['lh-manage-error'], true);
          return;
        }
        hiddenKeys = {};
        hiddenList.forEach(function (key) { hiddenKeys[key] = true; });
        saveMirror();
        applyVisibility();
        closeManage();
      }).catch(function () {
        MB.busy(els['lh-manage-save'], false);
        show(els['lh-manage-error'], true);
      });
    }

    if (lastPlan && lastPlan.settings) proceed(settingsPayload());
    else {
      // 抽屉打开在 plan 返回之前：补拉一次（15s 超时同首屏），拿不到就走可见报错
      getJson(urls.plan).then(function (response) {
        var result = response.ok && response.data && response.data.result;
        if (result && result.settings) {
          lastPlan = result;
          proceed(settingsPayload());
        } else proceed(null);
      }).catch(function () { proceed(null); });
    }
  }

  els['lh-manage-save'].addEventListener('click', saveManage);

  // ---------- 启动 ----------

  function fail(message) {
    show(els['ln-error'], true);
    els['ln-error-text'].textContent = message;
  }

  function loadAll() {
    show(els['ln-error'], false);
    getJson(urls.plan).then(function (response) {
      if (response.ok && response.data && response.data.result) {
        renderPlan(response.data.result);
      }
    }).catch(function () { fail(mbT('Failed to load your plan — press retry.')); });
    getJson(urls.stats).then(function (response) {
      if (response.ok && response.data && response.data.result) renderStats(response.data.result);
    }).catch(function () { /* 摘要卡是增强，失败留隐藏态，不挡 banner */ });
  }

  els['ln-retry'].addEventListener('click', loadAll);

  loadMirror();
  applyVisibility(); // 内含 paint：先按镜像裁剪再启动轮播，避免首帧闪现被勾掉的卡
  restart();
  loadAll();
})();
