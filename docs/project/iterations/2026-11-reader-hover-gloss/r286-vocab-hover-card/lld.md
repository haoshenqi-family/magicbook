# LLD · R286 生词悬停释义卡（去掉「问号指针」，悬停即出释义）

- 状态：**已被 R287 取代**（2026-11-06 13:50）——用户补充口径「划词翻译与生词划线是两个功能，生词悬停就是划词翻译的结果」，独立卡片已下线，悬停改为复用划词气泡。本文保留为历史决策记录，勿据此实现；现行口径见同目录 `r287-selection-vs-vocab/lld.md`
- 关联需求：R286（修改意见，挂 R284 的「划词形态」后续；R284 已否决的 hover 卡由本轮重新设计）
- 目标仓：magicbook（纯前端 + 守卫 + 文档，moon-well 零改动、MagicLens 扩展零改动）

> 目录沿用 `2026-11-reader-hover-gloss`（同一件事的第三次迭代），不改名、不迁路径。

## 1. 现场与根因

用户 2026-11-06 12:41 再次反馈「magicbook 划词翻译显示问号」，参考图仍是 MagicLens 气泡。
截图里 `reversed` 同时具备两种状态：橙色波浪线 + `rgba(217,139,0,.16)` 悬停底色
（= `.reading-vocabulary-unknown:hover`），说明是**悬停**而非划词，且**没有出选区气泡**。

根因两层，都是「界面上静默退化」：

| 层 | 事实 | 后果 |
| --- | --- | --- |
| 样式 | `.reading-vocabulary-unknown { cursor: help }`（`reader.css` + `reader-core.js` 注入 iframe 的同款规则） | 鼠标一停生词就变成**问号指针**——就是用户说的「显示问号」 |
| 数据 | `span.title = gloss` 自 R268 下线；`ReaderSelection.setHost` 只接 `markVocabulary`/`buildSpeechUtterance`，装配层一直在传的 `getWordRecord`/`applyWordRecord` 被**静默丢弃** | 悬停没有任何释义落点；`record.gloss` 永远读不到；气泡 ＋/－ 高亮也永远不亮 |

划词（拖选）气泡本身是好的，但它只在 `mouseup` 时弹、且扩展声明接管该帧时让位——
**悬停这条路径从来就没有过任何信息**，而阅读时鼠标大半时间是悬停。

## 2. 方案（用户 2026-11-06 拍板：悬停弹 MagicLens 同款气泡）

- **指针**：`cursor: help` → `cursor: pointer`（父页 `reader.css` 与注入 iframe 的
  `READER_TOOLS_STYLE` **两处同改**；R268 的教训就是只改一处等于没改）。
- **卡片**：`reader-selection.js` 新增 F 节「生词悬停释义卡」——`.reading-vocab-card`
  挂在父页 body（正文 iframe 内没有可用层级），坐标按 `frameElement` 换算，与划词气泡
  同一套口径；白卡 + 词条 + 释义 + 胶囊按钮 `译 / 详 / 🔊 / 认识 / 生词 / AI / ✕`。
- **释义来源**：优先 `record.gloss`（`/ajax/reading-vocabulary` 返回的词典首义项，
  零请求零计费）；**没有 gloss 时不自作主张发请求**——单词未命中词典会走 LLM 计费，
  悬停不能悄悄扣积分，交给用户点「译」显式触发（moon-well 侧按文本持久缓存，重复点不再花钱）。
- **触屏**：`touchend` 点一下生词出卡；点出选区时仍走划词气泡（`getSelection()` 非空即让位）。
- **时机**：`mouseover` 后 140ms 确认再弹（扫过一行文字、拖选经过生词不弹）；移开 200ms
  收起，指针移进卡片则取消收起（否则按钮点不到）。
- **关闭路径**：`✕`、Esc、翻页 `relocated`、正文 `mousedown`、点卡片外部、连续滚动
  （`content.window` scroll 会让卡片脱锚）、以及「标认识」成功后（波浪线已拆，卡片指向空。
  **互斥**：与划词气泡同层——开卡即收气泡，拖选出译文时收卡，避免两个浮层叠在一处。
- **共用标记路径**：把气泡 `＋/－` 里的请求逻辑抽成 `markWord(word, unknown, btn, onDone)`，
  卡片的「认识/生词」复用同一条（请求 + 回写台账 + 同步波浪线只写一份）。
- **连带修复**：`setHost` 补接 `startWholeBookProgressPolling` / `getWordRecord` /
  `applyWordRecord`。此前三个实参被静默丢弃，「＋标生词」不画波浪线、「－标认识」不拆线、
  ＋/－ 高亮不亮；本轮卡片要读台账，这条通道必须真的接上。

## 3. 为什么不是回到 R284 的 hover 卡

R284 的两次尝试（`span.title = gloss` / 自绘小卡）被用户否决，原因是**形态不对**
（原生 tooltip、无按钮的小卡），且当时的实现挂在让位链路上。本轮按参考图重做成
MagicLens 同形制卡片，并把「指针」这一层（用户实际看到的「问号」）一并处理。
MagicLens 扩展与 moon-well 均未改动：正文 iframe 里扩展不接管高亮时，内置链路就是
用户能看到的那条波浪线，落在这里才有效。

## 4. 验证

- 新增守卫 `tests/test_r286_vocab_hover_card.py`（6 例）：禁回 `cursor:help`（父页 +
  注入样式）、卡片构建/悬停绑定/按钮形制、`setHost` 四条通道、标记路径收敛、
  翻页/点外/Esc/滚动四条关闭路径。
- 定向回归：`test_r268_vocab_underline_iframe.py`、`test_r261_jinshu_borrow.py`、
  `test_i18n_seed_contract.py`、`test_reader_r226_acceptance.py` + 本用例 = **25 passed**；
  阅读器/词汇相关子集 **273 passed**（`test_reading_tts_service.py` 44 例为 pytest
  tmpdir 在沙箱里的 `FileExistsError`，与本次改动无关，develop 上同样复现）。
- 视觉冒烟：用无头 Chrome 加载真实 `reader-selection.js` + 真实 `reader.css`，模拟
  iframe 正文里悬停 `reversed`，卡片按预期出现在词下方（词条灰字 + 释义 + 七个胶囊按钮，
  「生词」为选中态）。
- 未真机：真实 EPUB 分栏、深色主题下的卡片对比度、触屏点按待线上验收。

## 5. 文档四问

| 问 | 落点 |
| --- | --- |
| 能力变了吗 → L1 | `readme/reading.md`「划词查词」条目补「悬停生词即出释义卡」 |
| 契约变了吗 → L2 | 无接口变化（复用 `/ajax/reading-translate`、`-word-mark`、`-word-detail`） |
| 实现/边界变了吗 → L3 | `product/reading-vocabulary.md` §2 交互（指针口径 + 卡片规格 + 计费边界） |
| 本次怎么实现 → LLD | 本文件；台账 `requests.md` #286 / `response.md` |

## 6. 驻留登记

worktree `../magicbook-r286-vocab-hover-card`，分支 `feat/r286-vocab-hover-card`
（从 `origin/develop` 最新点切出）。按家族纪律 merge 后原样保留，验收通过才
`worktree remove` → `branch -d`。
