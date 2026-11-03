/**
 * 登录页：微信一键登录 + 首次绑定。
 *
 * 状态机只有两段：
 *   idle —— 只有「微信一键登录」；
 *   bind —— 免登不了（后端返回 bindRequired），就地出账号密码表单。
 * 表单就在本页展开而不是跳新页：票据 10 分钟过期，多一次跳转就多一次失败面。
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

  async onTapLogin() {
    if (this.data.loading) return;
    this.setData({ loading: true, error: '' });
    try {
      const result = await auth.login();
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
