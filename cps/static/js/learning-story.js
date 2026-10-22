// 单词编故事子页面（R200）：到期词或粘贴词表 → AI 微故事 + 词表卡 + 朗读。
//
// 契约同 learning 其余子页：统一 Result 信封 {success, result, message}；生成是
// LLM 长任务，主路径走 SSE（status/ping/result/error），建连失败才回退 JSON 一次。
// 词表卡由 moon-well 从正文加粗处回抽，本页只负责展示，不自行猜句子。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, show = MB.show, clear = MB.clear, li = MB.li,
      esc = MB.esc, busy = MB.busy, getJson = MB.getJson, postJson = MB.postJson,
      resultOf = MB.resultOf, postSse = MB.postSse, csrfToken = MB.csrfToken;
  var urls = window.learningUrls || {};

  var els = {};
  ['sw-story-source', 'sw-story-due-controls', 'sw-story-count', 'sw-story-due-go',
   'sw-story-manual-controls', 'sw-story-words', 'sw-story-manual-go',
   'sw-story-status', 'sw-story-result', 'sw-story-title', 'sw-story-meta',
   'sw-story-text', 'sw-story-speak', 'sw-story-credit', 'sw-story-cards',
   'sw-story-history-panel', 'sw-story-history',
  ].forEach(function (id) { els[id] = $(id); });
  if (!els['sw-story-due-go']) return;

  var current = null;

  function setStatus(text) {
    esc(els['sw-story-status'], text || '');
    show(els['sw-story-status'], !!text);
  }

  function syncControls() {
    var manual = els['sw-story-source'].value === 'manual';
    show(els['sw-story-due-controls'], !manual);
    show(els['sw-story-manual-controls'], manual);
  }
  els['sw-story-source'].addEventListener('change', syncControls);
  syncControls();

  function tag(text) {
    var span = document.createElement('span');
    span.className = 'sw-story-tag';
    span.textContent = text;
    return span;
  }

  // 只解析 **加粗**：其余内容一律 textContent，上游正文不过 HTML 解析器。
  function renderStoryText(text) {
    clear(els['sw-story-text']);
    String(text).split(/\*\*([^*\n]+)\*\*/).forEach(function (part, i) {
      if (!part) return;
      if (i % 2 === 1) {
        var strong = document.createElement('strong');
        strong.textContent = part;
        els['sw-story-text'].appendChild(strong);
      } else {
        els['sw-story-text'].appendChild(document.createTextNode(part));
      }
    });
  }

  function renderCards(cards) {
    clear(els['sw-story-cards']);
    (cards || []).forEach(function (card) {
      var line = li('', 'sw-story-card');
      var word = document.createElement('span');
      word.className = 'sw-story-card-word';
      esc(word, card.word);
      line.appendChild(word);
      if (card.meaning) {
        var meaning = document.createElement('span');
        meaning.className = 'sw-story-card-meaning';
        esc(meaning, card.meaning);
        line.appendChild(meaning);
      }
      if (card.missing) line.appendChild(tag(mbT('Not in the story')));
      else if (card.uncached) line.appendChild(tag(mbT('Meaning from AI')));
      if (card.storySentence) {
        var sentence = document.createElement('p');
        sentence.className = 'sw-story-card-sentence';
        esc(sentence, card.storySentence);
        line.appendChild(sentence);
      }
      els['sw-story-cards'].appendChild(line);
    });
  }

  function renderStory(story) {
    current = story;
    show(els['sw-story-result'], true);
    esc(els['sw-story-title'], story.title || 'Word Story');
    var when = String(story.createdAt || '').replace('T', ' ').slice(0, 16);
    var sourceLabel = story.source === 'manual' ? mbT('Your word list') : mbT("Today's due words");
    esc(els['sw-story-meta'], [when, sourceLabel, story.cefrLevel]
      .filter(Boolean).join(' · '));
    renderStoryText(story.storyText || '');
    renderCards(story.cards);
    show(els['sw-story-credit'], true);
    if (els['sw-story-result'].scrollIntoView) {
      els['sw-story-result'].scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function handleEvent(event, payload) {
    if (event === 'status') {
      setStatus(payload && payload.phase === 'generating'
        ? mbT('Writing the story…') : mbT('Connecting…'));
    } else if (event === 'ping') {
      var seconds = Math.max(1, Math.round(((payload && payload.elapsedMs) || 0) / 1000));
      setStatus(mbT('Writing the story…') + ' ' + seconds + 's');
    }
  }

  function bodyFor(source) {
    if (source === 'manual') {
      var text = els['sw-story-words'].value.trim();
      if (!text) {
        window.alert(mbT('Paste a few English words first'));
        return null;
      }
      return { source: 'manual', words: [text] };
    }
    return { source: 'due', count: parseInt(els['sw-story-count'].value, 10) || 6 };
  }

  function submit(source) {
    var body = bodyFor(source);
    if (!body) return;
    var btn = source === 'manual' ? els['sw-story-manual-go'] : els['sw-story-due-go'];
    var streamUrl = urls.storyGenerateStream;
    var usedStream = !!streamUrl;
    var streamed = false;
    busy(btn, true, mbT('Writing the story…'));
    setStatus(mbT('Connecting…'));

    var request = usedStream
      ? postSse(streamUrl, body, handleEvent)
      : postJson(urls.storyGenerate, body).then(function (response) {
        return resultOf(response);
      });

    request.then(function (story) {
      streamed = true;
      setStatus('');
      renderStory(story);
      loadHistory();
    }).catch(function (err) {
      // 只在建连失败/首个事件前断网时回退 JSON；已经收到 status/ping 后的断网
      // 不再重试——故事可能已经落库并入账，重发只会多花一次 token。
      if (usedStream && !streamed && err && !err.streamStarted) {
        return postJson(urls.storyGenerate, body).then(function (response) {
          var story = resultOf(response);
          setStatus('');
          renderStory(story);
          loadHistory();
        });
      }
      throw err;
    }).catch(function (err) {
      var message = (err && err.message) || mbT('Story generation failed');
      setStatus(message);
      window.alert(message);
    }).finally(function () {
      busy(btn, false);
    });
  }

  els['sw-story-due-go'].addEventListener('click', function () { submit('due'); });
  els['sw-story-manual-go'].addEventListener('click', function () { submit('manual'); });

  function speak() {
    if (!current || !urls.readingTts) return;
    var text = String(current.storyText || '').replace(/\*\*/g, '').trim();
    if (!text) return;
    var btn = els['sw-story-speak'];
    busy(btn, true, mbT('Preparing audio…'));
    fetch(urls.readingTts, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      // bookName 让 moon-well 按「书籍段落」永久缓存；只发 text 会被当临时语音清理。
      body: JSON.stringify({
        text: text,
        bookName: 'Word Story · ' + (current.title || ''),
        chapter: '',
      }),
    }).then(function (response) {
      var type = response.headers.get('Content-Type') || '';
      if (response.ok && type.indexOf('audio') >= 0) return response.blob();
      return response.text().then(function (raw) {
        var message = raw || ('HTTP ' + response.status);
        try {
          var data = JSON.parse(raw);
          message = (data && (data.message || data.error || data.msg)) || message;
        } catch (e) {}
        throw new Error(message);
      });
    }).then(function (blob) {
      var url = URL.createObjectURL(blob);
      var audio = new Audio(url);
      audio.onended = function () { URL.revokeObjectURL(url); };
      audio.play().catch(function () {
        URL.revokeObjectURL(url);
        window.alert(mbT('Audio playback failed'));
      });
    }).catch(function (err) {
      window.alert((err && err.message) || mbT('Audio playback failed'));
    }).finally(function () {
      busy(btn, false);
    });
  }
  els['sw-story-speak'].addEventListener('click', speak);

  function loadDetail(id) {
    getJson(urls.storyDetail + '?id=' + encodeURIComponent(id)).then(function (response) {
      renderStory(resultOf(response));
    }).catch(function (err) { window.alert(err.message); });
  }

  function loadHistory() {
    getJson(urls.storyHistory).then(function (response) {
      var items = resultOf(response) || [];
      show(els['sw-story-history-panel'], items.length > 0);
      clear(els['sw-story-history']);
      items.forEach(function (item) {
        var line = li('');
        line.style.cursor = 'pointer';
        var title = document.createElement('b');
        esc(title, item.title || 'Word Story');
        line.appendChild(title);
        var when = String(item.createdAt || '').replace('T', ' ').slice(0, 16);
        line.appendChild(document.createTextNode(' · ' + when + ' · ' +
          ((item.words || []).length) + ' ' + mbT('words')));
        line.addEventListener('click', function () { loadDetail(item.id); });
        els['sw-story-history'].appendChild(line);
      });
    }).catch(function () {
      // 历史是增强面：moon-well 未就绪时隐藏面板，不挡住首次生成。
      show(els['sw-story-history-panel'], false);
    });
  }

  loadHistory();
})();
