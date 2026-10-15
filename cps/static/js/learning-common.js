// 每日学习各页共用工具（R166 中枢化拆分）。
//
// Why 单独一个 common：中枢 + 七个子页面各载一个模块，HTTP 信封解包、CSRF、
// 显隐、四股字段口径、听力素材下拉这些逻辑原先在 learning.js 与
// speaking_writing.js 里各写一份，拆页后会变成九份副本（本仓并行会话多，
// 同文重复正是 R113 事故的形状）。
//
// 文案取词通道：window.mbT 由 i18n_seed.html 注入（layout.html 先载），
// 词条必须在渲染时取、不能在脚本加载时快照；字面量由
// tests/test_i18n_seed_contract.py 校验（必须进种子且 zh 译文非空）。
//
// 路由注入：每份模板在 {% block js %} 里注入 window.learningUrls，只列本页
// 用得到的端点。Why 每页各自声明 `var urls = window.learningUrls || {}`：
// R153 的 learning.js 直接引用了从未声明的 `urls`，ReferenceError 被计划头
// 的 promise catch 静默吞掉，今日计划与周视图整块不渲染（R166 排查发现）。
(function () {
  'use strict';

  function mbT(msgid) {
    return (window.MB_I18N && window.MB_I18N[msgid]) || msgid;
  }

  function byId(id) {
    return document.getElementById(id);
  }

  // Why 属性与内联双管齐下，缺一不可：只删 hidden 属性会被作者 display 规则顶回
  // （.ln-choices/.ln-spell 的 flex、.btn 的 inline-block）；只设内联则「显示」时
  // 模板里挂着的 hidden 属性仍在，UA 的 [hidden]{display:none} 继续生效——统计/
  // 计划/复习卡这些无作者 display 规则的元素永远显不出来（R140 模块全消失事故，
  // 是对 R139 空白格事故只修一半的后果）。属性解 UA 规则，内联压作者规则。
  function show(el, visible) {
    if (!el) return;
    el.hidden = !visible;
    el.style.display = visible ? '' : 'none';
  }

  // R177（架构评审 B5）：HTTP 基元/CSRF/解包单点迁至 static/js/common/api.js
  //（window.MBApi，layout.html 全局载入）；本文件保留导出名（MBLearning.*），
  // 内部委托——learning 九页调用方零改动。resultOf 走 strict 解包（与原口径
  // 等价：非信封一律抛，页面 catch 呈现），容错版见 MBApi.unwrapResult。
  function csrfToken() {
    return window.MBApi.csrfToken();
  }

  function httpJson(url, options) {
    return window.MBApi.httpJson(url, options);
  }

  function getJson(url) {
    return window.MBApi.getJson(url);
  }

  function postJson(url, body) {
    return window.MBApi.postJson(url, body);
  }

  function isBusinessError(response) {
    return window.MBApi.isBusinessError(response);
  }

  // 契约（moon-well learning 模块）：统一 Result 信封 {success, result, message}；
  // success=false 时 message 已是上游业务文案（zh），直接抛给调用方展示。
  function resultOf(response) {
    return window.MBApi.unwrapStrict(response.data);
  }

  // LLM 端点慢（批改/出题/报告 10-40s），按钮一律加在途锁防连击（R152 纪律）
  function busy(btn, on, label) {
    if (!btn) return;
    if (on) {
      btn.dataset.label = btn.textContent;
      btn.textContent = label;
      btn.disabled = true;
    } else {
      btn.textContent = btn.dataset.label || btn.textContent;
      btn.disabled = false;
    }
  }

  function clear(node) {
    while (node && node.firstChild) node.removeChild(node.firstChild);
  }

  function li(text, cls) {
    var el = document.createElement('li');
    if (cls) el.className = cls;
    el.textContent = text;
    return el;
  }

  // 一律 textContent：上游文案不过 HTML 解析器（R152 起就是这条纪律）
  function esc(node, text) {
    node.textContent = text == null ? '' : String(text);
  }

  // 四股字段口径（moon-well R150 台账读侧）：budget=预算分钟，earned=今日实际入账。
  // banner 卡片与中枢计划行共用这张表，earned 为 null（ES 降级/旧后端）按缺数处理。
  var STRANDS = {
    input: { budget: 'inputMinutes', earned: 'inputEarnedMinutes', label: 'Reading input' },
    language: { budget: 'languageMinutes', earned: 'languageEarnedMinutes', label: 'Word study' },
    output: { budget: 'outputMinutes', earned: 'outputEarnedMinutes', label: 'Speaking & writing' },
    fluency: { budget: 'fluencyMinutes', earned: 'fluencyEarnedMinutes', label: 'Fluency drills' },
  };
  var STRAND_ORDER = ['input', 'language', 'output', 'fluency'];
  var STRAND_COLORS = ['#5b9bd5', '#ed7d31', '#a5a5a5', '#ffc000'];

  // 听力素材下拉（计时重读 tts 档 / 听写 ted 档共用，R153）
  function loadMaterials(select, source, done) {
    var urls = window.learningUrls || {};
    if (!select || !urls.listeningMaterials) return;
    getJson(urls.listeningMaterials + '?source=' + source).then(function (response) {
      var items = resultOf(response) || [];
      clear(select);
      items.forEach(function (m) {
        var opt = document.createElement('option');
        opt.value = m.bookId;
        opt.textContent = (m.title || '') + (m.author ? ' · ' + m.author : '');
        select.appendChild(opt);
      });
      if (done) done(items);
    }).catch(function (err) { window.alert(err.message); });
  }

  function paragraphLine(paragraph, onPick) {
    var line = li((paragraph.chapterTitle ? '[' + paragraph.chapterTitle + '] ' : '') +
      String(paragraph.text || '').slice(0, 80) + '…' +
      ' · ' + paragraph.wordCount + ' ' + mbT('words'));
    line.style.cursor = 'pointer';
    line.addEventListener('click', function () { onPick(paragraph); });
    return line;
  }

  window.MBLearning = {
    mbT: mbT,
    byId: byId,
    show: show,
    csrfToken: csrfToken,
    httpJson: httpJson,
    getJson: getJson,
    postJson: postJson,
    isBusinessError: isBusinessError,
    resultOf: resultOf,
    busy: busy,
    clear: clear,
    li: li,
    esc: esc,
    STRANDS: STRANDS,
    STRAND_ORDER: STRAND_ORDER,
    STRAND_COLORS: STRAND_COLORS,
    loadMaterials: loadMaterials,
    paragraphLine: paragraphLine,
  };
})();
