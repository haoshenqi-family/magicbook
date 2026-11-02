// 计时重读（RRR）子页面（R166 自 speaking_writing.js 迁出；流利度股契约属 R153/B2c）。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, clear = MB.clear, li = MB.li,
      esc = MB.esc, busy = MB.busy, getJson = MB.getJson, postJson = MB.postJson,
      resultOf = MB.resultOf, loadMaterials = MB.loadMaterials,
      paragraphLine = MB.paragraphLine;
  var urls = window.learningUrls || {};

  var els = {};
  ['sw-rr-material', 'sw-rr-load', 'sw-rr-recommend', 'sw-rr-paragraphs',
   'sw-rr-panel', 'sw-rr-source', 'sw-rr-round-label', 'sw-rr-timer',
   'sw-rr-start', 'sw-rr-stop', 'sw-rr-metrics', 'sw-rr-trend',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-rr-load']) return;

  var rrr = { bookId: null, order: null, round: 0, startedAt: 0, timerId: null };

  function stopRrrTimer() {
    if (rrr.timerId) { clearInterval(rrr.timerId); rrr.timerId = null; }
  }

  function rrrLabel() {
    return mbT('Round {{n}} of {{m}}')
      .replace('{{n}}', Math.min(rrr.round, 3)).replace('{{m}}', 3);
  }

  function trendQuery(bookId, order) {
    return '?bookId=' + encodeURIComponent(bookId) + '&order=' + encodeURIComponent(order);
  }

  function renderTrend(trend) {
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
  }

  function loadRrrTrend() {
    getJson(urls.rrrTrend + trendQuery(rrr.bookId, rrr.order)).then(function (response) {
      renderTrend(resultOf(response));
    }).catch(function () { /* 趋势失败不打断训练 */ });
  }

  function armPanel(text) {
    esc(els['sw-rr-source'], text);
    show(els['sw-rr-panel'], true);
    els['sw-rr-round-label'].textContent = rrrLabel();
    els['sw-rr-metrics'].textContent = '';
  }

  function pickRrrParagraph(paragraph) {
    rrr.bookId = els['sw-rr-material'].value;
    rrr.order = paragraph.order;
    rrr.round = 1;
    armPanel(paragraph.text);
    els['sw-rr-trend'].hidden = true;
    els['sw-rr-stop'].hidden = true;
    els['sw-rr-start'].hidden = false;
  }

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

  // 「含你到期词的段落」推荐：点条目直接进训练（R153）
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
          getJson(urls.rrrTrend + trendQuery(item.bookId, item.order))
            .then(function (trendResponse) {
              var trend = resultOf(trendResponse);
              armPanel(trend.text);
              els['sw-rr-stop'].hidden = true;
              els['sw-rr-start'].hidden = false;
            }).catch(function (err) { window.alert(err.message); });
        });
        list.appendChild(line);
      });
    }).catch(function (err) { window.alert(err.message); });
  });
})();
