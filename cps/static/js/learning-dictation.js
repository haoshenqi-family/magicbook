// 听写子页面（R166 自 speaking_writing.js 迁出；词级 diff 契约属 R153/B2a）。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, clear = MB.clear, esc = MB.esc,
      busy = MB.busy, postJson = MB.postJson, resultOf = MB.resultOf,
      loadMaterials = MB.loadMaterials, paragraphLine = MB.paragraphLine;
  var urls = window.learningUrls || {};

  var els = {};
  ['sw-d-material', 'sw-d-load', 'sw-d-paragraphs',
   'sw-d-panel', 'sw-d-play', 'sw-d-audio-status', 'sw-d-audio',
   'sw-d-answer', 'sw-d-add-unknown', 'sw-d-check', 'sw-d-result',
   'sw-d-accuracy', 'sw-d-tokens', 'sw-d-missing', 'sw-d-extra',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-d-load']) return;

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
      // 真人音频（TED 素材）：按段落时间戳切片播放
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
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': MB.csrfToken() },
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
    }).catch(function () {
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
})();
