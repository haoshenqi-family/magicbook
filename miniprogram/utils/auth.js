/**
 * 登录态与微信登录/绑定流程（R240 起默认自动建号）。
 *
 * 流程（与 moon-well /auth/wx/* 对齐）：
 *   wx.login → code → POST /auth/wx/login
 *     ├─ 已绑定微信：直接拿到 JWT，进主界面
 *     ├─ 未绑定（默认）：后端建一个「微信临时账号」并下发 JWT，直接可用
 *     └─ 未绑定 + linkExisting：只拿到一张 10 分钟票据，输账号密码绑到老账号
 *
 * Why 默认建号：R239 的做法要求第一次用的人输账号密码，但新用户根本没有账号。
 * 现在先给一个能用的账号，再引导他去「账号」页绑定邮箱——绑到已有邮箱时，
 * 后端会把临时账号并进去，数据不会劈成两半。
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

/**
 * 登录。
 *
 * @param {boolean} linkExisting true = 我已有账号，别帮我建号（只拿票据走密码绑定）
 */
async function login(linkExisting) {
  const code = await wxLoginCode();
  return api.post('/auth/wx/login', { code, linkExisting: !!linkExisting }, { auth: false });
}

/** 老用户认领：票据 + 账号密码 → 直接登进已有账号。 */
function bind(bindTicket, username, password) {
  return api.post('/auth/wx/bind', { bindTicket, username, password }, { auth: false });
}

/**
 * 落盘登录结果。
 *
 * 三种来源形状一致（微信登录 / 密码绑定 / 邮箱绑定），都带 accessToken；
 * 邮箱绑定还会带上新的 userId——归并后账号换了，必须整份覆盖而不是合并。
 */
function persist(result) {
  api.setTokens(result.accessToken, result.refreshToken);
  api.setUser({
    userId: result.userId,
    username: result.username,
    nickname: result.nickname,
    avatar: result.avatar,
    email: result.email || '',
    emailVerified: !!result.emailVerified,
    wechatShadow: !!result.wechatShadow
  });
}

/** 刷新本地保存的账号信息（账号页拿到最新状态后调用，不必重新登录）。 */
function updateUser(patch) {
  const current = api.getUser() || {};
  api.setUser(Object.assign({}, current, patch || {}));
}

function logout() {
  api.clearSession();
  wx.reLaunch({ url: LOGIN_PAGE });
}

module.exports = {
  isLoggedIn,
  ensureLogin,
  login,
  bind,
  persist,
  updateUser,
  logout,
  LOGIN_PAGE
};
