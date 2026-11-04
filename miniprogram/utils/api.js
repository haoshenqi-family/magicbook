/**
 * moon-well API 访问层：统一鉴权、统一解包、401 单次刷新重试。
 *
 * 约定（与 moon-well 的 Result 形制对齐）：
 *   { success, code, message, result }
 * - 成功：success=true，数据在 result；
 * - 业务失败：HTTP 500 + Result.code（如 50403 绑定超时、50301 词表未就绪）；
 * - 鉴权失败：HTTP 401 / code 401 / code 102。
 *
 * Why 所有失败都抛同一个形状 { code, message }：页面只需要 `catch(e => toast(e.message))`，
 * 不需要各自判断 HTTP 状态。**不做静默降级**——后端故障显示成「暂无数据」会让用户以为
 * 自己的记录丢了（这是本项目明令禁止的形态）。
 */
const CONFIG = require('../config');

const KEY = {
  access: 'mb.accessToken',
  refresh: 'mb.refreshToken',
  user: 'mb.user'
};

function getAccess() {
  return wx.getStorageSync(KEY.access) || '';
}

function getRefresh() {
  return wx.getStorageSync(KEY.refresh) || '';
}

function setTokens(accessToken, refreshToken) {
  if (accessToken) wx.setStorageSync(KEY.access, accessToken);
  if (refreshToken) wx.setStorageSync(KEY.refresh, refreshToken);
}

function setUser(user) {
  if (user) wx.setStorageSync(KEY.user, user);
}

function getUser() {
  return wx.getStorageSync(KEY.user) || null;
}

function clearSession() {
  wx.removeStorageSync(KEY.access);
  wx.removeStorageSync(KEY.refresh);
  wx.removeStorageSync(KEY.user);
}

function rawRequest(options) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: CONFIG.baseUrl + options.path,
      method: options.method || 'GET',
      data: options.data,
      header: options.header || {},
      timeout: CONFIG.timeout,
      success: resolve,
      fail: (err) => {
        // 原始 errMsg 必须留痕：体验版最常见的失败是「域名不在白名单」，
        // 它只出现在这里。统一抹成「请检查网络」会把排查方向整体带偏——
        // 开发者工具关了域名校验就正常，真机/体验版却全挂，正是这个组合的典型症状。
        console.error('[api] 请求失败', options.path, (err && err.errMsg) || '');
        reject({ code: -1, message: describeNetworkError(err) });
      }
    });
  });
}

/**
 * 把 wx.request 的 fail 翻成「下一步该做什么」。
 *
 * 三类分开：白名单（要改小程序后台）、超时（重试）、链路/证书（查服务端与网络）。
 * 认不出来的原样带出 errMsg——保底可见，胜过一句什么都没说的「请检查网络」。
 */
function describeNetworkError(err) {
  const raw = (err && err.errMsg) || '';
  if (/url not in domain list|not in domain list/i.test(raw)) {
    return '请求域名未配置白名单：请在小程序后台「开发管理 → 开发设置 → 服务器域名」'
      + '添加 ' + CONFIG.baseUrl.replace('https://', '');
  }
  if (/timeout/i.test(raw)) {
    return '请求超时：网络较慢或服务未响应，请重试';
  }
  if (/ssl|cert|handshake|ERR_CONNECTION/i.test(raw)) {
    return '连接失败：' + raw;
  }
  return raw ? '网络请求失败：' + raw : '网络请求失败：请检查网络';
}

function unwrap(res) {
  const body = res && res.data && typeof res.data === 'object' ? res.data : {};
  const status = (res && res.statusCode) || 0;
  if (status === 401 || body.code === 401 || body.code === 102) {
    return {
      authError: true,
      code: body.code || 401,
      message: body.message || '登录已失效，请重新登录'
    };
  }
  if (status >= 400 || body.success === false) {
    return {
      error: true,
      code: body.code == null ? status : body.code,
      status,
      message: body.message || ('请求失败（HTTP ' + status + '）')
    };
  }
  return { data: body.result };
}

// 同一时刻只允许一次刷新：四个 tab 同时 401 时不能打出四发 refreshToken
let refreshing = null;

function refreshToken() {
  if (refreshing) return refreshing;
  const token = getRefresh();
  if (!token) return Promise.resolve(false);
  refreshing = rawRequest({
    path: '/auth/refreshToken',
    method: 'POST',
    data: { refreshToken: token },
    header: { 'content-type': 'application/json' }
  })
    .then((res) => {
      const result = (res.data && res.data.result) || {};
      if (res.statusCode < 400 && result.accessToken) {
        setTokens(result.accessToken, result.refreshToken || token);
        return true;
      }
      clearSession();
      return false;
    })
    .catch(() => false)
    .then((ok) => {
      refreshing = null;
      return ok;
    });
  return refreshing;
}

async function request(options) {
  const useAuth = options.auth !== false;
  const send = () => {
    const header = Object.assign({ 'content-type': 'application/json' }, options.header || {});
    if (useAuth && getAccess()) {
      header.authorization = 'Bearer ' + getAccess();
    }
    return rawRequest({ path: options.path, method: options.method, data: options.data, header });
  };

  let res = await send();
  let out = unwrap(res);
  if (out.authError && useAuth) {
    const refreshed = await refreshToken();
    if (refreshed) {
      res = await send();
      out = unwrap(res);
    }
  }
  if (out.authError) {
    clearSession();
    throw { code: out.code, message: out.message, authError: true };
  }
  if (out.error) {
    throw { code: out.code, message: out.message };
  }
  return out.data;
}

function get(path, data, options) {
  return request(Object.assign({ path, data, method: 'GET' }, options || {}));
}

function post(path, data, options) {
  return request(Object.assign({ path, data, method: 'POST' }, options || {}));
}

/** 页面统一的错误提示：AuthException 直接甩回登录页，其余弹后端文案。 */
function toastError(error) {
  const message = (error && error.message) || '请求失败';
  if (error && error.authError) {
    wx.reLaunch({ url: '/pages/login/login' });
    return;
  }
  wx.showToast({ title: message, icon: 'none', duration: 2600 });
}

/**
 * UTF-8 分块解码（SSE 专用，可导出做单测）。
 *
 * Why 不能直接 String.fromCharCode：onChunkReceived 给的是字节片段，一个汉字（3 字节）
 * 完全可能跨两个片段，半个序列直接转会变乱码。carry 把没凑齐的字节留到下一块；
 * 遇到坏字节用 U+FFFD 兜住，不让一个片段毁掉整段回答。
 */
function decodeUtf8(bytes, carry) {
  const buf = carry && carry.length
    ? carry.concat(Array.prototype.slice.call(bytes))
    : Array.prototype.slice.call(bytes);
  let text = '';
  let i = 0;
  while (i < buf.length) {
    const b = buf[i];
    let need = 1;
    if (b >= 0xC2 && b <= 0xDF) need = 2;
    else if (b >= 0xE0 && b <= 0xEF) need = 3;
    else if (b >= 0xF0 && b <= 0xF4) need = 4;
    if (i + need > buf.length) break; // 序列没凑齐，留到下一块
    let cp = need === 1 ? b : b & (0x7F >> need);
    let valid = true;
    for (let k = 1; k < need; k++) {
      const cont = buf[i + k];
      if ((cont & 0xC0) !== 0x80) { valid = false; break; }
      cp = (cp << 6) | (cont & 0x3F);
    }
    if (!valid || (need > 1 && b < 0xC2)) {
      text += '\uFFFD';
      i += 1;
      continue;
    }
    if (cp > 0xFFFF) {
      cp -= 0x10000;
      text += String.fromCharCode(0xD800 + (cp >> 10), 0xDC00 + (cp & 0x3FF));
    } else {
      text += String.fromCharCode(cp);
    }
    i += need;
  }
  return { text, carry: buf.slice(i) };
}

/** 解析一个 SSE 帧；兼容只有 data 行的旧裸文本流。 */
function parseSseBlock(block) {
  let name = null;
  const dataLines = [];
  block.split('\n').forEach((line) => {
    const trimmed = line.trim();
    if (trimmed.indexOf('event:') === 0) name = trimmed.slice(6).trim();
    else if (trimmed.indexOf('data:') === 0) dataLines.push(trimmed.slice(5).trim());
  });
  if (!dataLines.length) return null;
  const raw = dataLines.join('\n');
  let data;
  try {
    data = JSON.parse(raw);
  } catch (e) {
    data = { text: raw, data: raw };
  }
  return { name: name || 'delta', data };
}

/**
 * AI 伴读 SSE 流式对话（POST /ai/agent/chat）。
 *
 * Why 单独一条通道而不是复用 request()：小程序没有 fetch/EventSource，SSE 必须走
 * wx.request 的 enableChunked + onChunkReceived；普通请求的 Promise 解包只认
 * Result{success,result}，会把事件流当成一个 JSON 直接判失败。
 *
 * 401 只在「连接建立、流尚未开始」时重试一次（与网页薄代理同口径）：流一旦开始就
 * 无法回滚已发的 delta，重放会重复计费、重复出字。
 *
 * @returns {object} wx.request 的 RequestTask，页面可在 onUnload 里 abort()
 */
function chatStream(payload, handlers) {
  const onEvent = (handlers && handlers.onEvent) || function () {};
  const onDone = (handlers && handlers.onDone) || function () {};
  const onError = (handlers && handlers.onError) || function () {};
  let buffer = '';
  let carry = [];
  let receivedChunks = false;
  let finished = false;
  let retried = false;
  let task = null;

  function drain(flush) {
    // SseEmitter 用 \n\n 分帧；代理层偶尔带 CRLF，先归一，否则帧永远拼不齐。
    buffer = buffer.replace(/\r\n/g, '\n');
    let idx;
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      const block = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const event = parseSseBlock(block);
      if (event) onEvent(event.name, event.data);
    }
    if (flush && buffer.trim()) {
      const event = parseSseBlock(buffer);
      if (event) onEvent(event.name, event.data);
      buffer = '';
    }
  }

  function finish(error) {
    if (finished) return;
    finished = true;
    if (error) onError(error);
    else onDone();
  }

  function httpError(res) {
    let body = {};
    try {
      const raw = typeof res.data === 'string'
        ? res.data
        : res.data && res.data.byteLength
          ? decodeUtf8(new Uint8Array(res.data), []).text
          : '';
      body = raw ? JSON.parse(raw) : {};
    } catch (e) {
      body = {};
    }
    return body.message || ('请求失败（HTTP ' + res.statusCode + '）');
  }

  function start() {
    const header = {
      'content-type': 'application/json',
      Accept: 'text/event-stream'
    };
    if (getAccess()) header.authorization = 'Bearer ' + getAccess();
    task = wx.request({
      url: CONFIG.baseUrl + '/ai/agent/chat',
      method: 'POST',
      data: payload,
      header,
      responseType: 'arraybuffer',
      enableChunked: true,
      timeout: CONFIG.chatTimeout,
      success: (res) => {
        const status = res.statusCode || 0;
        if ((status === 401 || status === 403) && !retried) {
          retried = true;
          refreshToken().then((ok) => {
            if (ok) start();
            else { clearSession(); finish('登录已失效，请重新登录'); }
          });
          return;
        }
        if (status >= 400) {
          console.error('[api] chat HTTP error', status);
          finish(httpError(res));
          return;
        }
        // 低版本基础库不支持 onChunkReceived 时，success 里拿到的是完整响应体
        if (!receivedChunks && res.data && res.data.byteLength) {
          const decoded = decodeUtf8(new Uint8Array(res.data), carry);
          carry = decoded.carry;
          buffer += decoded.text;
        }
        drain(true);
        finish();
      },
      fail: (err) => {
        console.error('[api] chat 请求失败', (err && err.errMsg) || '');
        finish(describeNetworkError(err));
      }
    });
    if (task && typeof task.onChunkReceived === 'function') {
      task.onChunkReceived((res) => {
        receivedChunks = true;
        const decoded = decodeUtf8(new Uint8Array(res.data), carry);
        carry = decoded.carry;
        buffer += decoded.text;
        drain(false);
      });
    }
  }

  start();
  return {
    abort: function () {
      if (task && typeof task.abort === 'function') task.abort();
    }
  };
}

module.exports = {
  getAccess,
  getRefresh,
  setTokens,
  setUser,
  getUser,
  clearSession,
  request,
  get,
  post,
  refreshToken,
  toastError,
  chatStream,
  decodeUtf8,
  parseSseBlock
};
