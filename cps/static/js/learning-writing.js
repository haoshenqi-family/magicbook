// 写作工坊子页面（R166 自 speaking_writing.js 迁出；批改契约属 R152/B1）。
//
// 契约（moon-well learning B1，LLD us2-b1-output-lld）：统一 Result 信封
// {success, result, message}；代理已做域校验，本文件按 success/message 分支。
// 出题/批改都是 LLM 端点（实测 10-40s），按钮一律在途锁防连击。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, clear = MB.clear, li = MB.li,
      esc = MB.esc, busy = MB.busy, getJson = MB.getJson, postJson = MB.postJson,
      resultOf = MB.resultOf;
  var urls = window.learningUrls || {};

  var els = {};
  ['sw-w-mode', 'sw-w-cefr', 'sw-w-topic', 'sw-w-book', 'sw-w-generate',
   'sw-w-task', 'sw-w-prompt', 'sw-w-requirements', 'sw-w-tips',
   'sw-w-text', 'sw-w-submit', 'sw-w-status',
   'sw-w-review', 'sw-w-progress', 'sw-w-overall', 'sw-w-scores',
   'sw-w-sentences', 'sw-w-upgrades',
   'sw-w-history-panel', 'sw-w-history',
   'sw-w-resume-bar', 'sw-w-resume', 'sw-w-resume-label',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-w-generate']) return;

  var writing = { taskId: null, lastDraftNo: null, resumeTaskId: null };
  // busy() 会把文案换成「批改中…」再按 dataset.label 还原，所以按钮基准文案
  // 只在初始化时取一次，之后由 refreshSubmitButton 统一改写
  var SUBMIT_LABEL = els['sw-w-submit'].textContent;

  function fillList(node, items) {
    clear(node);
    (items || []).forEach(function (line) {
      node.appendChild(li(line));
    });
  }

  /**
   * 提交按钮跟着草稿状态走（R168 续写）：一个编辑区、一个提交按钮，
   * 目标端点由 lastDraftNo 决定——避免「初稿/修订」两个框都能提交同一稿的歧义。
   * 两稿封顶是上游规则（50513），到 2 就把按钮 disable 而不是让用户去撞错误。
   */
  function refreshSubmitButton() {
    var btn = els['sw-w-submit'];
    var done = writing.lastDraftNo != null && writing.lastDraftNo >= 2;
    var label = done ? mbT('Both drafts finished')
      : (writing.lastDraftNo === 1 ? mbT('Submit revision') : SUBMIT_LABEL);
    btn.disabled = done;
    // dataset.label 是 busy() 还原时的基准文案，必须与当前意图一致，
    // 否则「批改中…」结束会退回初稿态的文案（探针实测踩过）
    btn.dataset.label = label;
    btn.textContent = label;
  }

  function draftEndpoint() {
    return writing.lastDraftNo && writing.lastDraftNo >= 1 ? urls.writingRevise : urls.writingSubmit;
  }

  function scoreRow(label, value) {
    var wrap = document.createElement('div');
    wrap.className = 'sw-score';
    var b = document.createElement('b');
    b.textContent = value == null ? '–' : value;
    var span = document.createElement('span');
    span.textContent = label;
    wrap.appendChild(b);
    wrap.appendChild(span);
    return wrap;
  }

  function renderReview(review) {
    show(els['sw-w-review'], true);
    esc(els['sw-w-overall'], review.overall);
    var progress = els['sw-w-progress'];
    if (review.progress) {
      esc(progress, review.progress);
      progress.hidden = false;
    } else {
      progress.hidden = true;
    }
    clear(els['sw-w-scores']);
    els['sw-w-scores'].appendChild(scoreRow(mbT('Grammar'), review.scores && review.scores.grammar));
    els['sw-w-scores'].appendChild(scoreRow(mbT('Vocabulary'), review.scores && review.scores.vocabulary));
    els['sw-w-scores'].appendChild(scoreRow(mbT('Coherence'), review.scores && review.scores.coherence));
    els['sw-w-scores'].appendChild(scoreRow(mbT('Task completion'), review.scores && review.scores.task));
    clear(els['sw-w-sentences']);
    (review.sentences || []).forEach(function (item) {
      var line = document.createElement('li');
      var strong = document.createElement('strong');
      esc(strong, item.text);
      line.appendChild(strong);
      line.appendChild(document.createTextNode(' — ' + (item.comment || '')));
      if (item.suggestion) {
        var tip = document.createElement('div');
        tip.className = 'text-muted';
        esc(tip, mbT('Suggestion: ') + item.suggestion);
        line.appendChild(tip);
      }
      els['sw-w-sentences'].appendChild(line);
    });
    clear(els['sw-w-upgrades']);
    (review.upgrades || []).forEach(function (item) {
      els['sw-w-upgrades'].appendChild(li(
        (item.from || '') + ' → ' + (item.to || '') + (item.why ? '（' + item.why + '）' : '')));
    });
  }

  function loadWritingHistory() {
    getJson(urls.writingHistory).then(function (response) {
      var items = resultOf(response) || [];
      var panel = els['sw-w-history-panel'];
      if (!items.length) {
        show(panel, false);
        show(els['sw-w-resume-bar'], false);
        return;
      }
      var list = els['sw-w-history'];
      clear(list);
      items.forEach(function (task) {
        var line = li((task.prompt || mbT('Free writing')) + ' · ' + statusLabel(task));
        // R168：历史行从「只读摘要」变成续写入口——草稿正文与上次批改都在详情里
        line.style.cursor = 'pointer';
        line.title = mbT('Click to load this task back');
        line.addEventListener('click', function () { resume(task.taskId); });
        list.appendChild(line);
      });
      show(panel, true);
      armResumeBar(items);
    }).catch(function () {
      show(els['sw-w-history-panel'], false);
      show(els['sw-w-resume-bar'], false);
    });
  }

  function statusLabel(item) {
    if (!item.lastDraftNo) return mbT('Not started yet');
    if (item.lastDraftNo < 2) return mbT('Draft {{n}} submitted · revision pending')
      .replace('{{n}}', item.lastDraftNo);
    return mbT('Both drafts finished');
  }

  // 列表按创建时间倒序，第一条没写完的就是「上次未完成的写作」
  function armResumeBar(items) {
    var candidate = null;
    items.forEach(function (item) {
      if (!candidate && (item.lastDraftNo == null || item.lastDraftNo < 2)) {
        candidate = item;
      }
    });
    if (!candidate) { show(els['sw-w-resume-bar'], false); return; }
    writing.resumeTaskId = candidate.taskId;
    var prompt = candidate.prompt || mbT('Free writing');
    els['sw-w-resume-label'].textContent = prompt.length > 40
      ? prompt.slice(0, 40) + '…' : prompt;
    show(els['sw-w-resume-bar'], true);
  }

  function resume(taskId) {
    if (!urls.writingTask) { window.alert(mbT('Resume is unavailable')); return; }
    els['sw-w-status'].textContent = mbT('Loading');
    getJson(urls.writingTask + '?taskId=' + encodeURIComponent(taskId))
      .then(function (response) { applyTask(resultOf(response)); })
      .catch(function (err) {
        els['sw-w-status'].textContent = '';
        window.alert(err.message);
      });
  }

  /** 把任务原样铺回页面：题目与要求 + 最新草稿正文 + 该稿批改结果。 */
  function applyTask(detail) {
    var drafts = detail.drafts || [];
    var last = drafts.length ? drafts[drafts.length - 1] : null;
    writing.taskId = detail.taskId;
    writing.lastDraftNo = last ? last.draftNo : null;
    if (detail.mode) els['sw-w-mode'].value = String(detail.mode).toLowerCase();
    if (detail.cefrLevel) els['sw-w-cefr'].value = detail.cefrLevel;
    if (detail.bookTitle) els['sw-w-book'].value = detail.bookTitle;
    esc(els['sw-w-prompt'], detail.prompt || '');
    fillList(els['sw-w-requirements'], detail.requirements);
    // R172 之前出题不落 tips：旧任务这里是空的，属预期而非报错
    fillList(els['sw-w-tips'], detail.tips);
    show(els['sw-w-task'], !!(detail.prompt || (detail.requirements || []).length));
    els['sw-w-text'].value = last && last.text ? last.text : '';
    refreshSubmitButton();
    if (last && last.review) renderReview(last.review);
    else show(els['sw-w-review'], false);
    esc(els['sw-w-status'], last
      ? mbT('Resumed draft {{n}} — keep editing in the box above and submit again.')
          .replace('{{n}}', last.draftNo)
      : mbT('Task loaded — nothing written yet.'));
    els['sw-w-text'].focus();
  }

  els['sw-w-generate'].addEventListener('click', function () {
    busy(els['sw-w-generate'], true, mbT('Generating…'));
    postJson(urls.writingGenerate, {
      mode: els['sw-w-mode'].value,
      cefrLevel: els['sw-w-cefr'].value || null,
      prompt: els['sw-w-topic'].value || null,
      bookTitle: els['sw-w-book'].value || null,
    }).then(function (response) {
      var task = resultOf(response);
      writing.taskId = task.taskId;
      writing.lastDraftNo = null;      // 新任务：一稿未交
      esc(els['sw-w-prompt'], task.prompt);
      fillList(els['sw-w-requirements'], task.requirements);
      fillList(els['sw-w-tips'], task.tips);
      show(els['sw-w-task'], true);
      show(els['sw-w-review'], false);
      els['sw-w-status'].textContent = '';
      refreshSubmitButton();
    }).catch(function (err) { window.alert(err.message); })
      .finally(function () { busy(els['sw-w-generate'], false); });
  });

  els['sw-w-resume'].addEventListener('click', function () {
    if (writing.resumeTaskId) resume(writing.resumeTaskId);
  });

  els['sw-w-submit'].addEventListener('click', function () {
    if (!writing.taskId) { window.alert(mbT('Generate a task first')); return; }
    var btn = els['sw-w-submit'];
    busy(btn, true, mbT('Reviewing…'));
    postJson(draftEndpoint(), { taskId: writing.taskId, text: els['sw-w-text'].value })
      .then(function (response) {
        var review = resultOf(response);
        if (review.draftNo != null) writing.lastDraftNo = review.draftNo;
        renderReview(review);
        refreshSubmitButton();
        // 状态行跟着走：不然用户看到的还是「已恢复第 1 稿」，不知道刚交的是哪一稿
        esc(els['sw-w-status'], writing.lastDraftNo >= 2
          ? mbT('Both drafts finished — this task can only be reviewed now.')
          : mbT('Draft {{n}} reviewed. Revise it above and submit again.')
              .replace('{{n}}', review.draftNo == null ? '' : review.draftNo));
        loadWritingHistory();
      })
      .catch(function (err) { window.alert(err.message); })
      .finally(function () {
        busy(btn, false);
        // busy(false) 无条件解禁按钮，两稿完成后的 disabled 会被它冲掉（探针实测），
        // 所以解锁之后必须再按当前草稿状态刷一遍
        refreshSubmitButton();
      });
  });

  refreshSubmitButton();
  loadWritingHistory();
})();
