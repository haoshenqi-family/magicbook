/**
 * 学习数据：今日四股预算与入账 + 复习摘要 + 近 7 天走势 + 最近一次词汇量。
 *
 * 数据源（全部只读）：
 *   GET /learning/plan/today        四股预算与今日已入账
 *   GET /vocabulary/review/stats    复习摘要（到期/今日/明日/掌握/保持率）
 *   GET /learning/strands/summary   近 7 天逐日四股
 *   GET /vocabulary/test/history    最近一次词汇量
 *
 * Why 四个请求各自 try：任一接口降级（ES 抖动、词表重载）不该让整页白屏；
 * 但失败的那一块必须在界面上写明「加载失败」，不能显示成 0 或「暂无数据」。
 */
const api = require('../../utils/api');
const auth = require('../../utils/auth');

const STRANDS = [
  { key: 'input', name: '阅读输入', color: '#2f6fed' },
  { key: 'language', name: '词汇学习', color: '#15803d' },
  { key: 'output', name: '说与写', color: '#b45309' },
  { key: 'fluency', name: '流利度', color: '#7c3aed' }
];

Page({
  data: {
    user: null,
    strands: [],
    srs: null,
    week: [],
    weekMeta: null,
    latestTest: null,
    errors: {},
    loading: false
  },

  onShow() {
    if (!auth.ensureLogin()) return;
    this.setData({ user: api.getUser() });
    this.loadAll();
  },

  /** 账号与绑定：放在页尾，绑定成功后返回本页会重读 user（onShow）。 */
  onTapAccount() {
    wx.navigateTo({ url: '/pages/account/account' });
  },

  onPullDownRefresh() {
    this.loadAll().then(() => wx.stopPullDownRefresh());
  },

  async loadAll() {
    this.setData({ loading: true });
    const errors = {};
    const [plan, srs, week, history] = await Promise.all([
      api.get('/learning/plan/today').catch((e) => { errors.plan = e.message; return null; }),
      api.get('/vocabulary/review/stats').catch((e) => { errors.srs = e.message; return null; }),
      api.get('/learning/strands/summary', { days: 7 }).catch((e) => { errors.week = e.message; return null; }),
      api.get('/vocabulary/test/history', { limit: 1 }).catch((e) => { errors.test = e.message; return null; })
    ]);

    this.setData({
      loading: false,
      errors,
      strands: buildStrands(plan),
      srs: decorateSrs(srs),
      week: buildWeek(week),
      weekMeta: buildWeekMeta(week),
      latestTest: history && history.length ? decorateTest(history[0]) : null
    });
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '退出后需重新用微信登录（无需再输密码）。',
      success: (res) => {
        if (res.confirm) auth.logout();
      }
    });
  }
});

function buildStrands(plan) {
  const budget = (plan && plan.strands) || {};
  return STRANDS.map((strand) => {
    const planned = budget[strand.key + 'Minutes'] || 0;
    const earnedRaw = budget[strand.key + 'EarnedMinutes'];
    const earned = earnedRaw == null ? null : Math.round(earnedRaw * 10) / 10;
    return {
      key: strand.key,
      name: strand.name,
      color: strand.color,
      planned,
      earned,
      earnedText: earned == null ? '统计暂不可用' : earned + ' 分钟',
      // 预算为 0 时不出进度条，避免「0/0 = 100%」的假满格
      percent: planned > 0 && earned != null ? Math.min(100, Math.round((earned / planned) * 100)) : 0
    };
  });
}

function decorateSrs(srs) {
  if (!srs) return null;
  const target = srs.todayTarget || 0;
  const reviewed = srs.todayReviewed || 0;
  return Object.assign({}, srs, {
    progressText: reviewed + ' / ' + target,
    percent: target > 0 ? Math.min(100, Math.round((reviewed / target) * 100)) : 0,
    retentionText: srs.retention7d == null ? '—' : srs.retention7d + '%'
  });
}

function buildWeek(days) {
  const rows = Array.isArray(days) ? days.slice(-7) : [];
  if (!rows.length) return [];
  const totals = rows.map((day) => STRANDS.reduce((sum, s) => sum + (day[s.key + 'Minutes'] || 0), 0));
  const max = Math.max.apply(null, totals.concat([1]));
  return rows.map((day, index) => ({
    date: day.date,
    label: shortDate(day.date),
    totalText: Math.round(totals[index] * 10) / 10 + ' 分钟',
    segs: STRANDS.map((strand) => {
      const minutes = day[strand.key + 'Minutes'] || 0;
      return {
        key: strand.key,
        color: strand.color,
        width: Math.round((minutes / max) * 100),
        minutes
      };
    }).filter((seg) => seg.width > 0)
  }));
}

function buildWeekMeta(days) {
  const rows = Array.isArray(days) ? days : [];
  const total = rows.reduce((sum, day) => {
    return sum + STRANDS.reduce((inner, s) => inner + (day[s.key + 'Minutes'] || 0), 0);
  }, 0);
  return { totalText: Math.round(total * 10) / 10 };
}

function decorateTest(report) {
  const finished = report.finishedAt ? String(report.finishedAt).slice(0, 10) : '';
  return {
    sizeText: report.estimatedSize == null ? '—' : String(report.estimatedSize).replace(/\B(?=(\d{3})+(?!\d))/g, ','),
    rangeText: report.ciLow + ' – ' + report.ciHigh,
    dateText: finished
  };
}

function shortDate(value) {
  const text = String(value || '');
  return text.length >= 10 ? text.slice(5) : text;
}
