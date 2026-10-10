// 每日学习页前端逻辑（R132 / B3）。
//
// Why 独立文件而不是模板内联：队列渲染 + 三题型状态机 + 计划/统计/匹配三路异步加载
// 超过 300 行，内联会把模板翻倍（vocab-test.js 同款取舍）。
//
// 文案取词通道：window.mbT 由 i18n_seed.html 注入（layout.html 在本脚本之前 include），
// 词条必须在渲染时取、不能在脚本加载时快照（vocab-test.js 同纪律）；
// 字面量由 tests/test_i18n_seed_contract.py 校验（必须进种子且 zh 译文非空）。
//
// 契约（moon-well learning 模块，LLD §4）：统一 Result 信封 {success, result, message}；
// 业务错误 HTTP 500 + Result.code（50501 计划行不存在 / 50502 grade 非法 / 50503 四股和），
// 代理层薄透传——前端按 code 分支，scheduleId 传回的是字符串（防精度口径）。
(function () {
  'use strict';

  function mbT(msgid) {
    return (window.MB_I18N && window.MB_I18N[msgid]) || msgid;
  }

  var root = document.getElementById('ln-card');
  if (!root) return;

  var $ = function (id) { return document.getElementById(id); };
  var els = {
    csrf: $('ln-csrf'), error: $('ln-error'), errorText: $('ln-error-text'),
    retry: $('ln-retry'), stats: $('ln-stats'), todayReview: $('ln-today-review'),
    dueTomorrow: $('ln-due-tomorrow'), mastered: $('ln-mastered'),
    retention: $('ln-retention'), plan: $('ln-plan'), strandLine: $('ln-strand-line'),
    newWordsLine: $('ln-new-words-line'), empty: $('ln-empty'),
    todayDone: $('ln-today-done'), continueBtn: $('ln-continue'),
    word: $('ln-word'), encounters: $('ln-encounters'), stem: $('ln-stem'),
    context: $('ln-context'), contextSource: $('ln-context-source'),
    choices: $('ln-choices'), recall: $('ln-recall'), reveal: $('ln-reveal'),
    spell: $('ln-spell'), spellInput: $('ln-spell-input'), spellCheck: $('ln-spell-check'),
    grades: $('ln-grades'),
    feedback: $('ln-feedback'), cardError: $('ln-card-error'), skip: $('ln-skip'),
    matchRoot: $('ln-match-root'), matchStatus: $('ln-match-status'),
    matchList: $('ln-match-list'),
  };

  var queue = [];          // 剩余队列（每项已含 questionType 与 choices）
  var current = null;      // 当前卡
  var answeredAt = 0;      // 本卡展示时刻：作答延迟 = 提交时刻 - 展示时刻
  var inFlight = false;    // 在途锁：评分按钮连击忽略
  var revealing = false;   // RECALL 题已揭示
  var lastStats = null;    // 最近一次统计：队列打空时判断「还有余量→继续」还是「真没了」

  // ---------- 小工具 ----------

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

  function csrfToken() {
    return els.csrf ? els.csrf.value : '';
  }

  function fail(message) {
    show(els.error, true);
    els.errorText.textContent = message;
  }

  function httpJson(url, options) {
    return fetch(url, options).then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { /* 非 JSON 按失败处理 */ }
        return { ok: response.ok, status: response.status, data: data, raw: text };
      });
    });
  }

  function getJson(url) {
    return httpJson(url, { credentials: 'same-origin' });
  }

  function postJson(url, body) {
    return httpJson(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(body || {}),
    });
  }

  function isBusinessError(response) {
    return response.data && response.data.success === false && response.data.code &&
      response.data.code !== 200;
  }

  // ---------- 统计头 ----------

  function renderStats(result) {
    if (!result) return;
    lastStats = result;
    // R144：今日复习进度 x/20（min 封顶——超出目标继续答也不涨）；dueNow 逾期欠账
    // 仍在接口里但不再上墙（1949 拍脸上=劝退，进度式才是今日承诺）
    if (result.todayReviewed == null || result.todayTarget == null) {
      els.todayReview.textContent = '–';   // 部署时差（旧后端无新字段）按缺数处理
    } else {
      els.todayReview.textContent =
        Math.min(result.todayReviewed, result.todayTarget) + '/' + result.todayTarget;
    }
    els.dueTomorrow.textContent = result.dueTomorrow == null ? '–' : result.dueTomorrow;
    els.mastered.textContent = result.mastered == null ? '–' : result.mastered;
    show(els.stats, true);
    if (result.retention7d == null) {
      els.retention.textContent = '–';
    } else {
      els.retention.textContent = result.retention7d + '%';
    }
  }

  // ---------- 每日计划头 ----------

  var STRAND_LABELS = [
    ['inputMinutes', _('Reading input'), 'inputPct'],
    ['languageMinutes', _('Word study'), 'languagePct'],
    ['outputMinutes', _('Speaking & writing'), 'outputPct'],
    ['fluencyMinutes', _('Fluency drills'), 'fluencyPct'],
  ];

  function renderPlan(result) {
    if (!result || !result.strands) return;
    var budget = result.strands;
    var parts = STRAND_LABELS.map(function (pair) {
      return mbT(pair[1]) + ' ' + budget[pair[0]] + 'min';
    });
    els.strandLine.textContent = mbT('Time budget by strand') + '（' +
      mbT('{{minutes}} minutes a day').replace('{{minutes}}', result.settings && result.settings.dailyMinutes) +
      '）：' + parts.join(' · ');
    if (result.newWords && result.newWords.length) {
      var names = result.newWords.slice(0, 8).map(function (item) { return item.word; });
      els.newWordsLine.textContent = mbT('New words today') + '（' + result.newWords.length + '）：' +
        names.join(', ') + (result.newWords.length > 8 ? ' …' : '');
      show(els.newWordsLine, true);
    } else {
      els.newWordsLine.textContent = mbT('No fresh words yet — mark unknown words while reading.');
      show(els.newWordsLine, true);
    }
    show(els.plan, true);
  }

  // ---------- 复习队列 ----------

  function renderQueue(items) {
    queue = Array.isArray(items) ? items.slice() : [];
    show(els.todayDone, false);   // 新一批开始，收起上一批的完成态
    nextCard();
  }

  function nextCard() {
    current = queue.shift();
    if (!current) {
      // R144：打空≠没词了——统计里 dueNow>0 说明还有逾期余量，给「继续复习」；
      // 真没了才显示 Keep reading。原先一律显示后者是失实承诺。
      var moreDue = !!(lastStats && lastStats.dueNow != null && lastStats.dueNow > 0);
      show(els.empty, !moreDue);
      show(els.todayDone, moreDue);
      show(root, false);
      return;
    }
    // 服务端约定（LearningChoiceService）：干扰池不足时 choices=null，选择题降级回忆题，
    // 不出「无法作答的死卡」——服务端不回改题型字段，客户端按契约降级。
    if (current.questionType === 'CHOOSE' && !(current.choices && current.choices.length > 1)) {
      current.questionType = 'RECALL';
    }
    show(els.empty, false);
    show(root, true);
    revealing = false;
    inFlight = false;
    answeredAt = Date.now();
    els.word.textContent = current.word;
    els.word.className = 'ln-word';
    show(els.encounters, !!(current.encounterCount && current.encounterCount > 0));
    if (current.encounterCount > 0) {
      els.encounters.textContent = mbT('met {{count}}×').replace('{{count}}', current.encounterCount);
    }
    // R137 题干：释义即题面，词面即答案——有释义时藏词面与语境卡（原句含目标词），
    // 揭示/判定后再亮。无释义统一降级 SELF（亮词自评，Anki 基础模式）：
    // CHOOSE 没题干会变「选它自己」、RECALL 的 Reveal 变「揭示已亮着的词」、
    // SPELL 没题干变「听写自己」，全不成立，只有自评保底诚实可答。
    var hasMeaning = !!(current.meaning && current.meaning.length);
    if (!hasMeaning) {
      current.questionType = 'SELF';
    }
    show(els.stem, hasMeaning);
    if (hasMeaning) {
      els.stem.textContent = mbT('Which word means “{{meaning}}”?')
        .replace('{{meaning}}', current.meaning);
    }
    show(els.word, !hasMeaning);
    showContext(hasMeaning ? false : !!(current.contextSentence && current.contextSentence.length > 0));
    els.spellInput.value = '';
    els.spellInput.className = 'form-control';
    show(els.feedback, false);
    show(els.cardError, false);
    var type = current.questionType;
    show(els.recall, type === 'RECALL');
    show(els.reveal, type === 'RECALL');
    show(els.spell, type === 'SPELL');
    renderChoices(current);
    show(els.grades, type === 'SELF');
    if (type === 'SPELL' && hasMeaning) {
      els.spellInput.focus();
    }
  }

  /** 语境卡显隐（S1）：出处与原句一起亮。 */
  function showContext(visible) {
    var hasContext = !!(current && current.contextSentence && current.contextSentence.length > 0);
    var on = visible && hasContext;
    els.context.textContent = on ? '“' + current.contextSentence + '”' : '';
    show(els.context, on);
    els.contextSource.textContent = on
      ? (current.contextBook || '') + (current.contextChapter ? ' · ' + current.contextChapter : '')
      : '';
    show(els.contextSource, on);
  }

  function renderChoices(item) {
    var isChoose = item.questionType === 'CHOOSE' && item.choices && item.choices.length > 1;
    show(els.choices, isChoose);
    if (!isChoose) return;
    var buttons = els.choices.querySelectorAll('.ln-choice');
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      if (item.choices[i]) {
        btn.textContent = item.choices[i];
        btn.className = 'btn btn-default ln-choice';  // 上一张的红/绿标记不复用
        btn.hidden = false;
        btn.style.display = '';   // .btn 有 inline-block 作者规则，只删属性藏不住/显不回
        btn.onclick = onChoicePicked;
      } else {
        btn.hidden = true;
        btn.style.display = 'none';  // 不足四个选项时空按钮必须真隐藏（show 同款双保险）
      }
    }
  }

  // CHOOSE：选中即判定（对→评分；错→亮出正确项并进评分，grade 由用户自报）
  function onChoicePicked(event) {
    if (inFlight || !current) return;
    var picked = event.target.textContent;
    var correct = picked === current.word;
    var buttons = els.choices.querySelectorAll('.ln-choice');
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].textContent === current.word) {
        buttons[i].className = 'btn btn-success ln-choice';
      } else if (buttons[i] === event.target && !correct) {
        buttons[i].className = 'btn btn-danger ln-choice';
      }
    }
    show(els.recall, false);
    show(els.grades, true);
    if (!correct) {
      show(els.feedback, true);
      els.feedback.textContent = mbT('The answer is highlighted — rate yourself honestly.');
    }
  }

  // RECALL：揭示后亮词面与语境，出评分
  function onReveal() {
    if (!current) return;
    revealing = true;
    show(els.recall, false);
    show(els.word, true);
    showContext(true);
    show(els.grades, true);
  }

  // SPELL：客户端归一比对（与服务端 QuestionTypePicker.normalize 同口径：
  // trim / 小写 / 弯撇号归一）；判完亮词面与语境，错了附正确拼写，评分自报。
  function spellMatches(expected, actual) {
    function norm(s) {
      return (s || '').trim().toLowerCase().replace(/’/g, "'");
    }
    return norm(expected) === norm(actual);
  }

  function onSpellCheck() {
    if (!current || inFlight) return;
    var typed = els.spellInput.value;
    if (!typed.trim()) return;   // 空提交不判定，等用户输入
    var correct = spellMatches(current.word, typed);
    show(els.spell, false);
    show(els.word, true);
    showContext(true);
    if (!correct) {
      els.word.className = 'ln-word text-danger';
      show(els.feedback, true);
      els.feedback.textContent = mbT('Correct spelling: {{word}}').replace('{{word}}', current.word);
    } else {
      els.word.className = 'ln-word text-success';
    }
    show(els.grades, true);
  }

  function submitGrade(grade, latencyMs) {
    if (inFlight || !current) return;
    inFlight = true;
    var payload = { scheduleId: current.scheduleId, grade: grade };
    var latency = latencyMs != null ? latencyMs : Math.min(Date.now() - answeredAt, 300000);
    if (latency > 0) payload.latencyMs = latency;
    postJson(window.learningUrls.answer, payload).then(function (response) {
      if (!response.ok || isBusinessError(response)) {
        inFlight = false;
        show(els.cardError, true);
        els.cardError.textContent = (response.data && response.data.message) ||
          mbT('Something went wrong — try again.');
        return;
      }
      var result = response.data && response.data.result;
      if (result && result.message) {
        show(els.feedback, true);
        els.feedback.textContent = result.message;
      }
      // 轻过渡后进下一张（500ms 让用户看到「下次再见」提示）
      window.setTimeout(function () { nextCard(); refreshStats(); }, 500);
    }).catch(function () {
      inFlight = false;
      show(els.cardError, true);
      els.cardError.textContent = mbT('Network error — try again.');
    });
  }

  function refreshStats() {
    getJson(window.learningUrls.stats).then(function (response) {
      if (response.ok && response.data && response.data.result) renderStats(response.data.result);
    }).catch(function () { /* 统计刷新失败不打扰复习 */ });
  }

  // ---------- 难度匹配（B3b）----------

  var MATCH_LEVELS = {
    EASY: { cls: 'label-success', name: _('Easy read') },
    FIT: { cls: 'label-primary', name:_('Just right') },
    HARD: { cls: 'label-warning', name: _('Challenging') },
  };

  function renderMatches(items) {
    if (!els.matchList) return;
    els.matchList.innerHTML = '';
    if (!Array.isArray(items) || !items.length) {
      els.matchStatus.textContent = mbT('No books to match yet.');
      return;
    }
    var stale = 0;
    items.forEach(function (item) {
      var li = document.createElement('li');
      var link = document.createElement('a');
      link.href = '/books/' + item.bookId + '/page/1';
      link.textContent = item.title || ('#' + item.bookId);
      li.appendChild(link);
      if (item.densityPct == null) {
        var pending = document.createElement('span');
        pending.className = 'ln-match-density';
        pending.textContent = mbT('estimating…');
        li.appendChild(pending);
        stale++;
      } else {
        var level = MATCH_LEVELS[item.level] || MATCH_LEVELS.FIT;
        var badge = document.createElement('span');
        badge.className = 'label ln-match-badge ' + level.cls;
        badge.textContent = mbT(level.name);
        li.appendChild(badge);
        var density = document.createElement('span');
        density.className = 'ln-match-density';
        density.textContent = item.densityPct + '% ' + mbT('unknown words') +
          (item.unknownTokenCount != null ? ' (~' + item.unknownTokenCount + ')' : '');
        li.appendChild(density);
        if (item.unknownSample && item.unknownSample.length && item.level === 'HARD') {
          var sample = document.createElement('span');
          sample.className = 'ln-match-sample';
          sample.textContent = item.unknownSample.slice(0, 5).join(', ');
          li.appendChild(sample);
        }
        if (item.upToDate === false) stale++;
      }
      els.matchList.appendChild(li);
    });
    els.matchStatus.textContent = stale > 0 ? mbT('Profiles refresh as your vocabulary grows.') : '';
  }

  function loadMatches() {
    if (!els.matchRoot || !window.learningUrls) return;
    getJson(window.learningUrls.matchBooks).then(function (response) {
      if (response.ok && response.data && response.data.result) {
        renderMatches(response.data.result);
      } else {
        els.matchStatus.textContent = mbT('Difficulty match is unavailable right now.');
      }
    }).catch(function () {
      els.matchStatus.textContent = mbT('Difficulty match is unavailable right now.');
    });
  }

  // ---------- 启动 ----------

  // 队列加载独立成函数：页面初载与「继续复习」共用（R144）
  function loadQueue() {
    getJson(window.learningUrls.queue + '?limit=20').then(function (response) {
      if (response.ok && response.data && response.data.success) {
        renderQueue(response.data.result);
      } else {
        fail((response.data && response.data.message) || mbT('Failed to load the review queue.'));
      }
    }).catch(function () {
      fail(mbT('Network error — press retry.'));
    });
  }

  function loadAll() {
    show(els.error, false);
    getJson(window.learningUrls.plan).then(function (response) {
      if (response.ok && response.data && response.data.result) {
        renderPlan(response.data.result);
      }
    }).catch(function () { /* 计划头失败不挡队列 */ });
    getJson(window.learningUrls.stats).then(function (response) {
      if (response.ok && response.data && response.data.result) {
        renderStats(response.data.result);
      }
    }).catch(function () { /* 统计失败不挡队列 */ });
    loadQueue();
    loadMatches();
  }

  els.retry.addEventListener('click', loadAll);
  els.continueBtn.addEventListener('click', loadQueue);
  els.reveal.addEventListener('click', onReveal);
  els.spellCheck.addEventListener('click', onSpellCheck);
  // 回车=检查：拼写题最高频动作，别让用户去摸鼠标
  els.spellInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      onSpellCheck();
    }
  });
  els.skip.addEventListener('click', function () { nextCard(); });
  els.grades.querySelectorAll('[data-grade]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      submitGrade(parseInt(btn.getAttribute('data-grade'), 10));
    });
  });

  loadAll();
})();
