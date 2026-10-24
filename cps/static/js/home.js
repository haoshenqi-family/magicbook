// R213-C / MB-18：首页「今日计划」卡取数。
//
// Why 不服务端渲染：今日计划是首页唯一依赖 moon-well 的块，服务端同步拉会让
//     首屏等上游（/learning 页在 R166 定过同款口径：页面零上游调用）。这里两个
//     请求并行、各自 catch，任一失败只让对应数字显示「–」，两个都失败才整卡
//     降级成「暂不可用 + 去学习页」——不整页白屏（AC C3）。
// Why 文案走 data-* 而不是 mbT()：这套文案与整页一起由 Jinja 的 `_()` 出，
//     多语言只有一个入口；home.js 里没有第二个取词通道，也就没有
//     「mbT 词条漏进种子」这类静默回退英文的失效模式。
//
// 取数口径（AC C2，两处数字必须一致）：
//   待复习词数 = /ajax/learning/plan/today 的 reviewTotal。
//   Why 不是 reviews.length：reviews 被 dailyMinutes 推出上限截断，用它会把
//   「到期 40 词」显示成「到期 20 词」。reviewTotal 与 /learning 页的
//   srs/stats.dueNow 是**同一个 countDueBetween 查询**（moon-well
//   LearningPlanService / ReviewService），数值恒等——这是 C2 的实证依据。
//   写作待办 = history 里 createdAt 落在今天、且 lastDraftNo == null 的条数
//   （null = 出题后一稿未写，moon-well WritingVO.HistoryItem 的既有字段）。

(function () {
  'use strict';

  var root = document.getElementById('home-plan');
  if (!root) return;

  var line = document.getElementById('home_plan_line');
  var planUrl = root.getAttribute('data-plan-url');
  var writingUrl = root.getAttribute('data-writing-url');
  var textReviews = root.getAttribute('data-text-reviews') || 'Words due for review';
  var textWriting = root.getAttribute('data-text-writing') || 'Writing tasks to finish';
  var textUnavailable = root.getAttribute('data-text-unavailable') || 'Plan unavailable';

  function getJson(url) {
    return fetch(url, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
      .then(function (resp) {
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return resp.json();
      });
  }

  // moon-well 的成功响应可能直接是 VO，也可能被 Result{success,result} 包一层；
  // 两种形态都解，解不出就当失败（宁可显示「–」也不显示编造的数字）。
  function unwrap(payload) {
    if (!payload || typeof payload !== 'object') return null;
    if (payload.success === false) return null;
    if (payload.result && typeof payload.result === 'object') return payload.result;
    return payload;
  }

  function localDateKey(value) {
    if (!value) return null;
    // moon-well 回的是 LocalDateTime.toString()（"2026-10-24T15:30:00"，无时区）。
    // 直接 new Date() 在多数浏览器按本地时间解析，正是我们要的「用户视角的今天」。
    var parsed = new Date(value);
    if (isNaN(parsed.getTime())) return null;
    var month = parsed.getMonth() + 1;
    var day = parsed.getDate();
    return parsed.getFullYear() + '-' + (month < 10 ? '0' : '') + month + '-' + (day < 10 ? '0' : '') + day;
  }

  function reviewsCount() {
    return getJson(planUrl).then(function (raw) {
      var plan = unwrap(raw);
      if (!plan) throw new Error('plan payload');
      if (typeof plan.reviewTotal === 'number') return plan.reviewTotal;
      // 旧后端没有 reviewTotal 时退回列表长度（数字会偏小，但不至于空着）
      return Array.isArray(plan.reviews) ? plan.reviews.length : 0;
    });
  }

  function writingCount() {
    return getJson(writingUrl).then(function (raw) {
      var payload = unwrap(raw);
      if (!payload) throw new Error('writing payload');
      var items = Array.isArray(payload) ? payload : (payload.items || payload.history || []);
      if (!Array.isArray(items)) throw new Error('writing list');
      var today = localDateKey(new Date().toISOString());
      return items.filter(function (item) {
        return item && item.lastDraftNo == null && localDateKey(item.createdAt) === today;
      }).length;
    });
  }

  function cell(value, label) {
    var wrap = document.createElement('span');
    wrap.className = 'home-plan-cell';
    var num = document.createElement('strong');
    num.textContent = value == null ? '–' : String(value);
    wrap.appendChild(num);
    wrap.appendChild(document.createTextNode(' ' + label));
    return wrap;
  }

  function render(reviews, writing) {
    if (reviews == null && writing == null) {
      // 两块都拿不到：整卡降级为一句可点的提示，不再保留「– / –」这种像坏了的样子
      line.textContent = textUnavailable;
      line.classList.add('home-plan-degraded');
      return;
    }
    line.textContent = '';
    line.appendChild(cell(reviews, textReviews));
    var sep = document.createElement('span');
    sep.className = 'home-plan-sep';
    sep.textContent = '·';
    line.appendChild(sep);
    line.appendChild(cell(writing, textWriting));
  }

  Promise.all([
    reviewsCount().catch(function () { return null; }),
    writingCount().catch(function () { return null; })
  ]).then(function (values) {
    render(values[0], values[1]);
  });
})();
