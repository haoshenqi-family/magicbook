// 全站 API 公共层（R177，架构评审 B5 / X1 本仓部分）。
//
// Why 单独一个 common：解包与 CSRF 获取此前四份副本（learning-common.js /
// ai_chat.js / vocab-test.js / credits.js），CSRF 元素 id 各页不同（#lh-csrf /
// #credit-csrf / input[name=csrf_token]），解包语义漂移（ai_chat 容错版 vs
// credits 严格版）。moon-well 侧 Result 包装开始框架兜底（M4）后，消费方解包
// 必须统一口径：非 Result 形态（登录页 HTML、网关 502、裸数组）不误判、不
// 静默；失败 message 必须抛给调用方呈现——静默降级把接口故障伪装成「数据
// 不存在」是家族级反模式（R44/R173 教训），公共层只负责抛，呈现归各页容器。
//
// 载入：layout.html 全局（learning 系/credits 等）+ read.html、
// reading_settings.html（独立骨架页）各自引入，必须先于页面脚本。
(function () {
  'use strict';

  // CSRF 元素三形态链式探测：learning 系（#lh-csrf）→ 积分页（#credit-csrf）
  // → 阅读页/设置页隐藏域（input[name=csrf_token]）。都不在返回空串：GET 类
  // 请求不需要 CSRF；POST 由后端 before_request 拦截，各页既有自愈逻辑不变。
  function csrfToken() {
    var el = document.getElementById('lh-csrf') ||
             document.getElementById('credit-csrf') ||
             document.querySelector("input[name='csrf_token']");
    return el ? el.value : '';
  }

  function httpJson(url, options) {
    return fetch(url, options).then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { /* 非 JSON 按失败处理 */ }
        return { ok: response.ok, status: response.status, data: data, raw: text };
      });
    });
  }

  function getJson(url) {
    return httpJson(url, { credentials: 'same-origin' });
  }

  function postJson(url, body) {
    return httpJson(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(body || {}),
    });
  }

  function isBusinessError(response) {
    return response.data && response.data.success === false && response.data.code &&
      response.data.code !== 200;
  }

  // moon-well Result 信封 {success, result, message} 的容错解包（ai_chat 口径）：
  //  - success === false → 抛 Error(message)（上游业务文案，调用方必须呈现）
  //  - success === true 且含 result 字段 → 解出 result（M4 起后端框架兜底，形态稳定）
  //  - 其余（非信封 JSON、裸数组、parse 失败的 null）→ 原样返回，不误判。
  // Why 容错而非严格：strict 口径（success !== true 即抛）会把登录页 HTML、
  // 网关 502 等非信封响应当「业务失败」，吞掉真实故障形态；容错版把非信封
  // 响应的判读留给调用方各自的 response.ok / codeOf 逻辑。
  function unwrapResult(data) {
    if (data && typeof data === 'object' && data.success === false) {
      throw new Error(data.message || window.mbT('Something went wrong'));
    }
    if (data && typeof data === 'object' && data.success === true &&
        Object.prototype.hasOwnProperty.call(data, 'result')) {
      return data.result;
    }
    return data;
  }

  // 严格解包（learning-common resultOf / credits unwrap 原口径，行为保持）：
  // 非标准信封（含 parse 失败 null）一律抛——这两页的消费方在 catch 里呈现
  // 错误行/告警框，strict 语义下 null 也不会静默漏到渲染层。
  function unwrapStrict(data) {
    if (!data || typeof data !== 'object' || data.success !== true) {
      throw new Error((data && data.message) || window.mbT('Something went wrong'));
    }
    return data.result;
  }

  window.MBApi = {
    csrfToken: csrfToken,
    httpJson: httpJson,
    getJson: getJson,
    postJson: postJson,
    isBusinessError: isBusinessError,
    unwrapResult: unwrapResult,
    unwrapStrict: unwrapStrict,
  };
})();
