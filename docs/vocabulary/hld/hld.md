# vocabulary · HLD（设计概要）

> 读者：模块调用者/集成者。magicbook 侧为薄代理 + 前端交互；判定/测试的**后端语义唯一权威在 moon-well** `docs/vocabulary/hld/hld.md`，本文件只维护代理映射与前端约定。

## 能力边界

阅读器划词/高亮/标记的前端交互、词汇量测试 UI、难度设置入口；后端判定矩阵、词族口径、测试状态机不在本模块。**划词翻译气泡、生词波浪线标注、单词详解面板的前端交互自 2026-10-09（R141）起让位给 magiclens 扩展**（magiclens R24 会把 content script 绑进 epub.js 的同源 iframe，两套并存会双气泡重叠、一词双线）；本模块的代理端点与后端语义不变，仅 epub.js 侧用 `READER_BUILTIN_AI_UI_ENABLED=false` 关掉内置 UI。

## 子功能概要

### 1. 生词判定与标记（代理 `/ajax/reading-vocabulary`）

- `POST /ajax/reading-vocabulary` → moon-well `POST /vocabulary/reading/analyze`（15s）：上送当前页文本，返回生词集合。**epub.js 仍每页上送**（喂 moon-well 阅读事件流与 AI 伴读生词上下文），但 `markVocabulary` 的 DOM 波浪线标注已下线（R141，改由 magiclens 在同一 iframe 用 CSS Custom Highlight 渲染）。
- 标记：划词气泡「＋生词 / －认识」→ moon-well `GET /vocabulary/unknown|known/{word}`（自动补录生词本）。**内置气泡入口已下线，现由 magiclens 承担**；`/ajax/reading-word-mark` 代理端点保留。
- 词形口径：后端按屈折词族判定（R107），前端不做词形过滤；标记按页面原文落库，后端入口做小写归一（moon-well R116）。

### 2. 划词翻译与详解

- 翻译映射见 [reading HLD](../reading/hld/hld.md) §1（`/ajax/reading-translate*`）。**内置划词气泡已下线（R141），`/ajax/reading-translate` 端点保留**，magiclens 直连 moon-well、不经本站代理。
- 详解：`POST /ajax/reading-word-detail` → `GET /vocabulary/detail/{word}`；六板块结构化 JSON。**内置「详」面板入口随气泡下线（R141），端点保留**；面板的前端交互契约（变体角标、仅 ✕/Esc 关闭、未完成保持「AI 生成中」）现由 magiclens 的详解面板承接（同构实现）。

### 3. 词汇量测试（`/reading/settings` 入口，全屏浮层）

- 测试会话代理端点（start / answer / finish / history）→ moon-well `/vocabulary/test/*`；请求体不带 word（服务端按 `seq` 定位题面）。
- 错误语义：后端业务异常为 HTTP 500 + `Result.code`（50301 词表未就绪 / 50302 会话不可用 / 50303 答题数不足 / 50304 题号错位），代理层按 code 分支展示。
- 结果报告：估算值 + 置信区间 + 频段掌握度 + **推荐难度一键应用**（写回 §4 难度设置）；交卷可勾选把不认识的词收进生词本。

### 4. 难度设置（`/vocabulary/reading/settings`）

- `GET` 当前档位 + 全集档位（测试报告推荐一键应用的落点）；`POST /hard-level` 改档实时生效。

## 调用方契约

- 鉴权：同 reading 模块——当前用户 JWT 代理，不走内网互信。
- 权威指针：判定矩阵与词族口径、测试状态机与错误码、详解缓存语义 → moon-well `docs/vocabulary/hld/hld.md`。

## L3 索引

- [词汇量测试 LLD（含 magicbook 侧 US4 代理与设置 UI）](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/vocab-size-test/design/vocab-size-test-lld.md)
- [阅读单词学习规格](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/reading-vocabulary.md)
