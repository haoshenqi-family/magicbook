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
   'sw-s-tts',
   'sw-rr-material', 'sw-rr-load', 'sw-rr-recommend', 'sw-rr-paragraphs',
   'sw-rr-panel', 'sw-rr-source', 'sw-rr-round-label', 'sw-rr-timer',
   'sw-rr-start', 'sw-rr-stop', 'sw-rr-metrics', 'sw-rr-trend',
   'sw-d-material', 'sw-d-load', 'sw-d-paragraphs',
   'sw-d-panel', 'sw-d-play', 'sw-d-audio-status', 'sw-d-audio',
   'sw-d-answer', 'sw-d-add-unknown', 'sw-d-check', 'sw-d-result',
   'sw-d-accuracy', 'sw-d-tokens', 'sw-d-missing', 'sw-d-extra',
   'sw-s-mic', 'sw-r-mic', 'sw-s-audio-status',
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
        speakIfEnabled(start.greeting);
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
          speakIfEnabled(turn.reply);
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

  // ---------- coach 回复朗读（R153）：复用阅读器 TTS 代理（AI 临时语音档） ----------

  var ttsAudio = null;

  function speakIfEnabled(text) {
    if (!text) return;
    var toggle = els['sw-s-tts'];
    if (!toggle || !toggle.checked) return;
    speakText(text);
  }

  function speakText(text) {
    try { if (ttsAudio) { ttsAudio.pause(); } } catch (e) { /* 上一段可能已释放 */ }
    fetch(urls.readingTts, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify({ text: String(text).slice(0, 1800) }),
    }).then(function (response) {
      if (!response.ok) throw new Error('tts ' + response.status);
      return response.blob();
    }).then(function (blob) {
      ttsAudio = new Audio(URL.createObjectURL(blob));
      return ttsAudio.play();
    }).catch(function () { /* 朗读失败静默：不打断对话与训练主链路 */ });
  }

  // ---------- 计时重读（RRR，B2c 流利度） ----------

  var rrr = { bookId: null, order: null, round: 0, startedAt: 0, timerId: null };

  function loadMaterials(select, source, done) {
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

  function stopRrrTimer() {
    if (rrr.timerId) { clearInterval(rrr.timerId); rrr.timerId = null; }
  }

  function rrrLabel() {
    return mbT('Round {{n}} of {{m}}')
      .replace('{{n}}', Math.min(rrr.round, 3)).replace('{{m}}', 3);
  }

  function loadRrrTrend() {
    var query = '?bookId=' + encodeURIComponent(rrr.bookId) +
      '&order=' + encodeURIComponent(rrr.order);
    getJson(urls.rrrTrend + query).then(function (response) {
      var trend = resultOf(response);
      var box = els['sw-rr-trend'];
      clear(box);
      if (!trend.rounds || !trend.rounds.length) { box.hidden = true; return; }
      var head = document.createElement('p');
      head.textContent = mbT('First WPM') + ' ' + (trend.firstWpm == null ? '–' : trend.firstWpm) +
        ' · ' + mbT('Best WPM') + ' ' + (trend.bestWpm == null ? '–' : trend.bestWpm) +
        (trend.improvementPct == null ? '' : ' · +' + trend.improvementPct + '%');
      box.appendChild(head);
      trend.rounds.forEach(function (round) {
        box.appendChild(li(mbT('Round {{n}} of {{m}}')
          .replace('{{n}}', round.round).replace('{{m}}', 3) +
          ' · ' + round.wpm + ' WPM · ' + round.wordCount + ' ' + mbT('words')));
      });
      box.hidden = false;
    }).catch(function () { /* 趋势失败不打断训练 */ });
  }

  function pickRrrParagraph(paragraph) {
    rrr.bookId = els['sw-rr-material'].value;
    rrr.order = paragraph.order;
    rrr.round = 1;
    esc(els['sw-rr-source'], paragraph.text);
    show(els['sw-rr-panel'], true);
    els['sw-rr-round-label'].textContent = rrrLabel();
    els['sw-rr-metrics'].textContent = '';
    els['sw-rr-trend'].hidden = true;
    els['sw-rr-stop'].hidden = true;
    els['sw-rr-start'].hidden = false;
  }

  function bindRrr() {
    els['sw-rr-load'].addEventListener('click', function () {
      var select = els['sw-rr-material'];
      if (!select.value) { window.alert(mbT('No materials available')); return; }
      postJson(urls.listeningParagraphs, { bookId: select.value })
        .then(function (response) {
          var paragraphs = resultOf(response) || [];
          var list = els['sw-rr-paragraphs'];
          clear(list);
          paragraphs.slice(0, 30).forEach(function (paragraph) {
            list.appendChild(paragraphLine(paragraph, pickRrrParagraph));
          });
        }).catch(function (err) { window.alert(err.message); });
    });

    els['sw-rr-material'].addEventListener('focus', function () {
      if (!els['sw-rr-material'].options.length) loadMaterials(els['sw-rr-material'], 'tts');
    });
    loadMaterials(els['sw-rr-material'], 'tts');

    els['sw-rr-start'].addEventListener('click', function () {
      if (!rrr.bookId) return;
      rrr.startedAt = Date.now();
      els['sw-rr-start'].hidden = true;
      els['sw-rr-stop'].hidden = false;
      stopRrrTimer();
      rrr.timerId = setInterval(function () {
        var seconds = Math.round((Date.now() - rrr.startedAt) / 1000);
        els['sw-rr-timer'].textContent =
          mbT('Time left: {{t}}').replace('{{t}}',
            Math.floor(seconds / 60) + ':' + ('0' + (seconds % 60)).slice(-2));
      }, 500);
    });

    els['sw-rr-stop'].addEventListener('click', function () {
      if (!rrr.bookId || rrr.timerId == null) return;
      stopRrrTimer();
      busy(els['sw-rr-stop'], true, mbT('Reviewing…'));
      postJson(urls.rrrRecord, {
        bookId: rrr.bookId,
        order: rrr.order,
        round: rrr.round,
        durationMs: Date.now() - rrr.startedAt,
        mode: 'ALOUD',
      }).then(function (response) {
        var record = resultOf(response);
        els['sw-rr-metrics'].textContent = rrrLabel() + ' · ' +
          record.wpm + ' WPM · ' + record.wordCount + ' ' + mbT('words');
        rrr.round += 1;
        els['sw-rr-stop'].hidden = true;
        els['sw-rr-start'].hidden = rrr.round > 3;
        els['sw-rr-round-label'].textContent = rrrLabel();
        loadRrrTrend();
      }).catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-rr-stop'], false); });
    });

    els['sw-rr-recommend'].addEventListener('click', function () {
      getJson(urls.rrrRecommend).then(function (response) {
        var items = resultOf(response) || [];
        var list = els['sw-rr-paragraphs'];
        clear(list);
        if (!items.length) {
          list.appendChild(li(mbT('No due words right now — pick any paragraph')));
          return;
        }
        items.forEach(function (item) {
          var line = li((item.title || '') + ' · #' + item.order +
            (item.author ? ' · ' + item.author : ''));
          line.style.cursor = 'pointer';
          line.addEventListener('click', function () {
            rrr.bookId = item.bookId;
            rrr.order = item.order;
            rrr.round = 1;
            getJson(urls.rrrTrend + '?bookId=' + encodeURIComponent(item.bookId) +
                    '&order=' + encodeURIComponent(item.order))
              .then(function (trendResponse) {
                var trend = resultOf(trendResponse);
                esc(els['sw-rr-source'], trend.text);
                show(els['sw-rr-panel'], true);
                els['sw-rr-round-label'].textContent = rrrLabel();
                els['sw-rr-metrics'].textContent = '';
              }).catch(function (err) { window.alert(err.message); });
          });
          list.appendChild(line);
        });
      }).catch(function (err) { window.alert(err.message); });
    });
  }

  // ---------- 听写（B2a 词汇股） ----------

  var dictation = { bookId: null, order: null, paragraph: null, objectUrl: null };

  function stopDictationAudio() {
    var audio = els['sw-d-audio'];
    try { audio.pause(); } catch (e) { /* 未播放时忽略 */ }
    if (dictation.objectUrl) {
      URL.revokeObjectURL(dictation.objectUrl);
      dictation.objectUrl = null;
    }
  }

  function playDictationAudio() {
    var paragraph = dictation.paragraph;
    if (!paragraph) return;
    var audio = els['sw-d-audio'];
    stopDictationAudio();
    var endMs = paragraph.audioEndMs;
    var startMs = paragraph.audioStartMs;
    function clip() {
      if (endMs != null && audio.currentTime * 1000 >= endMs) audio.pause();
    }
    if (paragraph.audioUrl) {
      audio.src = paragraph.audioUrl;
      audio.ontimeupdate = clip;
      audio.hidden = false;
      audio.currentTime = (startMs || 0) / 1000;
      audio.play().catch(function () { /* 自动播放被拦时用户手动点 */ });
      return;
    }
    esc(els['sw-d-audio-status'], mbT('Preparing audio…'));
    fetch(urls.readingTts, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify({ text: String(paragraph.text || '').slice(0, 1800) }),
    }).then(function (response) {
      if (!response.ok) throw new Error('tts ' + response.status);
      return response.blob();
    }).then(function (blob) {
      dictation.objectUrl = URL.createObjectURL(blob);
      audio.src = dictation.objectUrl;
      audio.ontimeupdate = null;
      audio.hidden = false;
      esc(els['sw-d-audio-status'], '');
      return audio.play();
    }).catch(function (err) {
      esc(els['sw-d-audio-status'], mbT('Audio unavailable for this paragraph'));
    });
  }

  function renderDictationResult(result) {
    show(els['sw-d-result'], true);
    els['sw-d-accuracy'].textContent = mbT('Accuracy') + ' ' + result.accuracyPct + '%' +
      ' (' + result.correctCount + '/' + result.wordCount + ')';
    var tokens = els['sw-d-tokens'];
    clear(tokens);
    (result.tokens || []).forEach(function (token) {
      var span = document.createElement('span');
      if (token.status === 'MATCH') {
        span.className = 'sw-tok-ok';
        span.textContent = token.expected + ' ';
      } else if (token.status === 'WRONG') {
        span.className = 'sw-tok-wrong';
        span.textContent = token.actual + ' ';
        span.title = token.expected;
      } else if (token.status === 'MISSING') {
        span.className = 'sw-tok-missing';
        span.textContent = '[' + token.expected + '] ';
      } else { // EXTRA：多打的不在原文里，灰调小字
        span.style.color = '#999';
        span.textContent = '(' + token.actual + ') ';
      }
      tokens.appendChild(span);
    });
    els['sw-d-missing'].textContent =
      (result.missing && result.missing.length ? mbT('Missing') + ': ' + result.missing.join(', ') : '');
    els['sw-d-extra'].textContent =
      (result.extra && result.extra.length ? mbT('Extra') + ': ' + result.extra.join(', ') : '');
    if (result.addedWords && result.addedWords.length) {
      els['sw-d-extra'].textContent +=
        ' · ' + mbT('Added to review queue') + ': ' + result.addedWords.length;
    }
  }

  function pickDictationParagraph(paragraph) {
    dictation.bookId = els['sw-d-material'].value;
    dictation.order = paragraph.order;
    dictation.paragraph = paragraph;
    show(els['sw-d-panel'], true);
    els['sw-d-answer'].value = '';
    show(els['sw-d-result'], false);
    esc(els['sw-d-audio-status'], '');
  }

  function bindDictation() {
    els['sw-d-load'].addEventListener('click', function () {
      var select = els['sw-d-material'];
      if (!select.value) { window.alert(mbT('No materials available')); return; }
      postJson(urls.listeningParagraphs, { bookId: select.value })
        .then(function (response) {
          var paragraphs = resultOf(response) || [];
          var list = els['sw-d-paragraphs'];
          clear(list);
          paragraphs.slice(0, 30).forEach(function (paragraph) {
            list.appendChild(paragraphLine(paragraph, pickDictationParagraph));
          });
        }).catch(function (err) { window.alert(err.message); });
    });

    els['sw-d-material'].addEventListener('focus', function () {
      if (!els['sw-d-material'].options.length) loadMaterials(els['sw-d-material'], 'ted');
    });
    loadMaterials(els['sw-d-material'], 'ted');

    els['sw-d-play'].addEventListener('click', playDictationAudio);

    els['sw-d-check'].addEventListener('click', function () {
      if (!dictation.bookId) return;
      var answer = els['sw-d-answer'].value.trim();
      if (!answer) { window.alert(mbT('Type what you said first')); return; }
      busy(els['sw-d-check'], true, mbT('Reviewing…'));
      postJson(urls.dictationCheck, {
        bookId: dictation.bookId,
        order: dictation.order,
        answer: answer,
        addUnknown: els['sw-d-add-unknown'].checked,
      }).then(function (response) {
        renderDictationResult(resultOf(response));
      }).catch(function (err) { window.alert(err.message); })
        .finally(function () { busy(els['sw-d-check'], false); });
    });
  }

  // ---------- 语音输入（R155）：WebAudio 采集端直接编 16k wav ----------
  //
  // Why 不用 MediaRecorder：其产物 webm/opus 在 SiliconFlow 转写端兼容性存疑，
  // 且浏览器间编码不可控；WebAudio 拿原始 PCM 后在采集端编码 16k 单声道 wav
  //（≈32KB/s，3 分钟 <6MB），上游转写链路只见标准音频。ScriptProcessor 虽已
  // 被标记过时，但兼容性最稳，个人工具量级足够。

  function encodeWav(chunks, inputRate) {
    var targetRate = 16000;
    var count = 0;
    chunks.forEach(function (chunk) { count += chunk.length; });
    // 先合并成单条 PCM（逐块索引在 3 分钟音频上会是百万次链表遍历）
    var merged = new Float32Array(count);
    var offset = 0;
    chunks.forEach(function (chunk) {
      merged.set(chunk, offset);
      offset += chunk.length;
    });
    var outLength = Math.max(1, Math.floor(count * targetRate / inputRate));
    var samples = new Int16Array(outLength);
    for (var i = 0; i < outLength; i++) {
      var pos = i * inputRate / targetRate;
      var index = Math.floor(pos);
      var frac = pos - index;
      var a = merged[Math.min(index, count - 1)];
      var b = merged[Math.min(index + 1, count - 1)];
      var sample = a + (b - a) * frac;
      samples[i] = Math.max(-32768, Math.min(32767, Math.round(sample * 32767)));
    }
    var buffer = new ArrayBuffer(44 + samples.length * 2);
    var view = new DataView(buffer);
    function str(offset, value) {
      for (var i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i));
    }
    str(0, 'RIFF'); view.setUint32(4, 36 + samples.length * 2, true); str(8, 'WAVE');
    str(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); view.setUint32(24, targetRate, true);
    view.setUint32(28, targetRate * 2, true); view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    str(36, 'data'); view.setUint32(40, samples.length * 2, true);
    new Int16Array(buffer, 44).set(samples);
    return new Blob([buffer], { type: 'audio/wav' });
  }

  var recorder = { ctx: null, stream: null, source: null, processor: null,
                   chunks: [], startedAt: 0, timerId: null };

  function recorderStart(onTick) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return Promise.reject(new Error(mbT('Microphone unavailable')));
    }
    return navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 } })
      .then(function (stream) {
        var AudioCtx = window.AudioContext || window.webkitAudioContext;
        recorder.ctx = new AudioCtx();
        recorder.stream = stream;
        recorder.source = recorder.ctx.createMediaStreamSource(stream);
        recorder.processor = recorder.ctx.createScriptProcessor(4096, 1, 1);
        recorder.chunks = [];
        recorder.startedAt = Date.now();
        recorder.processor.onaudioprocess = function (event) {
          recorder.chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
        };
        recorder.source.connect(recorder.processor);
        recorder.processor.connect(recorder.ctx.destination);
        recorder.timerId = setInterval(function () {
          var seconds = Math.round((Date.now() - recorder.startedAt) / 1000);
          onTick(mbT('Recording {{t}}').replace('{{t}}',
            Math.floor(seconds / 60) + ':' + ('0' + (seconds % 60)).slice(-2)));
        }, 500);
      });
  }

  function recorderStop() {
    if (recorder.timerId) { clearInterval(recorder.timerId); recorder.timerId = null; }
    try {
      if (recorder.processor) recorder.processor.onaudioprocess = null;
      if (recorder.processor) recorder.processor.disconnect();
      if (recorder.source) recorder.source.disconnect();
      if (recorder.stream) recorder.stream.getTracks().forEach(function (t) { t.stop(); });
    } catch (e) { /* 已停止时忽略 */ }
    var rate = recorder.ctx ? recorder.ctx.sampleRate : 48000;
    var chunks = recorder.chunks.slice();
    if (recorder.ctx && recorder.ctx.close) recorder.ctx.close();
    recorder.ctx = null; recorder.processor = null; recorder.source = null;
    recorder.stream = null;
    if (!chunks.length) return Promise.reject(new Error(mbT('Recording too short')));
    return Promise.resolve(encodeWav(chunks, rate));
  }

  function transcribeRecording() {
    var seconds = Math.round((Date.now() - recorder.startedAt) / 1000);
    if (seconds < 1) return Promise.reject(new Error(mbT('Recording too short')));
    return recorderStop().then(function (blob) {
      var form = new FormData();
      form.append('file', blob, 'recording.wav');
      return fetch(urls.asrTranscribe, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrfToken() },
        body: form,
      }).then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok || !data || data.success !== true) {
            throw new Error((data && data.message) || mbT('Something went wrong'));
          }
          var text = String(data.result && data.result.text || '').trim();
          if (!text) throw new Error(mbT('No speech detected'));
          return text;
        });
      });
    });
  }

  var MIC_IDLE_LABEL = 'Voice input';

  function micLabel(btn, text) {
    var label = btn.querySelector('.sw-mic-label');
    if (label) label.textContent = text;
  }

  // 状态全在按钮上自更新：语音输入 → 录音中 mm:ss（红底，再点停止）→ 转写中…
  // 图标字体缺失时按钮仍有文字，不再是「空白按钮」。
  function micButton(btn, statusNode, onText) {
    btn.addEventListener('click', function () {
      if (!btn.classList.contains('sw-rec')) {
        btn.classList.add('sw-rec');
        micLabel(btn, mbT('Recording {{t}}').replace('{{t}}', '0:00')
          + ' · ' + mbT('click to stop'));
        recorderStart(function (label) {
          statusNode.textContent = label;
          micLabel(btn, label + ' · ' + mbT('click to stop'));
        }).catch(function (err) {
          btn.classList.remove('sw-rec');
          statusNode.textContent = '';
          micLabel(btn, MIC_IDLE_LABEL);
          window.alert(err.message);
        });
        return;
      }
      btn.classList.remove('sw-rec');
      btn.disabled = true;
      micLabel(btn, mbT('Transcribing…'));
      statusNode.textContent = '';
      // R158：同步段抛错也必须复原按钮——此前 statusNode 未注册时同步 TypeError
      // 让按钮永远停在「转写中…」且无任何提示
      try {
        transcribeRecording().then(function (text) {
          micLabel(btn, MIC_IDLE_LABEL);
          btn.disabled = false;
          onText(text);
        }).catch(function (err) {
          micLabel(btn, MIC_IDLE_LABEL);
          btn.disabled = false;
          window.alert(err.message);
        });
      } catch (err) {
        micLabel(btn, MIC_IDLE_LABEL);
        btn.disabled = false;
        window.alert(err.message);
      }
    });
  }

  micButton(els['sw-s-mic'], els['sw-s-audio-status'],
    function (text) {
      els['sw-s-input'].value = els['sw-s-input'].value
        ? els['sw-s-input'].value + ' ' + text : text;
      els['sw-s-input'].focus();
    });
  micButton(els['sw-r-mic'], els['sw-r-metrics'],
    function (text) { els['sw-r-transcript'].value = text; });

  // ---------- 启动 ----------

  bindWriting();
  bindSpeaking();
  bindRetell();
  bindRrr();
  bindDictation();
  loadWritingHistory();
  loadSpeakingHistory();
})();
