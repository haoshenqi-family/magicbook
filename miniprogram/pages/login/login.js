/**
 * 登录页：微信一键登录（默认自动建号）+ 老用户密码认领。
 *
 * 状态机只有两段：
 *   idle —— 主按钮「微信一键登录」，次要入口「我已有账号」；
 *   bind —— 老用户点了次要入口，后端只给票据，就地展开账号密码表单。
 * 表单就在本页展开而不是跳新页：票据 10 分钟过期，多一次跳转就多一次失败面。
 *
 * Why 主按钮不再要求密码：第一次用小程序的人没有账号可输。先给他一个能用的
 * 临时账号，再引导绑定邮箱；老用户走次要入口，不会产生多余的空账号。
 */
const auth = require('../../utils/auth');
const api = require('../../utils/api');

Page({
  data: {
    phase: 'idle',
    loading: false,
    error: '',
    bindTicket: '',
    expiresIn: 0,
    username: '',
    password: ''
  },

  onLoad() {
    // 已登录直接进主界面（tabBar 页必须用 switchTab）
    if (auth.isLoggedIn()) {
      wx.switchTab({ url: '/pages/notebook/notebook' });
    }
  },

  /** 主路径：微信一键登录。后端未绑定时会自动建号并直接返回登录态。 */
  onTapLogin() {
    this.doLogin(false);
  },

  /** 次要路径：我已有账号 → 只拿票据，随后输密码绑到老账号。 */
  onTapLinkExisting() {
    this.doLogin(true);
  },

  async doLogin(linkExisting) {
    if (this.data.loading) return;
    this.setData({ loading: true, error: '' });
    try {
      const result = await auth.login(linkExisting);
      if (result && result.bindRequired) {
        this.setData({
          phase: 'bind',
          bindTicket: result.bindTicket,
          expiresIn: result.bindTicketExpiresIn || 600,
          loading: false
        });
        return;
      }
      auth.persist(result);
      this.setData({ loading: false });
      if (result && result.newAccount) {
        // 新账号不拦路：先让他用，提示放在主界面顶部（可点进账号页）
        wx.showToast({ title: '已为你创建微信账号', icon: 'none', duration: 1800 });
      }
      wx.switchTab({ url: '/pages/notebook/notebook' });
    } catch (error) {
      this.setData({ loading: false, error: error.message || '登录失败' });
    }
  },

  onUsernameInput(event) {
    this.setData({ username: event.detail.value });
  },

  onPasswordInput(event) {
    this.setData({ password: event.detail.value });
  },

  async onTapBind() {
    if (this.data.loading) return;
    const username = this.data.username.trim();
    const password = this.data.password;
    if (!username || !password) {
      this.setData({ error: '请输入用户名和密码' });
      return;
    }
    this.setData({ loading: true, error: '' });
    try {
      const result = await auth.bind(this.data.bindTicket, username, password);
      auth.persist(result);
      this.setData({ loading: false, password: '' });
      wx.switchTab({ url: '/pages/notebook/notebook' });
    } catch (error) {
      // 票据过期（50403）时把表单收回去，逼用户重新走微信登录拿新票据
      if (error.code === 50403) {
        this.setData({
          loading: false,
          phase: 'idle',
          bindTicket: '',
          error: error.message || '绑定已超时，请重新登录微信'
        });
        return;
      }
      this.setData({ loading: false, error: error.message || '绑定失败' });
    }
  },

  onCancelBind() {
    this.setData({ phase: 'idle', bindTicket: '', password: '', error: '' });
  }
});
