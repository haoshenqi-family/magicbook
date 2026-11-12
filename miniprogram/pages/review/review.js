/**
 * 每日复习：到期队列 + 四档自评。
 *
 * 后端：GET /vocabulary/review/queue?limit → POST /vocabulary/review/answer → GET /vocabulary/review/stats
 *
 * 题型口径（与网页端 learning-review.js 对齐）：
 * - CHOOSE（四选一）：题干是中文释义，选项是词；选中即亮答案，再由用户自评四档；
 * - SPELL（拼写）：题干是释义，输入拼写，客户端按「trim + 小写 + 弯撇号归一」比对；
 * - RECALL（回忆）：题干同样是中文释义，自己回想后揭示词面，再自评；
 * - SELF（自评，释义缺失时的兜底）：没有题干就直接亮词面按印象自评，绝不出白板卡。
 * 判对错不代替自评：SRS 的 grade 决定下次出现时间，「选对了但没想起来」和
 * 「真轻松」必须分开，所以任何题型最后都落在 1–4 四档上。
 *
 * 听辨题型（LISTEN_*）在本期不支持：音频端点要带 JWT 头，小程序的 audio 组件无法
 * 自定义请求头。后端 R238 起默认停出这四个题型，队列里正常不会出现；万一出现按
 * 「回忆 / 自评」降级，不会出哑题。
 */
const api = require('../../utils/api');
const auth = require('../../utils/auth');
const reviewCard = require('../../utils/review-card');

const QUEUE_LIMIT = 20;
const GRADES = [
  { grade: 1, label: '忘记', hint: '完全想不起来' },
  { grade: 2, label: '很难', hint: '想起来但很吃力' },
  { grade: 3, label: '想起', hint: '想起来了' },
  { grade: 4, label: '轻松', hint: '毫不费力' }
];

Page({
  data: {
    phase: 'idle',
    stats: null,
    queue: [],
    index: 0,
    card: null,
    mode: 'SELF',
    modeLabel: '自评',
    stem: '',
    stemCloze: false,
    revealed: false,
    chosen: '',
    spellInput: '',
    spellCorrect: null,
    grades: GRADES,
    answered: 0,
    submitting: false,
    loading: false,
    error: ''
  },

  onShow() {
    if (!auth.ensureLogin()) return;
    // 每次回到本页都刷统计：可能在网页端复习过，进度不该是小程序里的旧快照
    this.loadStats();
  },

  async loadStats() {
    try {
      const stats = await api.get('/vocabulary/review/stats');
      this.setData({ stats: decorateStats(stats) });
    } catch (error) {
      this.setData({ error: error.message || '统计加载失败' });
    }
  },

  async onTapStart() {
    if (this.data.loading) return;
    this.setData({ loading: true, error: '' });
    try {
      const queue = await api.get('/vocabulary/review/queue', { limit: QUEUE_LIMIT });
      if (!queue || !queue.length) {
        this.setData({ loading: false, phase: 'done', queue: [], index: 0, answered: 0, card: null });
        return;
      }
      this.setData({ loading: false, queue, index: 0, answered: 0 });
      this.showCard(0);
    } catch (error) {
      this.setData({ loading: false, error: error.message || '队列加载失败' });
      api.toastError(error);
    }
  },

  showCard(index) {
    const raw = this.data.queue[index];
    if (!raw) {
      this.finish();
      return;
    }
    // 计时起点：作答耗时进调度参数，从卡片出现开始算（不 setData，避免无谓渲染）
    this.answeredAt = Date.now();
    const presented = reviewCard.presentCard(raw);
    this.setData({
      phase: 'card',
      index,
      card: raw,
      mode: presented.mode,
      modeLabel: presented.label,
      stem: presented.stem,
      stemCloze: presented.cloze,
      revealed: false,
      chosen: '',
      spellInput: '',
      spellCorrect: null
    });
    wx.pageScrollTo({ scrollTop: 0, duration: 120 });
  },

  onChoiceTap(event) {
    if (this.data.revealed) return;
    this.setData({ chosen: event.currentTarget.dataset.choice, revealed: true });
  },

  onReveal() {
    this.setData({ revealed: true });
  },

  onSpellInput(event) {
    this.setData({ spellInput: event.detail.value });
  },

  onSpellCheck() {
    const typed = (this.data.spellInput || '').trim();
    if (!typed) return;
    const expected = this.data.card && this.data.card.word;
    this.setData({ revealed: true, spellCorrect: normalize(typed) === normalize(expected) });
  },

  async onGradeTap(event) {
    if (this.data.submitting) return;
    const grade = Number(event.currentTarget.dataset.grade);
    if (!grade) return;
    const card = this.data.card;
    if (!card) return;

    this.setData({ submitting: true });
    const payload = { scheduleId: card.scheduleId, grade };
    // 回传后端当初下发的题型（不是本地降级后的呈现态）：它进 word_event，是四技能统计的底座
    if (card.questionType) payload.questionType = card.questionType;
    const latency = Date.now() - (this.answeredAt || Date.now());
    if (latency > 0) payload.latencyMs = Math.min(latency, 300000);

    try {
      await api.post('/vocabulary/review/answer', payload);
      const next = this.data.index + 1;
      this.setData({ submitting: false, answered: this.data.answered + 1 });
      if (next >= this.data.queue.length) {
        this.finish();
      } else {
        this.showCard(next);
      }
    } catch (error) {
      this.setData({ submitting: false });
      api.toastError(error);
    }
  },

  finish() {
    this.setData({ phase: 'done', card: null, queue: [] });
    this.loadStats();
  },

  onExit() {
    this.setData({ phase: 'idle', card: null, queue: [], index: 0, answered: 0 });
  }
});

/**
 * 呈现态判定见 utils/review-card.js（纯函数，Node 可直接跑真代码验证）。
 * 这里只保留与提交口径有关的纯工具：拼写归一与统计装饰。
 */

function normalize(text) {
  return String(text || '')
    .trim()
    .toLowerCase()
    .replace(/’/g, "'");
}

function decorateStats(stats) {
  if (!stats) return null;
  const target = stats.todayTarget || 0;
  const reviewed = stats.todayReviewed || 0;
  const percent = target > 0 ? Math.min(100, Math.round((reviewed / target) * 100)) : 0;
  return Object.assign({}, stats, {
    percent,
    progressText: reviewed + ' / ' + target,
    retentionText: stats.retention7d == null ? '—' : stats.retention7d + '%'
  });
}
