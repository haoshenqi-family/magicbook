// 账号级阅读位置上报（R213-B / PJM MB-17）
//
// Why 独立文件：位置上报与「阅读活跃心跳」（reading_time_tracker.js）是两件事——
// 心跳回答「今天读了多久」，本文件回答「读到哪一页」。两者节流口径不同、失败策略
// 相同（静默丢弃、绝不打断阅读），拆开后各自的节流参数不会互相污染。
//
// Why 只上报、不负责恢复：恢复要在 rendition 初始化前拿到服务端位置，属于装配层
// （epub.js 的 book.ready 链路）；本文件只做「采集 + 节流 + 发送」。
//
// 节流口径：距上次上报 ≥10s，或页码变化 ≥5 页，才发一次；页面隐藏/卸载时补最后一笔
// （keepalive fetch 能带 CSRF 头，比 sendBeacon 更适合全局 CSRFProtect 的站点）。
(function () {
  'use strict';

  var ENDPOINT = '/ajax/reading-progress';
  var MIN_INTERVAL_MS = 10 * 1000; // 10 秒
  var PAGE_STEP = 5;               // 或翻 5 页

  var bookId = null;
  var bookFormat = null;
  var lastSentAt = 0;
  var lastSentPage = null;
  var lastPayload = null;   // 最后一次采集到的位置，卸载时补发用
  var sending = false;

  function csrfToken() {
    var el = document.querySelector("input[name='csrf_token']");
    return el ? el.value : '';
  }

  // 配置来源：read.html 注入的 window.calibre（bookId / bookFormat），
  // 也可由装配层显式调用 configure 覆盖（PDF/TXT 阅读器后续接入时用）
  function configure(opts) {
    opts = opts || {};
    var calibre = window.calibre || {};
    bookId = opts.bookId || calibre.bookId || null;
    bookFormat = (opts.format || calibre.bookFormat || '').toUpperCase() || null;
    return bookId && bookFormat;
  }

  function send(payload) {
    if (sending || !bookId || !bookFormat) return;
    sending = true;
    fetch(ENDPOINT, {
      method: 'POST',
      credentials: 'same-origin',
      keepalive: true, // 卸载瞬间补发也能送达（同 reading_time_tracker 的姿势）
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(payload),
    }).then(function (response) {
      if (!response.ok) {
        // Why 只 warn 不 toast：进度丢一次不影响这一屏阅读，但必须留痕——
        // 静默吞掉会让「进度没记住」永远无法定位是没上报还是被服务端拒了
        console.warn('[reader-progress] report rejected', response.status);
      }
    }).catch(function (err) {
      console.warn('[reader-progress] report failed', err && err.message);
    }).finally(function () { sending = false; });
  }

  // 采集一次位置；是否真的发出去由节流决定
  function update(location) {
    if (!location || !bookId || !bookFormat) return;
    lastPayload = {
      book_id: bookId,
      format: bookFormat,
      position: location.position || null,
      percent: typeof location.percent === 'number' ? location.percent : null,
      page_current: typeof location.page === 'number' ? location.page : null,
      page_total: typeof location.total === 'number' ? location.total : null,
    };
    var now = Date.now();
    var pageJumped = lastSentPage === null ||
      (typeof location.page === 'number' && Math.abs(location.page - lastSentPage) >= PAGE_STEP);
    if (now - lastSentAt < MIN_INTERVAL_MS && !pageJumped) return;
    lastSentAt = now;
    lastSentPage = typeof location.page === 'number' ? location.page : lastSentPage;
    send(lastPayload);
  }

  // 卸载/切后台补最后一笔：节流窗口内的位置否则会丢
  function flush() {
    if (!lastPayload) return;
    send(lastPayload);
    lastSentAt = Date.now();
  }

  if (!configure()) {
    console.warn('[reader-progress] 未配置 bookId/format，位置上报未启用');
  }

  window.addEventListener('pagehide', flush);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') flush();
  });

  window.ReaderProgress = {
    configure: configure,
    update: update,
    flush: flush,
  };
})();
