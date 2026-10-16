# vocabulary · L2 接口说明

> 读者：调用者 / 集成者。magicbook 侧为薄代理 + 前端交互；判定/测试的**后端语义唯一权威在 moon-well** `docs/vocabulary/hld/hld.md`，本文件只维护代理映射与前端约定。

## 能力边界

阅读器划词/高亮/标记的前端交互、词汇量测试 UI、难度设置入口；后端判定矩阵、词族口径、测试状态机不在本模块。**划词翻译气泡、生词波浪线标注、单词详解面板的前端交互自 2026-10-09（R141，边界经 R143 收窄）起让位给 magiclens 扩展**——口径是「只隐藏 magiclens 已经做了的部分」（其气泡划词翻译与生词高亮均已实现，且会绑进 epub.js 的同源 iframe，两套并存就是双气泡、一词双线）；段落/整页翻译 magiclens 仍是规划 P1，**不在隐藏范围**。本模块的代理端点与后端语义不变，仅 epub.js 侧按**运行时探测**关掉这两块内置 UI：划词气泡看本帧 `data-magiclens-selection`、波浪线看顶层 `data-magiclens-highlight`（magiclens v0.8.6 / R37 写入，其引擎关停时会自行清除），读不到标记则内置实现照常（R146，替代此前写死的开关——写死曾造成「装了扩展但该能力在此处不通 → 功能空白」）。

## 子功能概要

### 1. 生词判定与标记（代理 `/ajax/reading-vocabulary`）

- `POST /ajax/reading-vocabulary` → moon-well `POST /vocabulary/reading/analyze`（15s）：上送当前页文本，返回生词集合。**epub.js 仍每页上送**（喂 moon-well 阅读事件流与 AI 伴读生词上下文），但 `markVocabulary` 的 DOM 波浪线标注已下线（R141，改由 magiclens 在同一 iframe 用 CSS Custom Highlight 渲染）。
- 标记：划词气泡「＋生词 / －认识」→ moon-well `GET /vocabulary/unknown|known/{word}`（自动补录生词本）。**内置气泡入口已下线，现由 magiclens 承担**；`/ajax/reading-word-mark` 代理端点保留。
- 词形口径：后端按屈折词族判定（R107），前端不做词形过滤；标记按页面原文落库，后端入口做小写归一（moon-well R116）。

### 2. 划词翻译与详解

- 翻译映射见 [reading L2 接口说明](../reading/interface.md) §1（`/ajax/reading-translate*`）。**内置划词气泡已下线（R141），`/ajax/reading-translate` 端点保留**，magiclens 直连 moon-well、不经本站代理。
- 详解：`POST /ajax/reading-word-detail` → `GET /vocabulary/detail/{word}`；六板块结构化 JSON。**内置「详」面板入口随气泡下线（R141），端点保留**；面板的前端交互契约（变体角标、仅 ✕/Esc 关闭、未完成保持「AI 生成中」）现由 magiclens 的详解面板承接（同构实现）。

### 3. 词汇量测试（`/reading/settings` 入口，全屏浮层）

- 测试会话代理端点（start / answer / finish / history）→ moon-well `/vocabulary/test/*`；请求体不带 word（服务端按 `seq` 定位题面）。
- 错误语义：后端业务异常为 HTTP 500 + `Result.code`（50301 词表未就绪 / 50302 会话不可用 / 50303 答题数不足 / 50304 题号错位），代理层按 code 分支展示。
- 结果报告：估算值 + 置信区间 + 频段掌握度 + **推荐难度一键应用**（写回 §4 难度设置）；交卷可勾选把不认识的词收进生词本。

### 4. 难度设置（`/vocabulary/reading/settings`）

- `GET` 当前档位 + 全集档位（测试报告推荐一键应用的落点）；`POST /hard-level` 改档实时生效。

### 5. 全文单词详解（按书补缺，R176）

详情页第三个整本能力（与整本翻译/整本朗读并列），对端 moon-well R188。

| 端点 | 副作用 | 说明 |
| --- | --- | --- |
| `POST /ajax/word-detail-preview` | **只读** | `{book_id, book_format}` → `{distinctWords, cachedWords, targetWords, notWordLike, estimatedTokens, missingSample}` |
| `POST /ajax/word-detail-start` | 建台账 + 后台分批入队 | `{book_id, book_format, force}` → 批次进度快照（立即返回，发布在 daemon 线程） |
| `POST /ajax/word-detail-progress` | 只读 + 覆盖率懒回收 | `{job_id?}`（缺省按 `book_id` 取该书最新批次） |
| `POST /ajax/word-detail-cancel` | 停本批次 | 已入队任务仍由队列消费者生成完毕 |
| `GET /word-detail-batch` | 页面 | 管理员；`book_id` 非数字直接 400 |

- 门禁：四个 ajax 端点返回 **JSON 403**（`_llm_task_admin_gate` 形制，页面路由仍用 `@admin_required`）；权威白名单在 moon-well 侧二检，与 R126 面板同一纵深防御。
- **进度口径＝词覆盖率**（`coveredWords / targetWords`），不是任务状态：执行方是队列消费者，本站既非发起者也非唯一消费者，`COMPLETED` 不等于缓存里真有。
- 上游业务文案不被吞：灌队闸门（在途上限、单次 2000 词上限）的 `Result.message` 经 `progress.lastError` 原样到达页面。
- 台账 `reading_word_detail_job` / `reading_word_detail_job_item`，**item 粒度＝一批 200 词**（不是一词一行）；词形过滤（缩略形/连字符/单字母噪声）只存在于 moon-well 发布内核一处，本站照抽不滤，避免同一本书在两入口得出不同集合。
- 轮询 **30s** 且仅页面可见时：覆盖率源是 moon-well 的索引级扫描，不同于整本翻译的本地行计数（4s）。

## 调用方契约

- 鉴权：同 reading 模块——当前用户 JWT 代理，不走内网互信。
- 权威指针：判定矩阵与词族口径、测试状态机与错误码、详解缓存语义 → moon-well `docs/vocabulary/hld/hld.md`。

## L3 与历史设计

- [阅读单词学习规格](../reading-vocabulary.md)（跨 reading / vocabulary 的静态实现说明，L3 性质）
- 历史设计（`docs/project/_legacy/feat/`）：[词汇量测试 LLD（含 magicbook 侧 US4 代理与设置 UI）](../../project/_legacy/feat/vocab-size-test/design/vocab-size-test-lld.md) · [全文单词详解：台账与页面（R176）](../../project/_legacy/feat/word-detail/design/book-batch-panel.md)（对端 moon-well `docs/feat/word-detail/design/book-batch-warm-by-words.md`，R188）
