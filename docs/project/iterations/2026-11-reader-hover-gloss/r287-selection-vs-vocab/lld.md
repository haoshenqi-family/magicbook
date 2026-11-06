# LLD · R287 划词翻译与生词划线拆成两条独立功能

- 状态：**开发完成待验收**（2026-11-06；`feat/r287-selection-vs-vocab`）
- 关联需求：R287（修改意见，挂 R286 后续；R286 的卡片形态被本轮取代）
- 目标仓：magicbook（纯前端 + 守卫 + 文档；moon-well / MagicLens 零改动）

> 目录挂在 `2026-11-reader-hover-gloss` 下——同一件事（生词与划词的交互形态）的第三次迭代，
> 不新开迭代，避免同一个话题横跨三个目录。

## 1. 触发这次改的原因

R286 上线半小时后，用户给了完整口径（不是修 bug，是纠形）：

> 「划词翻译和生词划线是两个功能。生词划线仅自动标识生词即可，若用户打开了生词自动翻译
> 显示开关，生词后（里）显示词义。划词翻译适用于任何地方，不仅限于生词。未标注生词的单词
> 也可以。划词如果是英文单词，自动翻译。如果非英文单词，需要点击译字才翻译（避免用户只是
> 为了选中复制等其他非翻译场景浪费 token）。」

对照代码，R286 有三处与这个口径不符：

| # | 现状（R286） | 应有 |
| --- | --- | --- |
| 1 | 悬停弹一张**独立卡片**（自建 DOM/样式/状态/导出，七个按钮） | 悬停只是「免去框选」，内容就是划词翻译的结果——**同一个气泡** |
| 2 | `translateSelection` 被 `calibre.readingVocabularyEnabled` 绑死 | 两条功能独立：关掉生词，划词照常可用 |
| 3 | **任何选区都自动送 LLM**（含中文、长句） | 只有单个英文单词自动；其余等用户点「译」 |

另外，R286 的卡片只读 `record.gloss`（analyze 的词典首义项），缺 gloss 就显示「暂无译文」
等用户点「译」——而用户要的是「悬停**自动**显示划词翻译的内容」。

## 2. 实现

### 2.1 唯一入口 `openTranslationFor(text, context, rect)`

```
框选  → translateSelection → openTranslationFor
悬停  → bindVocabHover(140ms) → openTranslationFor
```

- 单词（`SINGLE_WORD_RE`）→ `showTranslationPopover('', rect, true)` → `requestTranslation()`
  自动请求；结果渲染译文 + 来源 + `🔊 / ＋ / － / 详 / AI`。
- 非单词 → `showTranslationPopover(原文预览, rect, false)` + `译`/`AI` 两个按钮，
  **不发请求**；点「译」才 `requestTranslation()`，并把气泡切到 loading。
- 非单词气泡不启动自动隐藏倒计时（用户在等自己决定）。

### 2.2 悬停生词

- `bindVocabHover`：`mouseover` 命中 `.reading-vocabulary-unknown` → 140ms 确认 → 有选区就让位
  （用户可能正在拖选）→ 把 span 矩形换算到主视口后喂给 `openTranslationFor`。
- `click` 兜底触屏（点一下 = 悬停），已开着同一个词则不重复请求。
- 鼠标移开**不**立刻收气泡，交给原有自动隐藏计时——用户要来点 🔊/详/＋/－。
- 正文滚动收起（连续滚动模式下锚点失效）。

### 2.3 下线 R286 卡片

删除 `.reading-vocab-card` 的 DOM 构建、样式、`vocabCard*` 状态、`isVocabCardOpen` 等导出，
以及 `epub.js` 里的三处卡片钩子（点外关闭 / Esc 分层 / 翻页关闭）。保留 R286 的两项附带修复：
`cursor:help → pointer`（父页 + 注入 iframe 两处）与 `setHost` 补接台账三通道。

### 2.4 一点顺带的收敛

- `renderTranslationResult()` 统一渲染，单词/非单词走同一处，避免两份按钮拼装逻辑。
- `appendAskAiButton()` 两种气泡都有 AI：单词气泡里是 float 的小 `AI`（与 🔊/＋/－/详 同排），
  非单词气泡里是胶囊按钮（与「译」同排）。

## 3. 边界与不做

- **不改 MagicLens 扩展**：站外与「扩展接管本帧」时的气泡仍由扩展负责，它本来就是
  「单词自动、非单词点译」的口径（其 R57）。若要扩展也支持 hover，是扩展侧的独立需求。
- **不改 moon-well**：单词/非单词的自动与手动之分完全在前端，端点与计费口径不变。
- **不动 R261 行内小字**：开关默认关、词上方小字、`data-gloss` + `::after` 渲染。
- **已知差异**：装了扩展且高亮开着时，内置不画 span → 悬停不触发（用户看到的是扩展的紫色
  高亮，扩展也没有 hover 卡片）。这是 R146 让位口径的必然结果，不属本轮范围。

## 4. 验证

- 新增守卫 `tests/test_r287_selection_vs_vocab.py` 7 例：解耦、单词自动/非单词不请求、
  译与 AI 入口、悬停复用同一链路且卡片下线、指针不退回 `help`、`setHost` 四通道、关闭路径。
- 定向回归：`test_r268` / `test_r261` / `test_i18n_seed_contract` / `test_reader_r226_acceptance`
  + 本轮 = **26 passed**。
- 视觉/行为冒烟（无头 Chrome 加载真实 `reader-selection.js` + `reader.css`，`$.ajax` 打桩）：
  - 悬停生词 → 自动出译文气泡（1 条 POST）；
  - 选中英文句子 → 只出原文 + `译`/`AI`，**0 条 POST**；
  - 选中中文 → 同上，**0 条 POST**；
  - 点「译」→ 发 1 条 POST 并渲染结果。
- **未真机**：触屏点按、真实 EPUB 分栏下的气泡定位待线上验收。

## 5. 文档四问

| 问 | 落点 |
| --- | --- |
| 能力变了吗 → L1 | `readme/reading.md`：拆成「生词划线」「划词翻译」两条 |
| 契约变了吗 → L2 | 无接口变化；`reading/interface.md` 修正 `/ajax/reading-translate` 的「暂无调用方」过期说法 |
| 实现/边界变了吗 → L3 | `product/reading-vocabulary.md` 重写为「两条独立功能 + 一条链路两种触发 + 历史沿革」 |
| 本次怎么实现 → LLD | 本文件；需求基线 `learning/requirements.md` §R287（§R286 已标注被取代）；台账 #287 |

## 6. 驻留登记

worktree `../magicbook-r287-selection-vs-vocab`，分支 `feat/r287-selection-vs-vocab`
（从 `origin/develop` 切出）。merge 后原样保留，验收通过才 `worktree remove` → `branch -d`。
同族工作树 `../magicbook-r286-vocab-hover-card` 的卡片实现已被本分支取代，验收时一并处置。
