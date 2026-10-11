// 阅读活跃心跳（R151 / moon-well R150 四股台账 INPUT 股信号源）。
//
// Why 独立文件：readtxt/readpdf 无 jQuery 且与 epub.js 的生命周期无关，
// 心跳必须是零依赖 vanilla JS，四个阅读模板（epub/txt/pdf）共用一份。
//
// 判定口径：标签页可见 && 最近 3 分钟内有真实交互（翻页/滚动/点击/按键/触摸）
// 才计活跃——后台标签页与挂机不动都不计入，宁低估不虚增。
// 结算节奏：每 30s 结算一次；每累计 300s 批量上报一次（moon-well 端按 5 分钟
// 槽位幂等入账，重发不双计）。上报失败静默丢弃：心跳丢失只影响当日台账展示，
// 绝不重试堆积、绝不打断阅读。
(function () {
  'use strict';

  var TICK_SECONDS = 30;                    // 结算周期
  var INTERACTION_FRESH_MS = 3 * 60 * 1000; // 交互保鲜期：3 分钟内无交互视为挂机
  var BATCH_SECONDS = 300;                  // 批量上报阈值（与 moon-well 槽位对齐）
  var MIN_REPORT_SECONDS = 30;              // 卸载补发下限（服务端 @Min(30)）
  var ENDPOINT = '/ajax/learning/strands/reading';

  var lastInteractionAt = 0;
  var activeSeconds = 0;   // 已判定活跃、尚未上报的秒数
  var sending = false;

  function csrfToken() {
    var el = document.querySelector("input[name='csrf_token']");
    return el ? el.value : '';
  }

  // 书 id 仅作排查线索；四个阅读器的持有方式不一，从 URL 取（/read/<id>/<fmt>）
  function bookId() {
    var match = location.pathname.match(/\/read\/(\d+)/);
    return match ? match[1] : null;
  }

  function bump() {
    lastInteractionAt = Date.now();
  }

  ['scroll', 'wheel', 'keydown', 'click', 'touchstart', 'mousedown'].forEach(function (name) {
    window.addEventListener(name, bump, { passive: true, capture: true });
  });

  function report(seconds) {
    if (sending) return;
    sending = true;
    var body = { seconds: seconds, bookId: bookId() };
    fetch(ENDPOINT, {
      method: 'POST',
      credentials: 'same-origin',
      keepalive: true,  // 页面卸载瞬间补发也能送达
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(body),
    }).catch(function () { /* 静默：宁低估不堆积 */ })
      .finally(function () { sending = false; });
  }

  setInterval(function () {
    if (document.visibilityState !== 'visible') return;
    if (!lastInteractionAt || Date.now() - lastInteractionAt > INTERACTION_FRESH_MS) return;
    activeSeconds += TICK_SECONDS;
    if (activeSeconds >= BATCH_SECONDS) {
      report(activeSeconds);
      activeSeconds = 0;
    }
  }, TICK_SECONDS * 1000);

  // 卸载补发尾巴：不足一个批次但满一个结算周期的活跃时长也入账
  window.addEventListener('pagehide', function () {
    if (activeSeconds >= MIN_REPORT_SECONDS) {
      report(activeSeconds);
      activeSeconds = 0;
    }
  });
})();
