/**
 * 账号页：看清「我现在是谁」+ 绑定邮箱（把微信临时账号并进已有账号）+ 退出登录。
 *
 * 三类状态，界面文案必须能区分开，否则用户不知道自己是不是在用一份孤立的账号：
 *   1. 微信临时账号（wechatShadow=true，无邮箱）：能用但没有找回途径；
 *   2. 已绑定邮箱（emailVerified=true）：正式账号，可在网页端用同一邮箱找回；
 *   3. 邮箱属于老账号且归并完成：userId 换了，token 也已换发。
 *
 * 归并前若发现临时账号里已有学习数据，后端返回 50512 并列出数据；
 * 这里必须再弹一次确认，绝不替用户丢掉已经背过的词。
 */
const api = require('../../utils/api');
const auth = require('../../utils/auth');

Page({
  data: {
    user: null,
    email: '',
    code: '',
    stage: 'idle',
    sending: false,
    submitting: false,
    countdown: 0,
    error: ''
  },

  onShow() {
    if (!auth.ensureLogin()) return;
    this.setData({ user: api.getUser() || {} });
  },

  onUnload() {
    this.clearTimer();
  },

  onHide() {
    this.clearTimer();
  },

  onEmailInput(event) {
    this.setData({ email: event.detail.value });
  },

  onCodeInput(event) {
    this.setData({ code: event.detail.value });
  },

  async onSendCode() {
    if (this.data.sending || this.data.countdown > 0) return;
    const email = this.data.email.trim();
    if (!email) {
      this.setData({ error: '请输入邮箱' });
      return;
    }
    this.setData({ sending: true, error: '' });
    try {
      const result = await api.post('/auth/email/send-code', { email });
      this.setData({ sending: false, stage: 'code' });
      // 用后端给的间隔起倒计时，避免前后端口径不一致导致「点了没反应」
      this.startCountdown(result.resendAfter || 60);
      wx.showToast({ title: '验证码已发送', icon: 'none' });
    } catch (error) {
      this.setData({ sending: false, error: error.message || '发送失败' });
    }
  },

  async onSubmitCode() {
    if (this.data.submitting) return;
    const code = this.data.code.trim();
    if (!code) {
      this.setData({ error: '请输入验证码' });
      return;
    }
    await this.submit(code, false);
  },

  /**
   * @param {boolean} discardShadowData 用户已确认放弃临时账号里的学习数据
   */
  async submit(code, discardShadowData) {
    this.setData({ submitting: true, error: '' });
    try {
      const result = await api.post('/auth/email/verify', {
        email: this.data.email.trim(),
        code,
        discardShadowData: !!discardShadowData
      });
      // 归并后 userId 变了，必须整份替换本地 token 与用户信息
      auth.persist(result);
      this.setData({
        submitting: false,
        stage: 'idle',
        code: '',
        user: api.getUser() || {}
      });
      if (result.merged) {
        wx.showModal({
          title: '已合并到原账号',
          content: '这个微信现在登录的是你原来的账号，网页端的学习记录都在。',
          showCancel: false
        });
      } else {
        wx.showToast({ title: '邮箱绑定成功', icon: 'success' });
      }
    } catch (error) {
      this.setData({ submitting: false });
      if (error.code === 50512) {
        this.confirmDiscard(error.message);
        return;
      }
      this.setData({ error: error.message || '绑定失败' });
    }
  },

  /** 50512：临时账号已有数据。把「有什么」摆出来，让用户自己决定。 */
  confirmDiscard(message) {
    wx.showModal({
      title: '临时账号里有数据',
      content: message,
      confirmText: '放弃并合并',
      cancelText: '先不合并',
      success: (res) => {
        if (res.confirm) {
          this.submit(this.data.code.trim(), true);
        }
      }
    });
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '退出后需重新用微信登录，账号与数据不受影响。',
      success: (res) => {
        if (res.confirm) auth.logout();
      }
    });
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
