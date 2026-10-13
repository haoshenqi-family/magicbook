// 复述训练（4-3-2）子页面（R166 自 speaking_writing.js 迁出；训练契约属 R152/B1，
// 可说可打的语音输入 R155）。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, clear = MB.clear, esc = MB.esc,
      busy = MB.busy, postJson = MB.postJson, resultOf = MB.resultOf;
  var urls = window.learningUrls || {};

  var els = {};
  ['sw-r-paragraph', 'sw-r-book', 'sw-r-chapter', 'sw-r-minutes', 'sw-r-start',
   'sw-r-round-panel', 'sw-r-source', 'sw-r-round-label', 'sw-r-timer',
   'sw-r-transcript', 'sw-r-submit', 'sw-r-metrics', 'sw-r-finish',
   'sw-r-summary-panel', 'sw-r-summary', 'sw-r-improvement', 'sw-r-advice',
   'sw-r-rounds', 'sw-r-mic', 'sw-r-mic-device',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-r-start']) return;

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

  function clock(seconds) {
    return Math.floor(seconds / 60) + ':' + ('0' + (seconds % 60)).slice(-2);
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
      esc(els['sw-r-timer'], mbT('Time left: {{t}}').replace('{{t}}', clock(left)));
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

  window.MBLearningVoice.attach({
    micBtn: els['sw-r-mic'],
    statusEl: els['sw-r-metrics'],   // 与 R155 原形态一致：录音计时直接写在指标位
    deviceSelect: els['sw-r-mic-device'],
    onText: function (text) { els['sw-r-transcript'].value = text; },
  });
})();
