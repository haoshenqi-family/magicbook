/**
 * 登录页：微信一键登录（默认自动建号）+ 邮箱验证登录已有账号（不输密码）。
 *
 * 状态机三段：
 *   idle  —— 主按钮「微信一键登录」，次按钮「我已有账号，用邮箱登录」；
 *   email —— 老用户点了次按钮：后端只给票据，先让他填邮箱；
 *   code  —— 验证码已发出，填 6 位码提交。
 *
 * Why 用邮箱而不是密码认领：账号密码是用户要记住的东西，而邮箱验证码只需要能收信；
 * 而且邮箱正是网页端账号的登录凭据，用它来「认」自己的账号比密码更接近真实语义。
 *
 * 表单就在本页展开而不是跳新页：票据 10 分钟过期，多一次跳转就多一次失败面。
 * 整个邮箱流程都不产生账号——后端只有在邮箱命中已有账号时才建绑定。
 */
const auth = require('../../utils/auth');

Page({
  data: {
    phase: 'idle',
    loading: false,
    error: '',
    bindTicket: '',
    expiresIn: 0,
    email: '',
    code: '',
    countdown: 0
  },

  onLoad() {
    if (auth.isLoggedIn()) {
      wx.switchTab({ url: '/pages/review/review' });
    }
  },

  onUnload() {
    this.clearTimer();
  },

  /** 主路径：微信一键登录。后端未绑定时自动建号并直接返回登录态。 */
  onTapLogin() {
    this.doLogin(false);
  },

  /** 次路径：我已有账号 → 只拿票据，随后用邮箱验证码登进去。 */
  onTapEmailLogin() {
    this.startEmailLogin();
  },

  async doLogin(linkExisting) {
    if (this.data.loading) return;
    this.setData({ loading: true, error: '' });
    try {
      const result = await auth.login(linkExisting);
      if (result && result.bindRequired) {
        this.setData({
          phase: 'email',
          bindTicket: result.bindTicket,
          expiresIn: result.bindTicketExpiresIn || 600,
          loading: false
        });
        return;
      }
      auth.persist(result);
      this.setData({ loading: false });
      if (result && result.newAccount) {
        wx.showToast({ title: '已为你创建微信账号', icon: 'none', duration: 1800 });
      }
      wx.switchTab({ url: '/pages/review/review' });
    } catch (error) {
      this.setData({ loading: false, error: error.message || '登录失败' });
    }
  },

  /** 邮箱登录入口：先换票据（不建号），再进邮箱表单。 */
  async startEmailLogin() {
    this.setData({ loading: true, error: '' });
    try {
      const result = await auth.login(true);
      if (result && result.bindRequired) {
        this.setData({
          phase: 'email',
          bindTicket: result.bindTicket,
          expiresIn: result.bindTicketExpiresIn || 600,
          loading: false
        });
        return;
      }
      // 这个微信已经绑着某个账号：直接进去，不必再验邮箱
      auth.persist(result);
      this.setData({ loading: false });
      wx.switchTab({ url: '/pages/review/review' });
    } catch (error) {
      this.setData({ loading: false, error: error.message || '获取登录票据失败' });
    }
  },

  onEmailInput(event) {
    this.setData({ email: event.detail.value });
  },

  onCodeInput(event) {
    this.setData({ code: event.detail.value });
  },

  async onSendCode() {
    if (this.data.loading || this.data.countdown > 0) return;
    const email = this.data.email.trim();
    if (!email) {
      this.setData({ error: '请输入邮箱' });
      return;
    }
    this.setData({ loading: true, error: '' });
    try {
      const result = await auth.sendEmailCode(this.data.bindTicket, email);
      this.setData({ loading: false, phase: 'code' });
      this.startCountdown((result && result.resendAfter) || 60);
      wx.showToast({ title: '验证码已发送', icon: 'none' });
    } catch (error) {
      this.setData({ loading: false, error: error.message || '发送失败' });
    }
  },

  async onVerify() {
    if (this.data.loading) return;
    const code = this.data.code.trim();
    if (!code) {
      this.setData({ error: '请输入验证码' });
      return;
    }
    this.setData({ loading: true, error: '' });
    try {
      const result = await auth.verifyEmail(this.data.bindTicket, this.data.email.trim(), code);
      auth.persist(result);
      this.setData({ loading: false });
      wx.showToast({ title: '已登录', icon: 'success' });
      wx.switchTab({ url: '/pages/review/review' });
    } catch (error) {
      this.setData({ loading: false });
      if (error.code === 50514) {
        // 邮箱没有账号：告诉他正确动作，而不是让他反复重试
        this.setData({
          error: error.message || '该邮箱还没有账号，请用「微信一键登录」创建',
          phase: 'idle',
          bindTicket: '',
          code: ''
        });
        this.clearTimer();
        return;
      }
      if (error.code === 50403) {
        this.setData({
          error: '登录已超时，请重新点击「我已有账号」',
          phase: 'idle',
          bindTicket: '',
          code: ''
        });
        this.clearTimer();
        return;
      }
      this.setData({ error: error.message || '验证失败' });
    }
  },

  onCancelEmail() {
    this.clearTimer();
    this.setData({ phase: 'idle', bindTicket: '', email: '', code: '', countdown: 0, error: '' });
  },

  startCountdown(seconds) {
    this.clearTimer();
    this.setData({ countdown: seconds });
    this.timer = setInterval(() => {
      const next = this.data.countdown - 1;
      if (next <= 0) {
        this.clearTimer();
        this.setData({ countdown: 0 });
        return;
      }
      this.setData({ countdown: next });
    }, 1000);
  },

  clearTimer() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
});
