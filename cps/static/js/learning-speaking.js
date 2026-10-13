// AI 口语陪练子页面（R166 自 speaking_writing.js 迁出；会话契约属 R152/B1，
// 语音输入 R155、教练回复朗读 R153）。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, clear = MB.clear, li = MB.li,
      esc = MB.esc, busy = MB.busy, getJson = MB.getJson, postJson = MB.postJson,
      resultOf = MB.resultOf;
  var urls = window.learningUrls || {};

  var els = {};
  ['sw-s-scenario', 'sw-s-style', 'sw-s-book', 'sw-s-start', 'sw-s-setup',
   'sw-s-chat-panel', 'sw-s-chat', 'sw-s-input', 'sw-s-send', 'sw-s-report',
   'sw-s-report-panel', 'sw-s-summary', 'sw-s-progress-line',
   'sw-s-vocab', 'sw-s-corrections', 'sw-s-history-panel', 'sw-s-history',
   'sw-s-tts', 'sw-s-mic', 'sw-s-audio-status', 'sw-s-mic-device',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-s-start']) return;

  var speaking = { sessionId: null };
  var ttsAudio = null;

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

  // ---------- 教练回复自动朗读（R153）：复用阅读器 TTS 代理（AI 临时语音档） ----------

  function speakText(text) {
    try { if (ttsAudio) { ttsAudio.pause(); } } catch (e) { /* 上一段可能已释放 */ }
    fetch(urls.readingTts, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': MB.csrfToken() },
      body: JSON.stringify({ text: String(text).slice(0, 1800) }),
    }).then(function (response) {
      if (!response.ok) throw new Error('tts ' + response.status);
      return response.blob();
    }).then(function (blob) {
      ttsAudio = new Audio(URL.createObjectURL(blob));
      return ttsAudio.play();
    }).catch(function () { /* 朗读失败静默：不打断对话与训练主链路 */ });
  }

  function speakIfEnabled(text) {
    if (!text) return;
    var toggle = els['sw-s-tts'];
    if (!toggle || !toggle.checked) return;
    speakText(text);
  }

  // ---------- 历史与回放 ----------

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

  // ---------- 会话 ----------

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

  window.MBLearningVoice.attach({
    micBtn: els['sw-s-mic'],
    statusEl: els['sw-s-audio-status'],
    deviceSelect: els['sw-s-mic-device'],
    onText: function (text) {
      els['sw-s-input'].value = els['sw-s-input'].value
        ? els['sw-s-input'].value + ' ' + text : text;
      els['sw-s-input'].focus();
    },
  });

  loadSpeakingHistory();
})();
