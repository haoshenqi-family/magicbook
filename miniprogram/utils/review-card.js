/**
 * 复习卡的「呈现态」判定：后端题型 → 这一张到底怎么问。
 *
 * Why 单独成模块：题型降级链是这张卡最容易出错的地方（R290 的 bug 就出在这里），
 * 而它只依赖队列项、不碰 wx 任何 API。抽成纯函数才能在 Node 里直接跑真代码断言，
 * 而不是靠人眼看 WXML 猜。
 *
 * 判定顺序（与网页端 learning-review.js 同口径）：
 *   1. CHOOSE / DISCRIMINATE：有释义**且有 ≥2 个选项**才出四选一；
 *   2. SPELL：有释义才出拼写；
 *   3. CONTEXT_CLOZE：有挖空句就用它当题干；
 *   4. 其余有释义的一律「回忆」——**释义就是题干**，词面揭示后才亮；
 *   5. 什么都没有才退到「自评」：直接亮词面让人凭印象打分。
 *
 * 第 4、5 条是 R290 修的那条：旧实现把「回忆」也塞进「看下面的提示」分支，
 * 而释义只在四选一/拼写两个分支里渲染，于是每张回忆卡都是**没有任何题干的死卡**；
 * 释义缺失时更糟——提示、释义、词面全都不出现，用户对着空气点「揭示答案」。
 * 释义缺失绝不硬出题（后端契约：缓存未命中 meaning=null），但也不能出空卡。
 */

const MODE_LABELS = {
  CHOOSE: '四选一',
  SPELL: '拼写',
  RECALL: '回忆',
  SELF: '自评'
};

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}

/**
 * @param {object} card 队列项（moon-well /vocabulary/review/queue 的一项）
 * @returns {{mode: string, label: string, stem: string, cloze: boolean}}
 *   mode 是本地呈现态；stem 是题干原文（SELF 时为空串）；cloze 决定题干用挖空句样式。
 */
function presentCard(card) {
  const item = card || {};
  const type = item.questionType;
  const meaning = text(item.meaning);
  const choices = Array.isArray(item.choices) ? item.choices : [];
  const clozeSentence = text(item.contextClozeSentence);

  if ((type === 'CHOOSE' || type === 'DISCRIMINATE') && meaning && choices.length >= 2) {
    return build('CHOOSE', meaning, false);
  }
  if (type === 'SPELL' && meaning) {
    return build('SPELL', meaning, false);
  }
  if (type === 'CONTEXT_CLOZE' && clozeSentence) {
    return build('RECALL', clozeSentence, true);
  }
  if (meaning) {
    return build('RECALL', meaning, false);
  }
  // 释义与挖空句都没有：不硬造题干，改亮词面自评（网页端同款兜底）。
  return build('SELF', '', false);
}

function build(mode, stem, cloze) {
  return { mode: mode, label: MODE_LABELS[mode] || MODE_LABELS.RECALL, stem: stem, cloze: cloze };
}

module.exports = {
  presentCard: presentCard,
  MODE_LABELS: MODE_LABELS
};
