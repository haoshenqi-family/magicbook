/**
 * 生词本：分页列表 + 状态筛选 + 词前缀搜索 + 就地改标记。
 *
 * 数据源 moon-well GET /vocabulary/notebook（R239 新增）。
 * 口径：只展示「有熟悉度标记」的词；查词自动建档（familiarity 为空）不进列表，
 * 否则首屏全是没标记过的词——它们属于查词留痕，不属于生词本。
 */
const api = require('../../utils/api');
const auth = require('../../utils/auth');

const FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'unknown', label: '生词' },
  { key: 'reviewing', label: '复习中' },
  { key: 'mastered', label: '已掌握' }
];

const STATUS_TEXT = { unknown: '生词', reviewing: '复习中', mastered: '已掌握' };
const SOURCE_TEXT = { manual: '手标', dictation: '听写', vocab_test: '测试', lookup: '查词' };

const PAGE_SIZE = 20;

Page({
  data: {
    filters: FILTERS,
    filter: 'all',
    keyword: '',
    items: [],
    counts: { all: 0, unknown: 0, reviewing: 0, mastered: 0 },
    total: 0,
    page: 1,
    hasNext: false,
    loading: false,
    error: '',
    wechatShadow: false
  },

  onShow() {
    if (!auth.ensureLogin()) return;
    // 临时账号提示条：每次回到本页重读，账号页绑定成功后这里要立刻消失
    const user = api.getUser() || {};
    this.setData({ wechatShadow: !!user.wechatShadow });
    this.reload();
  },

  onTapAccount() {
    wx.navigateTo({ url: '/pages/account/account' });
  },

  onPullDownRefresh() {
    this.reload().then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    if (this.data.hasNext && !this.data.loading) {
      this.load(this.data.page + 1);
    }
  },

  reload() {
    return this.load(1);
  },

  async load(page) {
    if (this.data.loading) return;
    this.setData({ loading: true, error: '' });
    try {
      const params = { page, size: PAGE_SIZE, filter: this.data.filter };
      // 空关键词不发：wx.request 会把 undefined 序列化进 query，服务端拿到 "undefined" 反而搜不到
      if (this.data.keyword) params.keyword = this.data.keyword;
      const result = await api.get('/vocabulary/notebook', params);
      const fresh = (result.items || []).map(decorate);
      this.setData({
        items: page === 1 ? fresh : this.data.items.concat(fresh),
        counts: result.counts || this.data.counts,
        total: result.total || 0,
        page: result.page || page,
        hasNext: !!result.hasNext,
        loading: false
      });
    } catch (error) {
      this.setData({ loading: false, error: error.message || '生词本加载失败' });
      api.toastError(error);
    }
  },

  onFilterTap(event) {
    const key = event.currentTarget.dataset.key;
    if (key === this.data.filter) return;
    this.setData({ filter: key, items: [], page: 1, hasNext: false });
    this.load(1);
  },

  onKeywordInput(event) {
    this.setData({ keyword: event.detail.value });
  },

  onSearchConfirm() {
    this.load(1);
  },

  onClearKeyword() {
    this.setData({ keyword: '' });
    this.load(1);
  },

  /** 点词就地改标记：认识 ↔ 生词。写库后重拉当前页，避免本地状态与服务端漂移。 */
  onItemTap(event) {
    const word = event.currentTarget.dataset.word;
    const item = this.data.items.find((entry) => entry.word === word);
    if (!item) return;
    const actions = item.status === 'mastered' ? ['标为生词'] : ['标为认识'];
    wx.showActionSheet({
      itemList: actions,
      success: (res) => {
        const action = item.status === 'mastered'
          ? 'unknown'
          : 'known';
        if (res.tapIndex === 0) this.mark(word, action);
      }
    });
  },

  async mark(word, action) {
    wx.showLoading({ title: '保存中', mask: true });
    try {
      await api.post('/vocabulary/mark', { word, action });
      wx.hideLoading();
      wx.showToast({ title: '已更新', icon: 'success' });
      this.load(1);
    } catch (error) {
      wx.hideLoading();
      api.toastError(error);
    }
  }
});

/** 列表项展示字段在 JS 里算好，WXML 只做绑定（WXS/过滤函数在列表里开销更高）。 */
function decorate(item) {
  return Object.assign({}, item, {
    statusText: STATUS_TEXT[item.status] || '未标记',
    sourceText: item.source ? (SOURCE_TEXT[item.source] || item.source) : '历史',
    encounterText: item.encounterCount ? '遇见 ' + item.encounterCount + ' 次' : '暂无遇见记录',
    lastText: formatDay(item.lastStudyTime)
  });
}

function formatDay(value) {
  if (!value) return '';
  // LocalDateTime 序列化为 "2026-11-03T09:12:33"；只保留日期
  const text = String(value);
  return text.length >= 10 ? text.slice(0, 10) : text;
}
