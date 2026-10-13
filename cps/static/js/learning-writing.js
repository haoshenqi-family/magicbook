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
   'sw-w-sentences', 'sw-w-upgrades', 'sw-w-revise-text', 'sw-w-revise',
   'sw-w-history-panel', 'sw-w-history',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-w-generate']) return;

  var writing = { taskId: null };

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
    if (review.draftNo != null) {
      // 二稿起清空修订框：让用户重写而不是把上一稿原样再交一次（进步确认就没意义了）
      els['sw-w-revise-text'].value = review.draftNo >= 2 ? '' : els['sw-w-text'].value;
    }
  }

  function loadWritingHistory() {
    getJson(urls.writingHistory).then(function (response) {
      var items = resultOf(response) || [];
      var panel = els['sw-w-history-panel'];
      if (!items.length) { show(panel, false); return; }
      var list = els['sw-w-history'];
      clear(list);
      items.forEach(function (task) {
        var line = li((task.prompt || mbT('Free writing')) + ' · ' +
          (task.submissions || []).map(function (sub) {
            return mbT('Draft') + ' ' + sub.draftNo;
          }).join(' · '));
        list.appendChild(line);
      });
      show(panel, true);
    }).catch(function () { show(els['sw-w-history-panel'], false); });
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
      esc(els['sw-w-prompt'], task.prompt);
      clear(els['sw-w-requirements']);
      (task.requirements || []).forEach(function (line) {
        els['sw-w-requirements'].appendChild(li(line));
      });
      clear(els['sw-w-tips']);
      (task.tips || []).forEach(function (line) {
        els['sw-w-tips'].appendChild(li(line));
      });
      show(els['sw-w-task'], true);
      show(els['sw-w-review'], false);
    }).catch(function (err) { window.alert(err.message); })
      .finally(function () { busy(els['sw-w-generate'], false); });
  });

  function submitDraft(url, btn, textarea) {
    if (!writing.taskId) { window.alert(mbT('Generate a task first')); return; }
    busy(btn, true, mbT('Reviewing…'));
    postJson(url, { taskId: writing.taskId, text: textarea.value })
      .then(function (response) {
        renderReview(resultOf(response));
        loadWritingHistory();
      })
      .catch(function (err) { window.alert(err.message); })
      .finally(function () { busy(btn, false); });
  }

  els['sw-w-submit'].addEventListener('click', function () {
    submitDraft(urls.writingSubmit, els['sw-w-submit'], els['sw-w-text']);
  });
  els['sw-w-revise'].addEventListener('click', function () {
    submitDraft(urls.writingRevise, els['sw-w-revise'], els['sw-w-revise-text']);
  });

  loadWritingHistory();
})();
