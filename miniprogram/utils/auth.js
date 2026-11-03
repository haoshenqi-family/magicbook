/**
 * 登录态与微信登录/绑定流程。
 *
 * 流程（与 moon-well /auth/wx/* 对齐）：
 *   wx.login → code → POST /auth/wx/login
 *     ├─ bindRequired=false：直接拿到 JWT，进主界面
 *     └─ bindRequired=true ：只拿到一张 10 分钟票据，需再用账号密码完成首次绑定
 *
 * Why 首次必须输一次账号密码：账号承载网页端积累的生词本与复习进度，
 * 让小程序自动建新号等于把用户的数据劈成两半。
 */
const api = require('./api');

const LOGIN_PAGE = '/pages/login/login';

function isLoggedIn() {
  return !!api.getAccess();
}

/** 未登录直接踢回登录页，返回 false 供调用方短路。 */
function ensureLogin() {
  if (isLoggedIn()) return true;
  wx.reLaunch({ url: LOGIN_PAGE });
  return false;
}

function wxLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        if (res && res.code) {
          resolve(res.code);
        } else {
          reject({ code: 'WX_NO_CODE', message: '微信登录失败，请重试' });
        }
      },
      fail: () => reject({ code: 'WX_LOGIN_FAIL', message: '微信登录失败，请重试' })
    });
  });
}

/** 第一步：code 换身份。返回 { bindRequired, bindTicket, accessToken, ... } */
async function login() {
  const code = await wxLoginCode();
  return api.post('/auth/wx/login', { code }, { auth: false });
}

/** 第二步：首次绑定。成功后同样返回 token 形状。 */
function bind(bindTicket, username, password) {
  return api.post('/auth/wx/bind', { bindTicket, username, password }, { auth: false });
}

/** 落盘登录结果（两处形状一致：登录与绑定成功都带 accessToken）。 */
function persist(result) {
  api.setTokens(result.accessToken, result.refreshToken);
  api.setUser({
    userId: result.userId,
    username: result.username,
    nickname: result.nickname,
    avatar: result.avatar
  });
}

function logout() {
  api.clearSession();
  wx.reLaunch({ url: LOGIN_PAGE });
}

module.exports = { isLoggedIn, ensureLogin, login, bind, persist, logout, LOGIN_PAGE };
