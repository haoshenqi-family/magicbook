# LLD · R284 恢复生词 hover 释义 + 页面引导入口下线

- 状态：**已上线待验收**（2026-11-06 11:11 push `48030f33` 触发 fnOS 部署；worktree `../magicbook-r284-hover-gloss-onboarding`）
- 关联需求：R284（修改意见；挂 R268 生词波浪线 / R226 引导入口的后续，按治理不新建 PingCode idea）
- 目标仓：magicbook（纯前端 + i18n + 文档，moon-well 零改动）

## 1. 现象与定位

用户 2026-11-06 截图（BBC 6 Minute English 双栏）反馈「这个 bug 又回来了」：
生词有橙色波浪线，鼠标悬停只出现问号光标，没有任何释义，也没有划词翻译。

核查结论**不是代码回退**：线上 `reader-core.js` 与 `origin/develop@3413afa0`
sha256 一致（`c9b4765c…`），R268 注入的两行样式仍在。真实成因是两件事叠加：

1. R42（2026-09-15）把 `span.title`（悬停 tooltip）与点击 `alert` 下线，理由是
   「释义 + 上次：书 · 章节」整串太长；R261 把残留注释也删掉，改成默认关闭的
   行内 gloss 小字。R139 又从 moon-well VO 移除了 `translation` 死字段，
   R236 才补上 `gloss`（词典中文首义项）。
2. R268（11-02）把「波浪线 + `cursor:help` + hover 橙底」整套写进
   `READER_TOOLS_STYLE` 注入 EPUB iframe。父页 `reader.css` 本来就有
   `cursor:help`（8/12 起），但父页 CSS 不跨文档；注入后问号光标随波浪线
   一起重新可见，于是 hover 变成「只有问号、没有内容」。

用户拍板：①恢复 hover 释义；②页面上的引导入口全部下线，只留右上角 Help。

## 2. 实现

**A. hover 释义**（`cps/static/js/reading/epub.js` `markVocabulary`）

```js
if (record.gloss) span.title = record.gloss;
```

- 数据源用 R236 的 `gloss`，不复活 R139 删除的 `translation`；不拼历史书名/章节，
  避免 R42 当初嫌长的整串回来。
- `gloss` 为 null（词典无文档）时不设 `title`，只留波浪线，不制造空/假释义。
- 原生 `title` 由浏览器渲染，不依赖父页 CSS，iframe 内可见；与 R146
  划词气泡让位、R261 行内小字开关（只管 `data-gloss`）互不影响。

**B. 引导入口下线**

| 位置 | 处置 |
| --- | --- |
| `layout.html` 右上角 Help → `#top_onboarding` | **保留，唯一入口**（R269 后该下拉本来就只有这一项） |
| `onboarding.js` `runSegment` | 只保留断点续览；不再 `showInvite`、不再 `showReaderHelp` |
| `onboarding.js` `showEntryAgainIfNeeded` | 留空，导览 finish/dismiss 不再挂回右下按钮 |
| `reading_settings.html` | 删 `<section class="reading-onboarding">` |
| `reading-preferences.js` | 删 `#reading-onboarding-start` 点击转发 |
| `read.html` | **保留** `onboarding_mount.html` include：右上角 Help 启动的导览仍需跨页续到阅读器段 |
| `onboarding.js` `showInvite` / `showReaderHelp` 函数体 | 保留但不再调用（R111/R226 视觉守卫仍锁其几何与文案形制） |

**C. 文案同源**（`i18n_seed.html` + `zh_Hans_CN` po/mo + `onboarding.js`）
收尾卡由「右下角按钮」改为 `Open Help in the top-right corner to replay this tour.`
（中文「随时从右上角「帮助」重看本段导览。」），只重编译 zh_Hans_CN 的 mo。

## 3. 验证

- 新增 `tests/test_r284_hover_gloss.py` 4 例：hover 释义用 `gloss` 且不含历史长串 /
  gloss 开关不联动 `title` / 页面入口只剩右上角 Help / i18n 文案与 po 同源。
- 更新 `test_reader_r226_acceptance.py`（R226 的「按钮带明确文案」改钉「调用链断开」）
  与 `test_onboarding_tour.py`（中文种子词条）。
- 定向回归 **106 passed**：R284、R226、R109/R216 引导、R111 阅读器视觉、R215 UI、
  R268 波浪线、生词契约、R251 账号 IA；`node --check` 三个改动 JS 全过。
- 全量未跑（开发态闸门：只跑受影响子集）；**未真机**：hover 原生 tooltip 的
  出现延迟与深色主题表现、导览从右上角 Help 启动后的跨页 handoff 需线上验收。

## 4. 边界

- 阅读器页没有顶栏，因此下线右下入口后该页不再有导览起点；这是用户口径
  「只保留右上角的帮助的入口」的直接结果，导览仍可由主站 Help 启动后续到阅读器。
- `onboarding.css` 的 `#onb-help` 规则保留（无 DOM 生成，R215 视觉守卫仍锁它），
  浏览器若缓存旧 JS 仍可能短暂看到按钮，强刷即可。
- 不改 moon-well：`ReadingVocabularyVO` 的 `gloss` 已足够；R232/R233/R236 的
  生词判定口径不变，被标哪些词不受本轮影响。
- hover 释义只覆盖词典命中的词；未命中词仍是「波浪线 + 问号光标」，但不再有
  「点了却什么都没有」的假释义。若要求全覆盖需另立需求（接 AI 释义/详解面板）。

## 5. 文档四问

| 问 | 落点 |
| --- | --- |
| 能力变了吗 → L1 | `readme/reading.md`（hover 释义、引导入口）、`readme/readme.md`（上手第 5 步） |
| 契约变了吗 → L2 | `product/reading-vocabulary.md`（R284 状态、`gloss` 双用途、旧规格标注取代） |
| 实现/边界变了吗 → L3 | `learning/features/onboarding.md`（入口表、状态机、`runSegment`） |
| 本次怎么实现 → LLD | 本文件；需求基线 `learning/requirements.md` §R284；台账 requests/response |

## 6. 驻留登记

worktree `../magicbook-r284-hover-gloss-onboarding`，分支 `feat/r284-hover-gloss-onboarding`，
基线 `origin/develop@43e9bec2`（R284 占号提交）。按家族纪律 merge 后原样保留待验收，
验收通过才 `worktree remove` → `branch -d`。代码已于 11:11 推送 `origin/develop`
（`43e9bec2..48030f33`），台账/LLD 状态回填以纯文档提交单独推送（不触发重建）。
worktree 分支停在 `3d31fa43`，比 develop 少一个纯文档提交，验收以 develop 为准。

## 7. 验收缺陷环：hover 仍然只有「问号」（同日 11:34 用户反馈）

- **现象**：R284 首版上线后用户复验「hover 波浪线生词还是问号」。
- **根因**：首版只补 `span.title`（浏览器原生 tooltip，需停留约 1 秒、`gloss=null`
  时根本不生成），**没有动产生问号的那行 `cursor: help`**。父页 `reader.css` 与
  R268 注入 iframe 的样式都留着它，hover 时鼠标变问号光标，观感完全没变。
- **修复**：① 两处 `cursor: help` → `cursor: pointer`；② `epub.js` 新增
  `cleanGloss` / `showVocabHoverCard` / `lookupVocabHover` / `bindVocabHover`，
  在 `markVocabulary` 遍历 contents 时对每个 iframe 文档幂等绑定 `mouseover`/`mouseout`；
  ③ hover 立即弹父页 fixed 卡片，优先 `record.gloss` → `hoverTranslation` → `span.title`，
  `?`/`-`/空白占位一律过滤；三者皆空时先显示「翻译中」，再走
  `/ajax/reading-translate`（与划词气泡同一端点、同样补 CSRF 头），结果按词缓存；
  ④ 迟到响应用 `vocabHoverSeq` + `vocabHoverWord` 双判据丢弃，`mouseout` 140ms 隐藏。
- **为什么不把卡片放进 iframe**：插进正文会被 `currentPageText` 当成正文上送，
  改变 analyze 页面签名并触发重复请求 / 重分页；父页 fixed 层用
  `frameElement.getBoundingClientRect()` 换算坐标（与 `translateSelection` 同款）。
- **验证**：`tests/test_r284_hover_gloss.py` 增 1 例并更新 2 处断言（问号光标下线、
  卡片与翻译兜底齐备、gloss 开关不联动）；定向 **131 passed / 0 failed**，
  `node --check` 两个改动 JS、`git diff --check` 通过。`mbT('Translating…')` 复用既有
  种子词条，避免 i18n 契约守卫报缺。
- **流程**：挂 R284 验收缺陷环，不另占号、不新建 idea；复用同一 worktree。
