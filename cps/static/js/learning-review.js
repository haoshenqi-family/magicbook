// 复习队列子页面（R166 自 learning.js 迁出；队列逻辑本体属 R132/R137/R144）。
//
// 契约（moon-well learning 模块，LLD §4）：统一 Result 信封 {success, result, message}；
// 业务错误 HTTP 500 + Result.code（50502 grade 非法），代理层薄透传——前端按 code 分支，
// scheduleId 传回的是字符串（防精度口径）。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, getJson = MB.getJson,
      postJson = MB.postJson, isBusinessError = MB.isBusinessError;
  var urls = window.learningUrls || {};

  var root = $('ln-card');
  if (!root) return;

  var els = {};
  ['ln-error', 'ln-error-text', 'ln-retry', 'ln-progress', 'ln-empty', 'ln-today-done',
   'ln-continue', 'ln-card', 'ln-word', 'ln-encounters', 'ln-stem', 'ln-context',
   'ln-context-source', 'ln-choices', 'ln-recall', 'ln-reveal', 'ln-spell',
   'ln-spell-input', 'ln-spell-check', 'ln-grades', 'ln-feedback', 'ln-card-error',
   'ln-skip', 'ln-note',
  ].forEach(function (id) { els[id] = $(id); });

  // 后端会认识而前端不认识的题型一律按 SELF 出卡：未知题型若原样渲染，四选一/揭示/
  // 拼写三个区都不亮，卡片没有任何作答入口（死卡）。R167 起后端新增 DISCRIMINATE，
  // 前后端发布不可能永远同刻到位，这条兜底是那个窗口的保底。
  var KNOWN_TYPES = ['CHOOSE', 'RECALL', 'SPELL', 'LISTEN_CHOOSE', 'LISTEN_SPELL',
                     'CONTEXT_CLOZE', 'DISCRIMINATE'];

  var queue = [];          // 剩余队列（每项已含 questionType 与 choices）
  var current = null;      // 当前卡
  var answeredAt = 0;      // 本卡展示时刻：作答延迟 = 提交时刻 - 展示时刻
  var inFlight = false;    // 在途锁：评分按钮连击忽略
  var lastStats = null;    // 最近一次统计：队列打空时判断「还有余量→继续」还是「真没了」

  function fail(message) {
    show(els['ln-error'], true);
    els['ln-error-text'].textContent = message;
  }

  // ---------- 统计 ----------

  // R144：今日复习进度 x/20（min 封顶——超出目标继续答也不涨）；dueNow 逾期欠账
  // 仍在接口里但不再上墙（1949 拍脸上=劝退，进度式才是今日承诺）
  function renderStats(result) {
    if (!result) return;
    lastStats = result;
    if (result.todayReviewed == null || result.todayTarget == null) {
      show(els['ln-progress'], false);   // 部署时差（旧后端无新字段）按缺数处理
      return;
    }
    els['ln-progress'].textContent = mbT("Today's review") + ' ' +
      Math.min(result.todayReviewed, result.todayTarget) + '/' + result.todayTarget;
    show(els['ln-progress'], true);
  }

  function refreshStats() {
    getJson(urls.stats).then(function (response) {
      if (response.ok && response.data && response.data.result) renderStats(response.data.result);
    }).catch(function () { /* 统计刷新失败不打扰复习 */ });
  }

  // ---------- 三题型状态机 ----------

  function renderQueue(items) {
    queue = Array.isArray(items) ? items.slice() : [];
    show(els['ln-today-done'], false);   // 新一批开始，收起上一批的完成态
    nextCard();
  }

  function nextCard() {
    current = queue.shift();
    if (!current) {
      // R144：打空≠没词了——统计里 dueNow>0 说明还有逾期余量，给「继续复习」；
      // 真没了才显示 Keep reading。原先一律显示后者是失实承诺。
      var moreDue = !!(lastStats && lastStats.dueNow != null && lastStats.dueNow > 0);
      show(els['ln-empty'], !moreDue);
      show(els['ln-today-done'], moreDue);
      show(root, false);
      return;
    }
    // 本地呈现态 mode 与后端题型 questionType 分开存：前端会因为缺选项/缺释义把卡
    // 降级（SELF/RECALL），但回传给后端记答题日志的必须是它当初发下来的题型——
    // SELF 后端根本不认识，而降级后的 RECALL 会掩盖「当时出的是辨析题」这个事实。
    var mode = KNOWN_TYPES.indexOf(current.questionType) >= 0 ? current.questionType : 'SELF';
    // 服务端约定（ReviewChoiceService）：干扰池不足时 choices=null，选择题降级回忆题，
    // 不出「无法作答的死卡」——服务端不回改题型字段，客户端按契约降级。
    if ((mode === 'CHOOSE' || mode === 'DISCRIMINATE') &&
        !(current.choices && current.choices.length > 1)) {
      mode = 'RECALL';
    }
    // R137 题干：释义即题面，词面即答案——有释义时藏词面与语境卡（原句含目标词），
    // 揭示/判定后再亮。CHOOSE/RECALL/SPELL 没释义就不成立（选它自己 / 揭示已亮着的词 /
    // 听写自己），只有 SELF 保底诚实可答。
    // 辨析题例外：它的题干就是词面本身（问「哪个词跟它最接近」），缺释义照样可答。
    var hasMeaning = !!(current.meaning && current.meaning.length);
    if (!hasMeaning && mode !== 'DISCRIMINATE') {
      mode = 'SELF';
    }
    current.mode = mode;
    var isDiscriminate = mode === 'DISCRIMINATE';
    show(els['ln-empty'], false);
    show(root, true);
    inFlight = false;
    answeredAt = Date.now();
    els['ln-word'].textContent = current.word;
    els['ln-word'].className = 'ln-word';
    show(els['ln-encounters'], !!(current.encounterCount && current.encounterCount > 0));
    if (current.encounterCount > 0) {
      els['ln-encounters'].textContent = mbT('met {{count}}×').replace('{{count}}', current.encounterCount);
    }
    show(els['ln-stem'], hasMeaning || isDiscriminate);
    if (isDiscriminate) {
      els['ln-stem'].textContent = mbT('Which word below is closest in meaning to it?');
    } else if (hasMeaning) {
      els['ln-stem'].textContent = mbT('Which word means “{{meaning}}”?')
        .replace('{{meaning}}', current.meaning);
    }
    show(els['ln-word'], !hasMeaning || isDiscriminate);
    showContext(!hasMeaning && !isDiscriminate &&
      !!(current.contextSentence && current.contextSentence.length > 0));
    els['ln-spell-input'].value = '';
    els['ln-spell-input'].className = 'form-control';
    show(els['ln-feedback'], false);
    show(els['ln-card-error'], false);
    show(els['ln-note'], false);
    show(els['ln-recall'], mode === 'RECALL');
    show(els['ln-reveal'], mode === 'RECALL');
    show(els['ln-spell'], mode === 'SPELL');
    renderChoices(current);
    show(els['ln-grades'], mode === 'SELF');
    if (mode === 'SPELL' && hasMeaning) {
      els['ln-spell-input'].focus();
    }
  }

  /** 语境卡显隐（S1）：出处与原句一起亮。 */
  function showContext(visible) {
    var hasContext = !!(current && current.contextSentence && current.contextSentence.length > 0);
    var on = visible && hasContext;
    els['ln-context'].textContent = on ? '“' + current.contextSentence + '”' : '';
    show(els['ln-context'], on);
    els['ln-context-source'].textContent = on
      ? (current.contextBook || '') + (current.contextChapter ? ' · ' + current.contextChapter : '')
      : '';
    show(els['ln-context-source'], on);
  }

  function renderChoices(item) {
    var isChoice = (item.mode === 'CHOOSE' || item.mode === 'DISCRIMINATE') &&
      item.choices && item.choices.length > 1;
    show(els['ln-choices'], isChoice);
    if (!isChoice) return;
    var buttons = els['ln-choices'].querySelectorAll('.ln-choice');
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

  // 选择题（CHOOSE / DISCRIMINATE）：选中即判定（对→评分；错→亮出正确项并进评分，
  // grade 由用户自报）
  function onChoicePicked(event) {
    if (inFlight || !current) return;
    // 正确项按 answer 判，不再按 word：辨析题的正确项是该词的同义词、word 只是调度锚点
    // 且不在选项里，沿用 word 会把选对判成选错（R167）。老后端不发 answer 时回退 word，
    // 行为与改动前逐字一致。
    var answer = current.answer || current.word;
    var picked = event.target.textContent;
    var correct = picked === answer;
    var buttons = els['ln-choices'].querySelectorAll('.ln-choice');
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].textContent === answer) {
        buttons[i].className = 'btn btn-success ln-choice';
      } else if (buttons[i] === event.target && !correct) {
        buttons[i].className = 'btn btn-danger ln-choice';
      }
    }
    show(els['ln-recall'], false);
    show(els['ln-grades'], true);
    if (current.answerNote) {
      els['ln-note'].textContent = current.answerNote;
      show(els['ln-note'], true);
    }
    if (!correct) {
      show(els['ln-feedback'], true);
      els['ln-feedback'].textContent = mbT('The answer is highlighted — rate yourself honestly.');
    }
  }

  // RECALL：揭示后亮词面与语境，出评分
  function onReveal() {
    if (!current) return;
    show(els['ln-recall'], false);
    show(els['ln-word'], true);
    showContext(true);
    show(els['ln-grades'], true);
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
    var typed = els['ln-spell-input'].value;
    if (!typed.trim()) return;   // 空提交不判定，等用户输入
    var correct = spellMatches(current.word, typed);
    show(els['ln-spell'], false);
    show(els['ln-word'], true);
    showContext(true);
    if (!correct) {
      els['ln-word'].className = 'ln-word text-danger';
      show(els['ln-feedback'], true);
      els['ln-feedback'].textContent = mbT('Correct spelling: {{word}}').replace('{{word}}', current.word);
    } else {
      els['ln-word'].className = 'ln-word text-success';
    }
    show(els['ln-grades'], true);
  }

  function submitGrade(grade, latencyMs) {
    if (inFlight || !current) return;
    inFlight = true;
    var payload = { scheduleId: current.scheduleId, grade: grade };
    // 回传后端**当初发下来的**题型（不是本地降级后的 mode）：辨析题在混出带里随机出现，
    // 服务端事后重算会错一半，而该字段是四技能统计与保持率的底座（R167）。
    // SELF 是前端呈现态、后端不认识，此时后端按缺省回落重算。
    if (KNOWN_TYPES.indexOf(current.questionType) >= 0) {
      payload.questionType = current.questionType;
    }
    var latency = latencyMs != null ? latencyMs : Math.min(Date.now() - answeredAt, 300000);
    if (latency > 0) payload.latencyMs = latency;
    postJson(urls.answer, payload).then(function (response) {
      if (!response.ok || isBusinessError(response)) {
        inFlight = false;
        show(els['ln-card-error'], true);
        els['ln-card-error'].textContent = (response.data && response.data.message) ||
          mbT('Something went wrong — try again.');
        return;
      }
      var result = response.data && response.data.result;
      if (result && result.message) {
        show(els['ln-feedback'], true);
        els['ln-feedback'].textContent = result.message;
      }
      // 轻过渡后进下一张（500ms 让用户看到「下次再见」提示）
      window.setTimeout(function () { nextCard(); refreshStats(); }, 500);
    }).catch(function () {
      inFlight = false;
      show(els['ln-card-error'], true);
      els['ln-card-error'].textContent = mbT('Network error — try again.');
    });
  }

  // ---------- 启动 ----------

  // 队列加载独立成函数：页面初载与「继续复习」共用（R144）
  function loadQueue() {
    getJson(urls.queue + '?limit=20').then(function (response) {
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
    show(els['ln-error'], false);
    refreshStats();
    loadQueue();
  }

  els['ln-retry'].addEventListener('click', loadAll);
  els['ln-continue'].addEventListener('click', loadQueue);
  els['ln-reveal'].addEventListener('click', onReveal);
  els['ln-spell-check'].addEventListener('click', onSpellCheck);
  // 回车=检查：拼写题最高频动作，别让用户去摸鼠标
  els['ln-spell-input'].addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      onSpellCheck();
    }
  });
  els['ln-skip'].addEventListener('click', function () { nextCard(); });
  els['ln-grades'].querySelectorAll('[data-grade]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      submitGrade(parseInt(btn.getAttribute('data-grade'), 10));
    });
  });

  loadAll();
})();
