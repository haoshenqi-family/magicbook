/**
 * AI 伴读（通用对话，R280）。
 *
 * 契约：moon-well R243 的 POST /ai/agent/chat（SSE）。请求必须带 scene='general'
 * 才能加载 agent-chat-system-general 通用 prompt；请求体里不带任何书籍/网页上下文
 * 字段，因为小程序里没有书也没有网页正文，传了只会让模板渲染出「未知书名」这类假上下文。
 *
 * 事件协议（与网页端 ai_chat.js 同源）：delta 增量正文、final 会话 id 与用量、
 * error 业务错误；tool_call/tool_result/audio 小程序不展示工具轨迹，只用 tool_call
 * 把「正在思考」换成「正在查证」。
 *
 * skipMemoryExtract=true：通用闲聊默认不写长期记忆，与网页场景隐私口径一致；
 * 伙伴仍会按用户明确要求用 save_memory 记笔记（那是模型工具，不受此开关影响）。
 */
const api = require('../../utils/api');
const auth = require('../../utils/auth');

const KEY_CONVERSATION = 'mb.chat.conversationId';
const SUGGESTIONS = [
  '这个词怎么用在句子里？',
  '帮我挑一本适合现在的英文书',
  '今天该练点什么英语？'
];

Page({
  data: {
    messages: [],
    input: '',
    sending: false,
    conversationId: null,
    scrollTo: '',
    suggestions: SUGGESTIONS,
    error: ''
  },

  onLoad() {
    this.seq = 0;
    this.task = null;
    const saved = wx.getStorageSync(KEY_CONVERSATION);
    if (saved) this.setData({ conversationId: saved });
  },

  onShow() {
    auth.ensureLogin();
  },

  onUnload() {
    // 页面销毁时掐断流，避免后台继续收 delta 并给已卸载的页面 setData
    if (this.task) this.task.abort();
  },

  onInput(event) {
    this.setData({ input: event.detail.value });
  },

  onTapSuggestion(event) {
    if (this.data.sending) return;
    const text = event.currentTarget.dataset.text || '';
    if (!text) return;
    this.setData({ input: text });
    this.onSend();
  },

  appendMessage(role, content, status) {
    const id = ++this.seq;
    const messages = this.data.messages.concat([{
      id,
      role,
      content: content || '',
      status: status || 'done',
      error: ''
    }]);
    this.setData({ messages, scrollTo: 'msg-' + id });
    return id;
  },

  patchMessage(id, patch) {
    const index = this.data.messages.findIndex((item) => item.id === id);
    if (index < 0) return;
    const data = {};
    Object.keys(patch).forEach((key) => {
      data['messages[' + index + '].' + key] = patch[key];
    });
    this.setData(data);
  },

  contentOf(id) {
    const found = this.data.messages.find((item) => item.id === id);
    return found ? found.content : '';
  },

  onSend() {
    if (this.data.sending) return;
    const text = (this.data.input || '').trim();
    if (!text) return;

    this.setData({ input: '', sending: true, error: '' });
    this.streamError = '';
    this.appendMessage('user', text, 'done');
    const replyId = this.appendMessage('assistant', '', 'thinking');

    this.task = api.chatStream({
      conversationId: this.data.conversationId || null,
      message: text,
      scene: 'general',
      skipMemoryExtract: true
    }, {
      onEvent: (name, data) => this.onStreamEvent(name, data, replyId),
      onDone: () => {
        this.task = null;
        this.setData({ sending: false });
        if (!this.contentOf(replyId)) {
          this.patchMessage(replyId, {
            status: 'error',
            error: this.streamError || '这次没有收到回复，请重试'
          });
        } else {
          this.patchMessage(replyId, { status: 'done' });
        }
      },
      onError: (message) => {
        this.task = null;
        this.setData({ sending: false, error: message });
        this.patchMessage(replyId, { status: 'error', error: message });
        wx.showToast({ title: message, icon: 'none', duration: 2600 });
      }
    });
  },

  onStreamEvent(name, data, replyId) {
    const payload = data || {};
    if (name === 'delta') {
      const piece = payload.text || payload.data || '';
      if (!piece) return;
      this.patchMessage(replyId, { content: this.contentOf(replyId) + piece, status: 'streaming' });
      this.setData({ scrollTo: 'msg-' + replyId });
      return;
    }
    if (name === 'tool_call') {
      if (!this.contentOf(replyId)) this.patchMessage(replyId, { status: 'tool' });
      return;
    }
    if (name === 'final') {
      if (payload.conversationId) {
        wx.setStorageSync(KEY_CONVERSATION, payload.conversationId);
        this.setData({ conversationId: payload.conversationId });
      }
      return;
    }
    if (name === 'error') {
      const message = payload.message || 'AI 服务暂时不可用';
      this.streamError = message;
      this.setData({ error: message });
      this.patchMessage(replyId, { status: 'error', error: message });
      wx.showToast({ title: message, icon: 'none', duration: 2600 });
    }
    // tool_result / audio：小程序不渲染工具轨迹，也不自动播放音频（避免后台出声）
  },

  onNewChat() {
    if (this.data.sending) {
      wx.showToast({ title: '等这条回答结束再开新会话', icon: 'none' });
      return;
    }
    wx.showModal({
      title: '开始新会话',
      content: '当前对话会从界面清掉；历史仍保存在账号里，可在网页端查看。',
      confirmText: '开始',
      success: (res) => {
        if (!res.confirm) return;
        wx.removeStorageSync(KEY_CONVERSATION);
        this.setData({ messages: [], conversationId: null, input: '', error: '', scrollTo: '' });
      }
    });
  }
});
