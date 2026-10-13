// 选书难度匹配子页面（R166 自 learning.js 迁出；选架→估算→推荐口径属 R147/R150）。
//
// 契约（moon-well /learning/match/books，R147）：result = {vocabSize, stage, books}，
// vocabSize=最近词汇量测试实测值（无测试为 null），stage=推荐阶（1-6，窗口 ±1），
// books[].bookId 是 Calibre 书 id（与本站 /book/{id} 同源，链接直达详情页）。
// 未算/过期的画像后端异步补算：densityPct=null 或 upToDate=false 的书存在时轮询。
(function () {
  'use strict';

  var MB = window.MBLearning;
  if (!MB) return;
  var mbT = MB.mbT, $ = MB.byId, getJson = MB.getJson;
  var urls = window.learningUrls || {};

  var els = {};
  ['ln-match-root', 'ln-match-status', 'ln-match-list'].forEach(function (id) { els[id] = $(id); });
  if (!els['ln-match-root']) return;

  var MATCH_LEVELS = {
    EASY: { cls: 'label-success', name: 'Easy read' },
    FIT: { cls: 'label-primary', name: 'Just right' },
    HARD: { cls: 'label-warning', name: 'Challenging' },
  };

  var MATCH_POLL_INTERVAL = 5000;
  var MATCH_POLL_MAX = 12;      // 1 分钟封顶：算不完就让「estimating…」自然停留
  var matchPollTimer = null;
  var matchPollCount = 0;
  var matchSeq = 0;             // 响应序号：轮询竞态时旧响应不覆盖新渲染

  function clearMatchPoll() {
    if (matchPollTimer) { clearTimeout(matchPollTimer); matchPollTimer = null; }
  }

  // 返回值：仍在估算/等待刷新的书本数（0=全部就绪）
  function renderShelf(shelf) {
    var list = els['ln-match-list'];
    list.innerHTML = '';
    var books = shelf && Array.isArray(shelf.books) ? shelf.books : [];

    var head = document.createElement('li');
    head.className = 'ln-match-head';
    if (shelf && shelf.stage != null) {
      var parts = [];
      if (shelf.vocabSize != null) {
        parts.push(mbT('Vocabulary') + ' ≈ ' + shelf.vocabSize);
      }
      parts.push(mbT('Recommended shelf') + ': ' + mbT('Stage') + ' ' + shelf.stage);
      head.textContent = parts.join(' · ');
    } else {
      head.textContent = mbT('Take the vocabulary test to size your bookshelf.');
    }
    list.appendChild(head);

    if (!books.length) {
      els['ln-match-status'].textContent = mbT('No graded books on this shelf yet.');
      return 0;
    }
    var pending = 0;
    books.forEach(function (item) {
      var li = document.createElement('li');
      // R147 404 修复：本站详情路由是 /book/{id}（Calibre 书 id），
      // 旧实现的 /books/{id}/page/1 是不存在的路由
      var link = document.createElement('a');
      link.href = '/book/' + item.bookId;
      link.textContent = item.title || ('#' + item.bookId);
      li.appendChild(link);
      if (item.stage != null) {
        var stage = document.createElement('span');
        stage.className = 'label ln-match-stage';
        stage.textContent = mbT('Stage') + ' ' + item.stage;
        li.appendChild(stage);
      }
      if (item.densityPct == null) {
        var estimating = document.createElement('span');
        estimating.className = 'ln-match-density';
        estimating.textContent = mbT('estimating…');
        li.appendChild(estimating);
        pending++;
      } else {
        var level = MATCH_LEVELS[item.level] || MATCH_LEVELS.FIT;
        var badge = document.createElement('span');
        badge.className = 'label ln-match-badge ' + level.cls;
        badge.textContent = mbT(level.name);
        li.appendChild(badge);
        var density = document.createElement('span');
        density.className = 'ln-match-density';
        density.textContent = item.densityPct + '% ' + mbT('unknown words') +
          (item.unknownTokenCount != null ? ' (~' + item.unknownTokenCount + ')' : '');
        li.appendChild(density);
        if (item.unknownSample && item.unknownSample.length && item.level === 'HARD') {
          var sample = document.createElement('span');
          sample.className = 'ln-match-sample';
          sample.textContent = item.unknownSample.slice(0, 5).join(', ');
          li.appendChild(sample);
        }
        if (item.upToDate === false) pending++;
      }
      list.appendChild(li);
    });
    els['ln-match-status'].textContent = pending > 0
      ? mbT('Estimating unknown words in {n} books…').replace('{n}', pending)
      : '';
    return pending;
  }

  function loadMatches() {
    var seq = ++matchSeq;
    getJson(urls.matchBooks).then(function (response) {
      if (seq !== matchSeq) return;   // 过期轮询响应
      if (response.ok && response.data && response.data.result) {
        var pendingCount = renderShelf(response.data.result);
        clearMatchPoll();
        if (pendingCount > 0 && matchPollCount < MATCH_POLL_MAX) {
          matchPollCount++;
          matchPollTimer = setTimeout(loadMatches, MATCH_POLL_INTERVAL);
        }
      } else {
        els['ln-match-status'].textContent = mbT('Difficulty match is unavailable right now.');
      }
    }).catch(function () {
      if (seq !== matchSeq) return;
      els['ln-match-status'].textContent = mbT('Difficulty match is unavailable right now.');
    });
  }

  loadMatches();
})();
