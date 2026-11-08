# 每日复习（miniprogram）· 实现说明（L3）

> 读者：要改小程序复习卡的人。只讲「这一页怎么实现 + 边界在哪」；
> 需求见 [需求基线 §R271](../requirements.md)，接口契约见 [L2](../interface.md) §5，
> 本次修复见 [R290 LLD](../../project/iterations/2026-11-wx-review-card/r290-review-card-stem/lld.md)。

## 1. 数据面

`pages/review` 只调三个后端端点（moon-well，直连、不带 magicbook 代理）：

| 用途 | 端点 |
| --- | --- |
| 到期队列 | `GET /vocabulary/review/queue?limit=20` |
| 作答 | `POST /vocabulary/review/answer`（`scheduleId` / `grade` / `questionType` / `latencyMs`） |
| 统计 | `GET /vocabulary/review/stats` |

队列项的字段口径以 moon-well `LearningReviewItemVO` 为准。本页用到的：

| 字段 | 用途 |
| --- | --- |
| `questionType` | 后端下发的题型；作答时**原样回传**，它是四技能统计与保持率的底座 |
| `word` | 词面（答案本身，揭示后才亮） |
| `meaning` | 中文短释义，**就是题干**；详解缓存未命中时为 `null` |
| `choices` / `answer` | 选择题选项与正确项（`DISCRIMINATE` 的正确项不是 `word`） |
| `contextClozeSentence` | 语境挖空句，`CONTEXT_CLOZE` 的题干 |
| `contextSentence` / `contextBook` / `contextChapter` | 语境卡；原句含目标词，**揭示前不渲染** |
| `encounterCount` | 「在阅读中遇见过 N 次」 |

## 2. 呈现态判定（`utils/review-card.js`）

题型到「这一张怎么问」的映射是纯函数 `presentCard(card)`，不碰任何 `wx` API，
因此可以在 Node 里跑真代码验证（`tests/test_r290_review_card_stem.py`）。

| 条件（按顺序） | 呈现态 | 题干 |
| --- | --- | --- |
| `CHOOSE` / `DISCRIMINATE` 且有释义且 `choices.length ≥ 2` | 四选一 | `meaning` |
| `SPELL` 且有释义 | 拼写 | `meaning` |
| `CONTEXT_CLOZE` 且有挖空句 | 回忆（挖空样式） | `contextClozeSentence` |
| 其余**有释义** | 回忆 | `meaning` |
| 以上都不满足 | 自评 | 无（直接亮词面） |

返回 `{ mode, label, stem, cloze }`：`mode` 决定 WXML 分支，`label` 是右上角题型标签，
`stem` 是题干原文，`cloze` 决定题干是否走 `.cloze` 样式。

### 边界条件

- **释义缺失绝不硬出题**：后端契约是缓存未命中 `meaning=null`，此时不编题干、不出现空卡，
  改为「自评」——亮词面，让用户凭印象打分。这条与网页端 `learning-review.js` 的 `SELF` 降级同口径。
- **选择题降级不丢题干**：选项不足（后端 `choices=null`）时降为回忆，题干仍是释义。
- **未知题型不产生死卡**：题型不认识但有释义就按回忆出，没有释义就自评。
- **回传的题型不随降级变化**：`answer` 带的是 `card.questionType` 原值，不是本地 `mode`。
  `SELF` 后端不认识，但缺失时后端会按该词历史重算。
- **语境卡门控**：`contextSentence` 含目标词，只在 `revealed` 或 `SELF` 时渲染（R137 泄题门控）。
- **拼写卡也给「揭示答案」**：想不起来的人必须走得掉，不能被卡在输入框上。

## 3. 历史缺陷（R290）

首版把题干只挂在「四选一 / 拼写」两个分支上，`RECALL` 落进 `wx:else` 的一句提示语
「看下面的提示，回想这个词」，而 `meaning` 从未被渲染——**每一张回忆卡都没有题面**；
释义缺失时提示语、释义、词面三者全不出现，卡片是一块白板（用户截图即此形态）。
修法见上表，并新增静态锁与 Node 断言钉住「任何队列项都必须露出题干或词面之一」。
