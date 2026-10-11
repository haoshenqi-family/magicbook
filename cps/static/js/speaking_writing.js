// 说与写页前端逻辑（R152 / B1 输出训练，moon-well R121 后端）。
//
// Why 独立文件：三个面板（写作工坊 / 口语陪练 / 复述训练）各有自己的小状态机，
// 合计超过 500 行，内联会把模板翻倍（learning.js 同款取舍）。
//
// 文案通道：mbT 由 i18n_seed.html 提供（layout 先载入），词条必须进种子且 po 有
// zh 译文（test_i18n_seed_contract 锁定）；本文件已加入其 JS_FILES 清单。
// 模板静态文案走 Jinja _()，运行时动态文案走 mbT——两层都进 po。
//
// 契约（moon-well learning B1，LLD us2-b1-output-lld）：统一 Result 信封
// {success, result, message}；代理已做域校验，本文件按 success/message 分支，
// LLM 端点慢（批改/出题/报告 10-40s），按钮一律加在途锁防连击。
(function () {
  'use strict';

  function mbT(msgid) {
    return (window.MB_I18N && window.MB_I18N[msgid]) || msgid;
  }

  var urls = window.speakingWritingUrls || {};
  var $ = function (id) { return document.getElementById(id); };

  var els = {};
  ['sw-csrf', 'sw-w-mode', 'sw-w-cefr', 'sw-w-topic', 'sw-w-book', 'sw-w-generate',
   'sw-w-task', 'sw-w-prompt', 'sw-w-requirements', 'sw-w-tips',
   'sw-w-text', 'sw-w-submit', 'sw-w-status',
   'sw-w-review', 'sw-w-progress', 'sw-w-overall', 'sw-w-scores',
   'sw-w-sentences', 'sw-w-upgrades', 'sw-w-revise-text', 'sw-w-revise',
   'sw-w-history-panel', 'sw-w-history',
   'sw-s-scenario', 'sw-s-style', 'sw-s-book', 'sw-s-start', 'sw-s-setup',
   'sw-s-chat-panel', 'sw-s-chat', 'sw-s-input', 'sw-s-send', 'sw-s-report',
   'sw-s-report-panel', 'sw-s-summary', 'sw-s-progress-line',
   'sw-s-vocab', 'sw-s-corrections', 'sw-s-history-panel', 'sw-s-history',
   'sw-r-paragraph', 'sw-r-book', 'sw-r-chapter', 'sw-r-minutes', 'sw-r-start',
   'sw-r-round-panel', 'sw-r-source', 'sw-r-round-label', 'sw-r-timer',
   'sw-r-transcript', 'sw-r-submit', 'sw-r-metrics', 'sw-r-finish',
   'sw-r-summary-panel', 'sw-r-summary', 'sw-r-improvement', 'sw-r-advice',
   'sw-r-rounds',
  ].forEach(function (id) { els[id] = $(id); });

  // ---------- 小工具 ----------

  function csrfToken() {
    return els['sw-csrf'] ? els['sw-csrf'].value : '';
  }

  function httpJson(url, options) {
    return fetch(url, options).then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { /* 非 JSON 按失败处理 */ }
        return { ok: response.ok, status: response.status, data: data };
      });
    });
  }

  function postJson(url, body) {
    return httpJson(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(body || {}),
    });
  }

  function getJson(url) {
    return httpJson(url, { credentials: 'same-origin' });
  }

  function resultOf(response) {
    // Result 信封：success=false 时 message 是上游业务文案（zh），直接展示
    if (response.data && response.data.success) return response.data.result;
    throw new Error((response.data && response.data.message) || mbT('Something went wrong'));
  }

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

  function esc(node, text) {
    node.textContent = text == null ? '' : String(text);
  }

  // ---------- 写作工坊 ----------

  var writing = { taskId: null };

  function scoreRow(labelZh, value) {
    var wrap = document.createElement('div');
    wrap.className = 'sw-score';
    var b = document.createElement('b');
    b.textContent = value == null ? '–' : value;
    var span = document.createElement('span');
    span.textContent = labelZh;
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

  function show(el, visible) {
    if (!el) return;
    el.hidden = !visible;
    el.style.display = visible ? '' : 'none';
  }

  function bindWriting() {
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
  }

  // ---------- AI 口语陪练 ----------

  var speaking = { sessionId: null };

  function chatBubble(role, text) {
    var wrap = document.createElement('div');
    wrap.className = 'sw-msg ' + (role === 'coach' ? 'sw-msg-coach' : 'sw-msg-user');
    var who = document.createElement('strong');
    who.textContent = role === 'coach' ? mbT('Coach') : mbT('You');
    wrap.appendChild(who);
    var body = document.createElement('div');
    esc(body, text);
    wrap.appendChild(body);
    return wrap;
  }

  function feedbackBlock(feedback) {
    var box = document.createElement('div');
    box.className = 'sw-feedback';
    if (feedback.encourage) {
      var line = document.createElement('div');
      esc(line, feedback.encourage);
      box.appendChild(line);
    }
    (feedback.errors || []).forEach(function (item) {
      var fix = document.createElement('div');
      fix.className = 'sw-correction';
      fix.textContent = '✎ ' + (item.original || '') + ' → ' + (item.corrected || '') +
        (item.note ? '（' + item.note + '）' : '');
      box.appendChild(fix);
    });
    if (feedback.better) {
      var better = document.createElement('div');
      better.className = 'sw-correction';
      better.textContent = '✦ ' + mbT('Better phrasing') + '：' + feedback.better;
      box.appendChild(better);
    }
    return box;
  }

  function loadSpeakingHistory() {
    getJson(urls.speakingHistory).then(function (response) {
      var items = resultOf(response) || [];
      var panel = els['sw-s-history-panel'];
      if (!items.length) { show(panel, false); return; }
      var list = els['sw-s-history'];
      clear(list);
      items.forEach(function (session) {
        var line = li((session.scenarioLabel || session.scenario || '') +
          ' · ' + (session.roundCount || 0) + ' ' + mbT('rounds') + ' · ' +
          (session.createdAt || ''));
        line.style.cursor = 'pointer';
        line.addEventListener('click', function () { replaySession(session.sessionId); });
        list.appendChild(line);
      });
      show(panel, true);
    }).catch(function () { show(els['sw-s-history-panel'], false); });
  }

  function replaySession(sessionId) {
    postJson(urls.speakingMessages, { sessionId: sessionId }).then(function (response) {
      var messages = resultOf(response) || [];
      speaking.sessionId = sessionId;
      show(els['sw-s-setup'], false);
      show(els['sw-s-chat-panel'], true);
      show(els['sw-s-report-panel'], false);
      var chat = els['sw-s-chat'];
      clear(chat);
      messages.forEach(function (message) {
        chat.appendChild(chatBubble(message.role === 'coach' ? 'coach' : 'user',
          message.content));
        if (message.role === 'coach' && message.feedback) {
          chat.appendChild(feedbackBlock(message.feedback));
        }
      });
      chat.scrollTop = chat.scrollHeight;
    }).catch(function (err) { window.alert(err.message); });
  }

  function bindSpeaking() {
    els['sw-s-start'].addEventListener('click', function () {
      busy(els['sw-s-start'], true, mbT('Loading'));
      postJson(urls.speakingSession, {
        scenario: els['sw-s-scenario'].value,
        coachStyle: els['sw-s-style'].value,
        bookTitle: els['sw-s-book'].value || null,
      }).then(function (response) {
        var start = resultOf(response);
        speaking.sessionId = start.sessionId;
        show(els['sw-s-setup'], false);
        show(els['sw-s-chat-panel'], true);
        show(els['sw-s-report-panel'], false);
        var chat = els['sw-s-chat'];
        clear(chat);
        chat.appendChild(chatBubble('coach', start.greeting));
      }).catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-s-start'], false); });
    });

    els['sw-s-send'].addEventListener('click', function () {
      var text = els['sw-s-input'].value.trim();
      if (!text || !speaking.sessionId) return;
      var chat = els['sw-s-chat'];
      chat.appendChild(chatBubble('user', text));
      els['sw-s-input'].value = '';
      chat.scrollTop = chat.scrollHeight;
      busy(els['sw-s-send'], true, mbT('Thinking…'));
      postJson(urls.speakingMessage, { sessionId: speaking.sessionId, text: text })
        .then(function (response) {
          var turn = resultOf(response);
          chat.appendChild(chatBubble('coach', turn.reply));
          if (turn.feedback) chat.appendChild(feedbackBlock(turn.feedback));
          chat.scrollTop = chat.scrollHeight;
        })
        .catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-s-send'], false); });
    });
    els['sw-s-input'].addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        els['sw-s-send'].click();
      }
    });

    els['sw-s-report'].addEventListener('click', function () {
      if (!speaking.sessionId) return;
      busy(els['sw-s-report'], true, mbT('Reviewing…'));
      postJson(urls.speakingReport, { sessionId: speaking.sessionId })
        .then(function (response) {
          var report = resultOf(response);
          esc(els['sw-s-summary'], report.summary);
          esc(els['sw-s-progress-line'], report.progress);
          clear(els['sw-s-vocab']);
          (report.activeVocab || []).forEach(function (word) {
            els['sw-s-vocab'].appendChild(li(word));
          });
          clear(els['sw-s-corrections']);
          (report.corrections || []).forEach(function (item) {
            els['sw-s-corrections'].appendChild(li(
              (item.original || '') + ' → ' + (item.corrected || '') +
              (item.note ? '（' + item.note + '）' : '')));
          });
          show(els['sw-s-report-panel'], true);
          speaking.sessionId = null;
          show(els['sw-s-setup'], true);
          loadSpeakingHistory();
        })
        .catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-s-report'], false); });
    });
  }

  // ---------- 复述训练（4-3-2）----------

  var retell = {
    retellId: null,
    round: 0,             // 当前第几轮（1 起）
    totalRounds: 0,
    minutes: [],
    startedAt: 0,
    timerId: null,
  };

  function stopTimer() {
    if (retell.timerId) { clearInterval(retell.timerId); retell.timerId = null; }
  }

  function startRound(round) {
    retell.round = round;
    var minutes = retell.minutes[round - 1] || 4;
    esc(els['sw-r-round-label'], mbT('Round {{n}} of {{m}}')
      .replace('{{n}}', round).replace('{{m}}', retell.totalRounds));
    els['sw-r-transcript'].value = '';
    show(els['sw-r-finish'], false);
    els['sw-r-metrics'].textContent = '';
    var deadline = Date.now() + minutes * 60000;
    stopTimer();
    retell.startedAt = Date.now();
    retell.timerId = setInterval(function () {
      var left = Math.max(0, Math.round((deadline - Date.now()) / 1000));
      esc(els['sw-r-timer'], mbT('Time left: {{t}}').replace('{{t}}',
        Math.floor(left / 60) + ':' + ('0' + (left % 60)).slice(-2)));
      if (left <= 0) stopTimer();
    }, 500);
    esc(els['sw-r-timer'], mbT('Time left: {{t}}').replace('{{t}}', minutes + ':00'));
  }

  function showRoundResult(round) {
    els['sw-r-metrics'].textContent = mbT('Round {{n}} of {{m}}')
        .replace('{{n}}', round.round).replace('{{m}}', retell.totalRounds) +
      ' · ' + round.wordCount + ' ' + mbT('words') +
      ' · WPM ' + round.wpm +
      ' · ' + mbT('Fillers') + ' ' + round.fillerCount +
      ' · ' + mbT('Lexical diversity') + ' ' + round.ttr;
  }

  function renderRetellSummary(summary) {
    show(els['sw-r-round-panel'], false);
    show(els['sw-r-summary-panel'], true);
    esc(els['sw-r-summary'], summary.summary);
    esc(els['sw-r-improvement'], summary.improvement);
    esc(els['sw-r-advice'], summary.advice);
    var tbody = els['sw-r-rounds'];
    clear(tbody);
    (summary.rounds || []).forEach(function (round) {
      var row = document.createElement('tr');
      [round.round, round.wpm, round.fillerCount, round.ttr].forEach(function (value) {
        var td = document.createElement('td');
        td.textContent = value;
        row.appendChild(td);
      });
      tbody.appendChild(row);
    });
  }

  function bindRetell() {
    els['sw-r-start'].addEventListener('click', function () {
      var paragraph = els['sw-r-paragraph'].value.trim();
      if (!paragraph) { window.alert(mbT('Paste an English paragraph you have read')); return; }
      var minutes = els['sw-r-minutes'].value.split(',')
        .map(function (piece) { return parseInt(piece, 10); })
        .filter(function (num) { return num > 0; });
      busy(els['sw-r-start'], true, mbT('Loading'));
      postJson(urls.retellStart, {
        paragraphText: paragraph,
        bookId: els['sw-r-book'].value || null,
        chapter: els['sw-r-chapter'].value || null,
        minutesPerRound: minutes.length ? minutes : null,
      }).then(function (response) {
        var started = resultOf(response);
        retell.retellId = started.retellId;
        retell.minutes = started.minutesPerRound || minutes || [4, 3, 2];
        retell.totalRounds = retell.minutes.length;
        esc(els['sw-r-source'], started.sourcePreview);
        show(els['sw-r-round-panel'], true);
        show(els['sw-r-summary-panel'], false);
        startRound(1);
      }).catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-r-start'], false); });
    });

    els['sw-r-submit'].addEventListener('click', function () {
      if (!retell.retellId) return;
      var transcript = els['sw-r-transcript'].value.trim();
      if (!transcript) { window.alert(mbT('Type what you said first')); return; }
      stopTimer();
      busy(els['sw-r-submit'], true, mbT('Reviewing…'));
      postJson(urls.retellRound, {
        retellId: retell.retellId,
        round: retell.round,
        durationMs: Date.now() - retell.startedAt,
        transcript: transcript,
      }).then(function (response) {
        var round = resultOf(response);
        showRoundResult(round);
        if (retell.round >= retell.totalRounds) {
          show(els['sw-r-finish'], true);
        } else {
          startRound(retell.round + 1);
        }
      }).catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-r-submit'], false); });
    });

    els['sw-r-finish'].addEventListener('click', function () {
      if (!retell.retellId) return;
      busy(els['sw-r-finish'], true, mbT('Reviewing…'));
      postJson(urls.retellFinish, { retellId: retell.retellId })
        .then(function (response) {
          renderRetellSummary(resultOf(response));
          retell.retellId = null;
        })
        .catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-r-finish'], false); });
    });
  }

  // ---------- 启动 ----------

  bindWriting();
  bindSpeaking();
  bindRetell();
  loadWritingHistory();
  loadSpeakingHistory();
})();
