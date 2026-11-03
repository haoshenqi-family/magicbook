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
  toastError
};
