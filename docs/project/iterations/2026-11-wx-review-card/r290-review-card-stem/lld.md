# LLD · R290 小程序每日复习页空题面死卡

- **状态**：开发中（代码与验证已完成，待 PR 评审与真机复核；见 §6）
- **迭代**：2026-11 小程序复习卡　**需求编号**：R290（用户 2026-11-08 截图报障）
- **影响范围**：`magicbook/miniprogram/pages/review/*`、新增 `miniprogram/utils/review-card.js`
- **后端**：零改动（moon-well 契约不变，`LearningReviewItemVO` 照旧下发 `meaning`）

## 1. 现象

用户 2026-11-08 15:36 在小程序「每日复习」页截图（`evidence/user-report.jpg`）：

- 统计卡正常（到期 3878 / 明日到期 1 / 复习中 8 / 已掌握 127 / 保持率 25%）；
- 卡片区只有一行灰字「看下面的提示，回想这个词」+ 一个「揭示答案」按钮；
- **没有任何题面**，也没有提示内容。用户没有可回想的东西，只能盲点。

## 2. 根因

`pages/review/review.wxml` 旧实现把题干只挂在两个分支上：

```
<view wx:if="{{mode === 'CHOOSE' || mode === 'SPELL'}}" class="prompt">{{card.meaning}}</view>
<view wx:elif="{{card.contextClozeSentence}}" class="prompt cloze">{{card.contextClozeSentence}}</view>
<view wx:else class="prompt muted">看下面的提示，回想这个词</view>
```

而 `pages/review/review.js` 的 `pickMode` 只对 `CHOOSE` / `SPELL` 返回具体题型，
其余（`RECALL`、`CONTEXT_CLOZE`、`LISTEN_*`、未知题型）**一律返回 `SELF`**。

两层叠起来的后果：

1. **`RECALL` 卡必然没有题干**。`RECALL` 是后端自适应策略的默认档位
   （`QuestionTypePicker.adaptive` 无历史即 `CHOOSE`，但降档与 legacy 梯度都会落到 `RECALL`），
   后端下发的 `meaning` 就在手里，前端却从未渲染它——落进 `wx:else` 只显示一句提示语。
2. **`SELF` 降级没有出口**。`SELF` 分支不渲染词面（词面只在 `revealed` 之后出现），
   所以「没有题干 + 没有词面」= 一块白板。用户截图正是这一形态：连 `meaning` 都没有的词，
   提示语之外什么都没有。
3. **`contextClozeSentence` 形同虚设**：`pickMode` 对 `CONTEXT_CLOZE` 返回 `SELF`，
   挖空句分支永远进不去（虽然 R238 起后端默认停出该题型，但开关放开后就是死卡）。

对照网页端 `cps/static/js/learning-review.js`：它把 `SELF` 当作**呈现态**而不是题型，
`RECALL` 保留释义当题干、揭示后才亮词面；`SELF` 时直接亮词面并给评分。小程序缺的就是这一层。

## 3. 修法

### 3.1 判定抽成纯函数

新增 `miniprogram/utils/review-card.js#presentCard(card)`，与网页端同口径：

| 条件（按顺序） | mode | 题干 |
| --- | --- | --- |
| `CHOOSE` / `DISCRIMINATE` + 释义 + ≥2 选项 | `CHOOSE` | 释义 |
| `SPELL` + 释义 | `SPELL` | 释义 |
| `CONTEXT_CLOZE` + 挖空句 | `RECALL`（挖空样式） | 挖空句 |
| 其余有释义 | `RECALL` | 释义 |
| 都不满足 | `SELF` | 无（亮词面自评） |

返回 `{ mode, label, stem, cloze }`。抽成纯函数的**理由是可验证性**：它不依赖 `wx`，
Node 能直接 `require` 真代码跑断言；留在 `Page({...})` 里就只能靠人眼看模板。

### 3.2 模板改为渲染统一题干

- 题干只从 `stem` 出，`stemCloze` 决定 `.cloze` 样式；删掉「看下面的提示」这句遮羞布。
- 词面与语境按 `revealed || mode === 'SELF'` 控制显隐——既不泄题，也不出白板。
- 题型标签改用 `modeLabel`（去掉三层三元嵌套）。
- 「揭示答案」对 `RECALL` 与 `SPELL` 都给：拼写卡卡在输入框上同样无路可走。
- 评分区对 `revealed || mode === 'SELF'` 出现：`SELF` 无需揭示即可自评。

### 3.3 不做的事

- 不碰后端题型策略、不补生成释义（那会消耗积分，且违反「只读缓存」口径）。
- 不改 `answer` 回传的 `questionType`（仍回后端原值，不随本地降级）。
- 不动统计卡、完成态、登录与请求层。

## 4. 验证

### 4.1 自动化

- `tests/test_r290_review_card_stem.py`（4 例）：
  1. Node 跑 `presentCard` 的 11 组输入矩阵（含释义缺失、选项不足、未知题型、空白释义）；
  2. Node 断言**任何队列项都必须露出题干或词面之一**（防回归到白板卡）；
  3. WXML 静态锁：不得再出现「看下面的提示」、题干只从 `stem` 渲染、揭示按钮覆盖 `RECALL`/`SPELL`；
  4. 页面静态锁：呈现态判定只在 `utils/review-card.js` 一处，`pickMode` 不得回来。
- 小程序既有静态锁全绿：`test_r271`/`r272`/`r273`/`r274`/`r275`/`r276`/`r277`/`r278`/
  `r280`/`r281`/`r282`/`r283` 合计 **54 passed**，加本文件 4 例共 **58 passed**。
- `node --check` 覆盖 `review.js` 与 `review-card.js`；全部 `.json` 过 `JSON.parse`。

### 4.2 视觉证据（真模板 + 真样式）

小程序不在容器里跑、本机无微信开发者工具，所以证据走「真代码渲染」而不是手绘 mockup：

1. `before` 取自 `origin/develop`（`38dfb494`）的 `miniprogram/` 整棵树，`after` 取本轮工作区；
2. 用 `miniprogram-simulate`（微信官方模板编译器 `wcc` + `j-component`）渲染**仓库里的 WXML**；
3. 用 `driver.js` 加载**真实的 `review.js`**（替换 `wx`/`Page` 运行时）跑 `showCard`，
   把 `setData` 之后的 data 交给模板——两边跑同一份队列项，差异只可能来自代码；
4. 套上仓库里的 `app.wxss` + `review.wxss`（`rpx→px`、`page{}`→`body{}`），
   无头 Chrome 以 375×760 @3x 截图；状态栏/导航栏/tabBar 是两边共用的静态壳。

证据图（`evidence/`）：

| 文件 | 场景 |
| --- | --- |
| `user-report.jpg` | 用户原始截图（症状） |
| `before-after-recall.png` | `RECALL` + 有释义：左「只有提示语」，右「释义即题干」 |
| `before-after-no-meaning.png` | 缺释义：左「整张卡空白」，右「亮词面自评」 |
| `before-after-recall-revealed.png` | 揭示后：两边都亮词面与语境，右侧题干仍在 |
| `before-after-choose.png` | 四选一无回归（前后一致） |

### 4.3 未做

- **未真机/未在微信开发者工具编译**（本机没有该工具，历史条目 R271–R283 同样如此）。
  截图来自真实 WXML 的官方模板编译产物 + 真 WXSS，与真机的差异只在系统字体与安全区。
- 未做真机 `wx.pageScrollTo` 与输入法聚焦验证（本轮未改这两处）。

## 5. 边界与风险

- **`SELF` 卡的语义**：直接亮词面自评，意味着这个词这一轮等于「看一眼再打分」，
  比有题干时更轻。这是「宁可不考也不出白板」的取舍，与网页端一致；
  根上要减少 `SELF` 需要让详解缓存命中率上升（内容生产侧，不在本轮）。
- **`SELF` 回传 `questionType` 仍是后端原值**（如 `RECALL`），后端据此算档位；
  前端降级不改变调度口径，这是 R271 定下的边界，未动。
- 历史 `LISTEN_*` 仍不支持（音频端点要 JWT 头），降级为回忆/自评，行为与改前一致。

## 6. 文档四问

1. 用户可见能力变了吗 → L1 `docs/product/readme/miniprogram.md` 复习段补「题干来源 + 缺释义时自评」；
2. 对外行为 / 接口变了吗 → 接口零变化（L2 无需改）；
3. 实现方式 / 边界条件变了吗 → 新建 L3 `docs/product/miniprogram/features/review.md`；
4. 这次怎么实现 → 本 LLD。
