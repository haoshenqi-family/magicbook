# LLD · R284 页面引导入口下线（只保留右上角 Help）

- 状态：**已上线待验收**（2026-11-06；生词 hover 相关改动已于 12:31 按用户要求全部撤销）
- 关联需求：R284（修改意见，挂 R226 引导入口后续，按治理不新建 PingCode idea）
- 目标仓：magicbook（纯前端 + i18n + 文档，moon-well 零改动）

> 目录名沿用初版 `r284-hover-gloss-onboarding`，但「hover gloss」部分已撤销；
> 按「历史只标注不重写」保留路径与编号，不改名、不新建迭代目录。

## 1. 需求与现场

用户 2026-11-06 反馈阅读器里出现「问号」，随后给出参考截图明确期望的
「划词翻译」形态：**MagicLens 扩展**的划词气泡（紫色 `#8b5cf6` 波浪线 +
译/详/🔊/认识/生词/AI/✕，见 `magiclens/extension/content.js` 与 `highlight.js`
的 `::highlight(ml-vocab)`）。扩展接管高亮时 magicbook 内置 `markVocabulary`
按 R146 让位，因此在 magicbook 内置链路上做 hover 释义/卡片并不会作用到用户
看到的那条波浪线——这是两轮改动被否决的根因。

用户最终拍板保留的部分：**页面上的引导入口全部下线，只保留右上角 Help**。

## 2. 实现（保留部分）

| 位置 | 处置 |
| --- | --- |
| `layout.html` 右上角 Help → `#top_onboarding` | **保留，全站唯一入口**（R269 后该下拉本来就只有这一项） |
| `onboarding.js` `runSegment` | 只保留断点续览；不再 `showInvite`、不再 `showReaderHelp` |
| `onboarding.js` `showEntryAgainIfNeeded` | 留空，导览 finish/dismiss 不再挂回右下按钮 |
| `reading_settings.html` | 删 `<section class="reading-onboarding">` |
| `reading-preferences.js` | 删 `#reading-onboarding-start` 点击转发 |
| `read.html` | **保留** `onboarding_mount.html` include：右上角 Help 启动的导览仍需跨页续到阅读器段 |
| `onboarding.js` `showInvite` / `showReaderHelp` 函数体 | 保留但不再调用（R111/R226 视觉守卫仍锁其几何与文案形制） |

**文案同源**：`i18n_seed.html` + `zh_Hans_CN` po/mo + `onboarding.js`，收尾卡由
「右下角按钮」改为 `Open Help in the top-right corner to replay this tour.`
（中文「随时从右上角「帮助」重看本段导览。」）。只重编译 zh_Hans_CN 的 mo：
整树 `pybabel compile` 会撞上 `it` 语既有的 `unknown named placeholder 'nome'`，
且会重写 30 个语言 mo，与本轮无关。

## 3. 已否决并撤销的部分（12:31）

用户明确「撤销我这两轮改动」。以下改动曾上线（`48030f33`、`6247fa44`），
现**全部回滚**，生词链路回到 R268 原状（`span.title` 仍下线、`cursor: help` 保留）：

| 轮次 | 曾做的改动 | 回滚 |
| --- | --- | --- |
| R284 首版 | `epub.js markVocabulary` 写 `span.title = gloss`（R236 词典首义项） | `epub.js` 恢复 `43e9bec2` 版本 |
| 验收缺陷环 | `cursor: help` → `cursor: pointer`（`reader.css` + `reader-core.js` 注入样式）；新增 `cleanGloss` / `showVocabHoverCard` / `lookupVocabHover` / `bindVocabHover` 即时卡片与划词翻译兜底 | 两个文件恢复 `43e9bec2` 版本 |
| 守卫 | 新增 `tests/test_r284_hover_gloss.py`（含 hover 释义、光标、卡片断言） | 删除 |
| 文档 | L1 生词悬停条目、L2 `reading-vocabulary.md` 的 R284 状态与验收缺陷段 | L1 条目删除、L2 整份恢复 `43e9bec2` 版本 |

**不做**：不改 MagicLens 扩展、不改 moon-well、不动 R268 波浪线注入、不动 R146
让位逻辑。若后续要恢复「hover 生词弹截图中那种气泡」，应落在 magiclens 侧
（`__magicLensShowWordBubble` / R20/R21 hover 链路），并另立需求。

## 4. 验证

- 保留 `test_reader_r226_acceptance.py`（R226 断言改钉「调用链断开」）与
  `test_onboarding_tour.py`（中文种子词条）。
- 撤销后定向回归需复跑引导 / 阅读器 / R268 / i18n 契约相关子集；
  `node --check`、`git diff --check`。
- **未真机**：导览从右上角 Help 启动后的跨页 handoff 待线上验收。

## 5. 文档四问（现行）

| 问 | 落点 |
| --- | --- |
| 能力变了吗 → L1 | `readme/reading.md`（使用引导条目）、`readme/readme.md`（上手第 5 步） |
| 契约变了吗 → L2 | 无接口变化；`reading-vocabulary.md` 已回退，不再有 R284 注记 |
| 实现/边界变了吗 → L3 | `learning/features/onboarding.md`（入口表、状态机、`runSegment`） |
| 本次怎么实现 → LLD | 本文件；需求基线 `learning/requirements.md` §R284（含撤销记录）；台账 requests/response |

## 6. 驻留登记

worktree `../magicbook-r284-hover-gloss-onboarding`，分支 `feat/r284-hover-gloss-onboarding`。
按家族纪律 merge 后原样保留待验收，验收通过才 `worktree remove` → `branch -d`。
代码已推送 `origin/develop`；台账/LLD 的撤销记录随本轮提交一并推送。
