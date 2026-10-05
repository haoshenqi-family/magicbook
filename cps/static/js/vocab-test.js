// 词汇量测试前端状态机（R116 / US4）。
//
// Why 独立文件而不是模板内联：设置页模板只放 DOM；状态机 + 三种视图渲染有 200+ 行，
// 内联会让 137 行的模板翻倍（US4 §2.3 定稿）。
//
// 文案取词通道：window.mbT 由 i18n_seed.html 注入，而该 include 在 block js **之后**
// （layout.html:250-252），所以词条必须在渲染时取、不能在脚本加载时快照，否则拿到回退值。
// 字面量由 tests/test_i18n_seed_contract.py 校验（必须进种子且 zh 译文非空）。
(function () {
  'use strict';

  var root = document.getElementById('vt-root');
  if (!root) return;

  // 与后端 VocabTestParams.BAND_UPPER 同一张表（moon-well），改动需两侧同步
  var BAND_UPPER = [1000, 2000, 3000, 5000, 8000, 12000, 18000, 25000];
  // 后端没有「总题数」字段（自适应状态机 20–40 题，硬上限 70），进度条按固定刻度弱对比
  var PROGRESS_SCALE = 40;

  var els = {};
  ['vt-add-unknown', 'vt-start', 'vt-status', 'vt-last-line', 'vt-last',
   'vt-toggle-history', 'vt-history-list', 'vt-overlay', 'vt-asking', 'vt-result',
   'vt-word', 'vt-sentence', 'vt-progress-fill', 'vt-progress-count', 'vt-known',
   'vt-unknown', 'vt-exit', 'vt-error-line', 'vt-size', 'vt-range', 'vt-capped-note',
   'vt-band-chart', 'vt-notebook-line', 'vt-done'].forEach(function (id) {
    els[id] = document.getElementById(id);
  });

  var state = 'idle';      // idle | asking | scoring | result
  var inFlight = false;    // 在途锁：同一题未收到响应前忽略重复提交（双击与键盘连击）
  var epoch = 0;           // 会话代数：closeOverlay 递增，作废已发出的请求（见下方 stale 判定）
  var sessionId = null;
  var question = null;     // {word, sentence, seq, band}：seq 是幂等锚点
  var retry = null;        // 最近一次失败的动作，供错误行重试

  // ---------- 小工具 ----------

  function show(el, visible) {
    if (el) el.hidden = !visible;
  }

  function setCardStatus(text, isError) {
    if (!els['vt-status']) return;
    els['vt-status'].textContent = text;
    els['vt-status'].className = isError ? 'text-danger' : 'text-muted';
  }

  function formatRank(value) {
    // 固定 en-US 千分位：数字分组不随 UI 语言变（用默认 locale 会让同一页面出两种分组形态）
    return Number(value).toLocaleString('en-US');
  }

  function cappedLabel() {
    // 顶格文案与档位表上界同源（BAND_UPPER 末位）；写死三处会在改档位表时漏改
    return formatRank(BAND_UPPER[BAND_UPPER.length - 1]) + '+';
  }

  function bandLabel(band) {
    var upper = BAND_UPPER[band - 1];
    if (!upper) return String(band);
    var lower = band === 1 ? 1 : BAND_UPPER[band - 2] + 1;
    return formatRank(lower) + '–' + formatRank(upper);
  }

  function isoDate(value) {
    // 统一 ISO 日期（YYYY-MM-DD）：首屏由 Jinja 渲染、结果页由 JS 渲染，
    // 若这里用 toLocaleDateString 同一页面会出现两种日期格式
    return value ? String(value).slice(0, 10) : '';
  }

  // CSRF：token 不放 cookie，项目惯例是渲染进 hidden input 再由 JS 读取
  function csrfToken() {
    var input = document.querySelector("input[name='csrf_token']");
    return input ? input.value : '';
  }

  // CSRF 失败自愈：token 过期/会话重建后服务端 400，刷新取新 token（独立标记键防死循环）
  function reloadIfCsrfBlocked(wrap) {
    if (!/csrf/i.test(wrap.text || '')) return false;
    try {
      if (sessionStorage.getItem('vtCsrfReloaded') === '1') return true;
      sessionStorage.setItem('vtCsrfReloaded', '1');
    } catch (e) { /* 隐私模式等场景忽略 */ }
    location.reload();
    return true;
  }

  // 请求发出后用户 Exit / 重开会话（closeOverlay 递增 epoch）时，迟到响应必须整段作废：
  // 否则 renderQuestion/renderResult 会把已隐藏的浮层状态复活，state 停在 asking/result
  // 而 Start 按钮因 state!=='idle' 永久失效，方向键还会在看不见的面板上继续提交答案。
  function stale(mine) {
    return mine !== epoch;
  }

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken()},
      credentials: 'same-origin',
      body: JSON.stringify(body || {})
    }).then(function (response) {
      return response.text().then(function (text) {
        var payload = null;
        try { payload = JSON.parse(text); } catch (e) { payload = null; }
        if (payload) {
          // 拿到可解析信封 = CSRF 这关过了，清掉自愈标记；否则下次真过期会被
          // reloadIfCsrfBlocked 的「已刷过一次」分支静默吞掉
          try { sessionStorage.removeItem('vtCsrfReloaded'); } catch (e) { /* 隐私模式忽略 */ }
        }
        return {
          http: response.status,
          // 登录过期：before_request 把未登录请求 302 到 /login，fetch 跟随后拿到的是
          // 200 + 登录页 HTML。判据沿用项目既有口径（onboarding.js 用 xhr.responseURL 找
          // /login），不是新发明的规则。
          toLogin: /\/login(\?|#|$)/.test(response.url || ''),
          payload: payload,
          text: text
        };
      });
    });
  }

  // 后端业务错误一律 HTTP 500 + Result.code（GlobalExceptionHandler 既有行为），
  // 代理层原样透传，所以语义判读看 code 而不是 response.ok
  function codeOf(wrap) {
    if (wrap.http === 401 || wrap.toLogin) return 401;
    // 响应体不是 JSON（网关错误页、被截断的 HTML）：不能当成功，也不能顺着取 .result
    if (!wrap.payload) return wrap.http === 200 ? 0 : wrap.http;
    if (wrap.payload.success === true) return 200;
    return Number(wrap.payload.code) || wrap.http;
  }

  // 会话过期只有重新登录这一条路；浮层进度不跨登录保留（后端 30 分钟超时语义已覆盖）
  function handleUnauthorized() {
    closeOverlay();
    location.reload();
  }

  function failAction(action) {
    retry = action;
    show(els['vt-error-line'], true);
  }

  // ---------- 卡片 ----------

  function readAddUnknown() {
    // 服务端 per-user 偏好需要新存储面；本期一人一设备，localStorage 足够（US4 §2.1）
    try {
      var stored = localStorage.getItem('vtAddUnknown');
      return stored === null ? true : stored === '1';
    } catch (e) {
      return true;
    }
  }

  function writeAddUnknown(value) {
    try { localStorage.setItem('vtAddUnknown', value ? '1' : '0'); } catch (e) { /* 忽略 */ }
  }

  els['vt-add-unknown'].checked = readAddUnknown();
  els['vt-add-unknown'].addEventListener('change', function () {
    writeAddUnknown(els['vt-add-unknown'].checked);
  });

  function renderLast(report) {
    if (!report || !els['vt-last']) return;
    els['vt-last'].textContent = (report.capped
        ? cappedLabel()
        : '~' + formatRank(report.estimatedSize) + ' (' +
          formatRank(report.ciLow) + '–' + formatRank(report.ciHigh) + ')')
        + ' · ' + isoDate(report.finishedAt);
    show(els['vt-last-line'], true);
  }

  function renderHistory(list) {
    if (!els['vt-history-list']) return;
    els['vt-history-list'].innerHTML = '';
    list.forEach(function (report) {
      var item = document.createElement('li');
      // textContent 拼接：后端数据不进 innerHTML，免得哪天题面/文案里的字符被当标记解析
      item.textContent = isoDate(report.finishedAt) + ' · ' + (report.capped
          ? cappedLabel()
          : '~' + formatRank(report.estimatedSize) + ' (' +
            formatRank(report.ciLow) + '–' + formatRank(report.ciHigh) + ')')
          + ' · ' + report.questionCount + ' ' + window.mbT('questions');
      els['vt-history-list'].appendChild(item);
    });
    show(els['vt-toggle-history'], true);
    renderLast(list[0]);
  }

  function loadHistory() {
    // Why 异步而不是服务端首屏渲染：设置页已经同步等一次 moon-well，再叠一次拉取就等于
    // 把首屏的最坏耗时翻倍（两处各 10s 超时）。历史只是摘要，晚到不影响任何操作。
    // Why 失败全静默：这正是 AC-C1 的「测试卡片独立降级」，弹错误反而打扰档位设置。
    if (!root.dataset.historyUrl) return;
    fetch(root.dataset.historyUrl, {credentials: 'same-origin'}).then(function (response) {
      return response.json().catch(function () { return null; });
    }).then(function (envelope) {
      if (!envelope || envelope.success !== true) return;
      if (!Array.isArray(envelope.result) || !envelope.result.length) return;
      renderHistory(envelope.result);
    }).catch(function () { /* 静默降级为无历史态 */ });
  }

  if (els['vt-toggle-history'] && els['vt-history-list']) {
    els['vt-toggle-history'].addEventListener('click', function (event) {
      event.preventDefault();
      show(els['vt-history-list'], els['vt-history-list'].hidden);
    });
  }

  // ---------- 浮层 ----------
  //
  // 显隐走 bootstrap 原生 modal（jQuery 由 layout 在 block js 之前载入，与 onboarding.js 同依赖）：
  // 蒙层/面板/按钮配色全交给主题的 .modal-* 规则。自造 fixed 蒙层在 caliBlur 主题下会拿到
  // 「浅色面板 + 白色文字」的低对比（无头截图实测），复用 modal 才是真的跟随宿主主题。

  function openOverlay() {
    show(els['vt-error-line'], false);
    show(els['vt-asking'], true);
    show(els['vt-result'], false);
    window.jQuery(els['vt-overlay']).modal('show');
  }

  function closeOverlay() {
    epoch += 1;            // 作废在途请求，见 stale()
    window.jQuery(els['vt-overlay']).modal('hide');
    state = 'idle';
    inFlight = false;
    question = null;
    retry = null;
  }

  function renderProgress(progress) {
    if (!progress || !els['vt-progress-fill']) return;
    var answered = progress.answered || 0;
    els['vt-progress-fill'].style.width =
        Math.min(100, Math.round(answered / PROGRESS_SCALE * 100)) + '%';
    els['vt-progress-count'].textContent = String(answered);
  }

  function renderQuestion(next) {
    question = next;
    els['vt-word'].textContent = next.word;
    els['vt-sentence'].textContent = next.sentence;
    show(els['vt-error-line'], false);
    state = 'asking';
  }

  // ---------- start ----------

  function startTest() {
    if (state !== 'idle' || inFlight) return;
    var mine = epoch;
    inFlight = true;
    els['vt-start'].disabled = true;
    post(root.dataset.startUrl, {}).then(function (wrap) {
      if (stale(mine)) return;
      inFlight = false;
      els['vt-start'].disabled = false;
      var code = codeOf(wrap);
      if (code === 401) { handleUnauthorized(); return; }
      if (reloadIfCsrfBlocked(wrap)) return;
      if (code === 50301) {
        // 词表未就绪：不进入浮层，卡片上给一句「稍后再试」
        setCardStatus(window.mbT('Test unavailable right now, please try again later.'), true);
        return;
      }
      if (code !== 200) {
        setCardStatus(window.mbT('Start failed, please try again.'), true);
        return;
      }
      setCardStatus('', false);
      var result = wrap.payload.result;
      sessionId = result.sessionId;
      renderProgress(result.progress);
      openOverlay();
      renderQuestion(result.question);
    }).catch(function () {
      if (stale(mine)) return;
      inFlight = false;
      els['vt-start'].disabled = false;
      setCardStatus(window.mbT('Start failed, please try again.'), true);
    });
  }

  els['vt-start'].addEventListener('click', startTest);

  // ---------- answer ----------

  function sendAnswer(known) {
    var mine = epoch;
    inFlight = true;
    show(els['vt-error-line'], false);
    // seq 原样回传：同题重发由后端按已落库题数回放，不重复计题（US2 §4）
    post(root.dataset.answerUrl, {
      sessionId: sessionId, seq: question.seq, answer: known ? 1 : 0
    }).then(function (wrap) {
      if (stale(mine)) return;
      inFlight = false;
      var code = codeOf(wrap);
      if (code === 401) { handleUnauthorized(); return; }
      if (reloadIfCsrfBlocked(wrap)) return;
      if (code === 50302) {
        // 会话不可用（不存在/非本人/已作废/已超时）：回卡片态
        closeOverlay();
        setCardStatus(window.mbT('This test session is no longer available.'), true);
        return;
      }
      if (code === 50304) {
        alignSeq(known, wrap.payload && wrap.payload.message);
        return;
      }
      if (code !== 200) {
        failAction(function () { sendAnswer(known); });
        return; // 按钮/按键仍在：下一次提交是同一 seq 的重发
      }
      var result = wrap.payload.result;
      renderProgress(result.progress);
      if (result.finished) {
        // 状态机已自然终止并写好估算；这次 finish 的作用是按开关落生词本 + 取回 Report
        question = null;
        state = 'scoring';
        sendFinish();
        return;
      }
      renderQuestion(result.question);
    }).catch(function () {
      if (stale(mine)) return;
      inFlight = false;
      failAction(function () { sendAnswer(known); });
    });
  }

  function submitAnswer(known) {
    if (state !== 'asking' || inFlight || !question) return;
    sendAnswer(known);
  }

  // 50304 有两种上游文案：「…当前应答第 7 题」（题号错位——中间某题没落库，对齐到服务端给的
  // 题号即可继续答，这正是它单列一码的理由），以及后端复用同码的「该题正在提交，请重试」
  // （VocabularyTestService 的提交互斥）。后者没有数字可对齐，退化成同 seq 重发而不是死链——
  // 错误行点了必须有动作，否则用户只剩刷新一条路。
  function alignSeq(known, message) {
    var matched = /(\d+)/.exec(message || '');
    if (!matched || !question) {
      failAction(function () { sendAnswer(known); });
      return;
    }
    question.seq = Number(matched[1]);
    show(els['vt-error-line'], false);
    retry = null;
  }

  els['vt-known'].addEventListener('click', function () { submitAnswer(true); });
  els['vt-unknown'].addEventListener('click', function () { submitAnswer(false); });
  els['vt-error-line'].addEventListener('click', function () {
    if (retry) { show(els['vt-error-line'], false); retry(); }
  });

  els['vt-exit'].addEventListener('click', function () {
    // 不发 abandon 请求：后端 30 分钟懒作废已覆盖，省一个端点（US4 §2.3）
    closeOverlay();
  });

  // ---------- finish + 结果视图 ----------

  function sendFinish() {
    var mine = epoch;
    inFlight = true;
    post(root.dataset.finishUrl, {
      sessionId: sessionId,
      addUnknownToNotebook: els['vt-add-unknown'].checked
    }).then(function (wrap) {
      if (stale(mine)) return;
      inFlight = false;
      var code = codeOf(wrap);
      if (code === 401) { handleUnauthorized(); return; }
      if (reloadIfCsrfBlocked(wrap)) return;
      if (code === 50302) {
        // 会话在答题途中被作废（30 分钟超时最常见）：重试永远不会成功，回卡片态
        closeOverlay();
        setCardStatus(window.mbT('This test session is no longer available.'), true);
        return;
      }
      if (code !== 200) {
        // 提前交卷不足一组：留在浮层，错误行给出可重试的入口
        failAction(sendFinish);
        return;
      }
      state = 'result';
      renderResult(wrap.payload.result);
    }).catch(function () {
      if (stale(mine)) return;
      inFlight = false;
      failAction(sendFinish);
    });
  }

  function renderResult(report) {
    show(els['vt-asking'], false);
    show(els['vt-result'], true);

    els['vt-size'].textContent = report.capped ? cappedLabel() : '~' + formatRank(report.estimatedSize);
    show(els['vt-range'], !report.capped);
    if (!report.capped) {
      // 刻意不拿 'and' 这类通用短词做 msgid：上游 po 里短词条已有别的语境的译文
      //（language-i18n §5 记过的坑）
      els['vt-range'].textContent = window.mbT('Estimated range') + ': ' +
          formatRank(report.ciLow) + '–' + formatRank(report.ciHigh);
    }
    show(els['vt-capped-note'], !!report.capped);

    renderBandChart(report.bandResults || []);

    // null = 本次没有执行落本（开关关闭，或此前已落过一次的重复提交）；
    // 0 = 执行了落本但本会话没有生词。两者都不上屏（US4 §2.2，用户确认）
    var added = report.addedToNotebook;
    if (typeof added === 'number' && added >= 1) {
      els['vt-notebook-line'].textContent =
          window.mbT('Unknown words were added to your notebook') + ' (+' + added + ')';
      show(els['vt-notebook-line'], true);
    } else {
      show(els['vt-notebook-line'], false);
    }
    renderLast(report);
  }

  function renderBandChart(bandResults) {
    els['vt-band-chart'].innerHTML = '';
    bandResults.forEach(function (row) {
      var line = document.createElement('div');
      line.className = 'vt-bar-row';

      var label = document.createElement('span');
      label.className = 'vt-bar-label';
      label.textContent = bandLabel(row.band);

      // 复用 bootstrap 的 progress/progress-bar：颜色与高度随宿主主题走，不自造配色
      var track = document.createElement('div');
      track.className = 'progress vt-bar-track';
      var fill = document.createElement('div');
      fill.className = 'progress-bar';
      // rate 是后端算好的 0–1 掌握率；未测档 questions=0，画空条
      fill.style.width = Math.round((row.rate || 0) * 100) + '%';
      track.appendChild(fill);

      var count = document.createElement('span');
      count.className = 'vt-bar-count';
      count.textContent = row.questions > 0 ? row.known + '/' + row.questions : '—';

      line.appendChild(label);
      line.appendChild(track);
      line.appendChild(count);
      els['vt-band-chart'].appendChild(line);
    });
  }

  els['vt-done'].addEventListener('click', function () {
    closeOverlay();
    setCardStatus('', false);
  });

  // ---------- 键盘 ----------

  document.addEventListener('keydown', function (e) {
    if (state !== 'asking') return;
    // IME 守卫（R114 同口径）：ime_guard.js 只守 INPUT/TEXTAREA 且无对外 API，
    // 浮层的监听挂在 document 上不经过它，所以这里自带判定
    if (e.isComposing || e.keyCode === 229) return;
    if (e.key === 'ArrowLeft' || e.key === 'j' || e.key === 'J') {
      // 键位按屏上按钮左右顺序映射：左键=「I know it」、右键=「Not sure」，与按钮排布一致
      e.preventDefault();
      submitAnswer(true);
    } else if (e.key === 'ArrowRight' || e.key === 'k' || e.key === 'K') {
      e.preventDefault();
      submitAnswer(false);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      closeOverlay();
    }
  });

  loadHistory();
})();
