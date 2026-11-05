/**
 * 词汇量测试：自适应出题（只答认识/不认识）→ 交卷 → 报告。
 *
 * 后端：/vocabulary/test/{start,answer,finish,history}（-well），题目由服务端按 seq 定位，
 * 客户端不回传词面——所以「答了哪个词」不是客户端说了算。
 *
 * 四个阶段（phase）：
 *   idle     说明 + 历史
 *   question 逐题作答
 *   submit   估已完成：勾选是否把不认识的词收进网页端生词本，再交卷
 *   report   估算值/区间/各频段/推荐难度（可一键应用）
 *
 * Why 有 submit 这一阶段而不是自动交卷：把「不认识」的词写进网页端生词本是一个有副作用的
 * 决定（会进入复习队列），必须在用户看得见的地方确认一次。
 */
const api = require('../../utils/api');
const auth = require('../../utils/auth');

Page({
  data: {
    phase: 'idle',
    loading: false,
    error: '',
    sessionId: null,
    question: null,
    progress: null,
    estimation: null,
    addUnknown: true,
    report: null,
    applied: false,
    history: []
  },

  onShow() {
    if (!auth.ensureLogin()) return;
    if (this.data.phase === 'idle') this.loadHistory();
  },

  async loadHistory() {
    try {
      const history = await api.get('/vocabulary/test/history', { limit: 5 });
      this.setData({ history: (history || []).map(decorateHistory) });
    } catch (error) {
      // 历史只是辅助信息：失败时把错误显式写出来，不静默当成「没有记录」
      this.setData({ error: error.message || '历史成绩加载失败' });
    }
  },

  async onTapStart() {
    if (this.data.loading) return;
    this.setData({ loading: true, error: '', report: null, applied: false, estimation: null });
    try {
      const result = await api.post('/vocabulary/test/start', {});
      this.setData({
        loading: false,
        phase: 'question',
        sessionId: result.sessionId,
        question: result.question,
        progress: decorateProgress(result.progress)
      });
    } catch (error) {
      this.setData({ loading: false, error: error.message || '测试开始失败' });
      api.toastError(error);
    }
  },

  onTapKnown() {
    this.submitAnswer(1);
  },

  onTapUnknown() {
    this.submitAnswer(0);
  },

  async submitAnswer(answer) {
    if (this.data.loading || !this.data.question) return;
    this.setData({ loading: true, error: '' });
    try {
      const result = await api.post('/vocabulary/test/answer', {
        sessionId: this.data.sessionId,
        seq: this.data.question.seq,
        answer
      });
      if (result.finished) {
        this.setData({
          loading: false,
          phase: 'submit',
          progress: decorateProgress(result.progress),
          estimation: result.estimation
        });
        return;
      }
      this.setData({
        loading: false,
        question: result.question,
        progress: decorateProgress(result.progress)
      });
    } catch (error) {
      this.setData({ loading: false, error: error.message || '作答失败' });
      api.toastError(error);
    }
  },

  onSwitchChange(event) {
    this.setData({ addUnknown: event.detail.value });
  },

  async onTapFinish() {
    if (this.data.loading || !this.data.sessionId) return;
    this.setData({ loading: true, error: '' });
    try {
      const report = await api.post('/vocabulary/test/finish', {
        sessionId: this.data.sessionId,
        addUnknownToNotebook: this.data.addUnknown
      });
      this.setData({
        loading: false,
        phase: 'report',
        report: decorateReport(report),
        sessionId: null,
        question: null
      });
      this.loadHistory();
    } catch (error) {
      this.setData({ loading: false, error: error.message || '交卷失败' });
      api.toastError(error);
    }
  },

  async onApplyRecommended() {
    const level = this.data.report && this.data.report.recommendedHardLevel;
    if (level == null || this.data.applied) return;
    try {
      await api.post('/vocabulary/reading/settings/hard-level', { hardLevel: level });
      this.setData({ applied: true });
      wx.showToast({ title: '已应用难度', icon: 'success' });
    } catch (error) {
      api.toastError(error);
    }
  },

  onTapRetake() {
    this.setData({
      phase: 'idle',
      report: null,
      applied: false,
      estimation: null,
      question: null,
      progress: null
    });
    this.loadHistory();
  },

  onCancelTest() {
    // 会话不主动作废：服务端 30 分钟懒作废，重开就是新会话
    this.setData({ phase: 'idle', sessionId: null, question: null, progress: null });
  }
});

function decorateProgress(progress) {
  if (!progress) return null;
  return Object.assign({}, progress, {
    answeredText: (progress.answered || 0) + ' 题已答 · 认识 ' + (progress.known || 0) + ' 个'
  });
}

function decorateReport(report) {
  if (!report) return null;
  return Object.assign({}, report, {
    rangeText: report.ciLow + ' – ' + report.ciHigh,
    sizeText: formatNumber(report.estimatedSize),
    bandRows: (report.bandResults || []).map((band) => ({
      band: band.band,
      known: band.known,
      questions: band.questions,
      rateText: Math.round((band.rate || 0) * 100) + '%',
      width: Math.max(2, Math.round((band.rate || 0) * 100))
    })),
    typeText: report.testType === 'refine' ? '细筛' : '标准'
  });
}

function decorateHistory(report) {
  const finished = report.finishedAt ? String(report.finishedAt).slice(0, 10) : '';
  return {
    sessionId: report.sessionId,
    sizeText: formatNumber(report.estimatedSize),
    rangeText: report.ciLow + ' – ' + report.ciHigh,
    dateText: finished,
    typeText: report.testType === 'refine' ? '细筛' : '标准'
  };
}

function formatNumber(value) {
  if (value == null) return '—';
  return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
