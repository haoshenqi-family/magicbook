# 阅读单词学习（生词划线 + 划词翻译）

本文件覆盖阅读器里两条**独立**功能（R287 口径，用户 2026-11-06 定义）：

| | 生词划线 | 划词翻译 |
|---|---|---|
| 触发 | 自动（当前页 analyze 后标注） | 用户框选任意文本；或**悬停生词**（等于免去框选） |
| 范围 | 只标生词（单词级） | 任何位置的任何文本：生词、非生词、短语、句子、中文 |
| 默认行为 | 只有波浪线；设置里打开「生词行内释义」才在词上方浮一行小字（R261，默认关） | 单个英文单词 → 自动出译文；**非单个英文单词 → 只出气泡，点「译」才发请求** |
| 成本 | 不产生 LLM 调用 | 单词走词典优先（金山命中即不花 LLM）；非单词必须用户显式点「译」 |

> **为什么非单词不自动翻**：框选长段/中文，多数场景是复制、引用、问 AI，一选就送 LLM
> 等于把复制动作也计费。单词相反——词典命中即免费，自动翻才划算。

## 一条链路，两种触发（R287）

`reader-selection.js` 的 `openTranslationFor(text, context, rect)` 是**唯一**入口：

- 用户框选 → `translateSelection` → `openTranslationFor`；
- 悬停生词 140ms（触屏点一下）→ `bindVocabHover` → `openTranslationFor`。

单词分支自动请求 `/ajax/reading-translate`，气泡显示译文 + 来源 + `🔊 / ＋ / － / 详 / AI`；
非单词分支只出原文预览 + `译 / AI`，点「译」才请求。两条分支共用同一个气泡、同一份
自动隐藏计时与关闭路径。

R286 曾为悬停另造过一张 `.reading-vocab-card` 七按钮卡片，与本气泡同页两套 UI，已随 R287 下线。

## 历史沿革（过去的口径，勿据此实现）

- **2026-09-14**：生词的「悬停 tooltip / 点击 alert」因「释义 + 上次：书 · 章节」太长下线，
  analyze 同步暂停查词典释义。**其中「上一次学习记录」相关字段已于 R139 从契约删除**
  （moon-well VO 只剩 `word / unknown`，R236 才补回 `gloss`）——本文件不再有「学习历史」这一项。
- **2026-10-09 R141 / 2026-10-10 R146（现行）· 与 MagicLens 扩展的边界**：内置划词气泡与
  生词波浪线在扩展声明接管时**让位**，且是运行时探测而非写死——气泡看**本帧**的
  `data-magiclens-selection`、波浪线看**顶层**的 `data-magiclens-highlight`；读不到标记就自己干
  （未装扩展 / 扩展过旧 / 该 frame 注入失败 / 用户关了高亮）。口径是**只让位扩展已实现的部分**
  （R143 纠偏：段落「译」、整页/整本翻译、朗读、批注、AI 伴读、右键菜单都留在内置）。
  守卫 `tests/test_reader_lens_handoff.py`。
- **保留项（内置独有）**：段落「译」、工具栏整页「译」与「整本译」、段落朗读/批注/AI 伴读、
  划词右键快捷菜单，以及 `inspectVocabulary` 的每页上送（喂 moon-well 阅读事件流与伴读生词上下文）。
  代理端点 `/ajax/reading-translate`、`-word-mark`、`-word-detail` **一直有前端调用方**
  （内置气泡在扩展未接管时工作；R287 的悬停触发也走同一条），`-translate-batch` 服务段落翻译。
- **R284（2026-11-06）**：试图用 `span.title` / 自绘小卡补悬停释义，被用户否决并撤销
  （形态不对，且挂在会自我让位的链路上）。
- **R286（2026-11-06）**：按 MagicLens 气泡形态补了独立卡片，**已被 R287 取代**。


## 功能要求

### 1. 核心目标

- **生词划线**：读者不必动手，当前页的陌生/待学单词自动带波浪线；释义按需查看（行内小字开关、悬停、或框选）。
- **划词翻译**：读者框选任何文本都能拿到中文；单个英文单词零点击直接出结果，其余不浪费额度。
- 两条功能互不依赖：关掉生词功能，划词翻译照常可用；不开划词，生词照样标。

### 2. 交互要求

**2.1 生词划线**

- 陌生词以**波浪下划线** + `cursor: pointer` 标识，悬停高亮背景（`reader.css` 的 `.reading-vocabulary-unknown`）。**R268**：EPUB 正文渲染在同源 iframe 内，父页 `reader.css` 不跨文档生效，故下划线/悬停规则必须同时随 `READER_TOOLS_STYLE` 注入正文 iframe（`reader-core.js`）；否则 `analyze` 正常返回、span 已插入却看不到下划线，刷新也不恢复（只有 MagicLens 重新扫描才可见）。
- **行内小字释义（R261，可选默认关）**：设置里打开后，`span[data-gloss]::after` 在词**上方**浮一行小字（`content: attr(data-gloss)`，不占文档流、不推动分页）；词典没有该词就不挂属性，自然降级为仅波浪线。开关 key `calibre.reader.vocabGloss`，切换即重标当前页、不重新请求。
- 指针**不得**用 `cursor: help`：那是「悬停有说明但什么都没弹」的年代留下的，用户反馈里那个「问号」就是它。
- 每个词仅包一层 span，禁止嵌套标注（`markVocabulary` 已跳过已标注的文本节点）。

**2.2 划词翻译**

- 范围：**任何位置的任何文本**，与是否生词无关（未标注的词、短语、句子、中文都能划）。
- **单个英文单词**（`^[A-Za-z][A-Za-z'’-]*$`）→ 打开即自动翻译；词典命中返回 `source: dictionary`，未命中才走 LLM。
- **非单个英文单词** → 气泡只显示原文预览（>120 字截断）+ `译 / AI` 两个按钮，**不发任何请求**；点「译」才请求，点「AI」把内容带进伴读输入框。
- 气泡按钮：单词为 `🔊 / ＋ / － / 详 / AI`，非单词为 `译 / AI`；点击气泡内任意按钮都会重置自动隐藏计时。
- 关闭路径：Esc、翻页 `relocated`、点正文、正文滚动、到点自动隐藏（时长按词数折算，见「翻译显示时长」设置）。

### 3. 数据上报要求

- 前端**只上报当前可见「页」的文本 `pageText`**，不得逐词上报，避免 payload 膨胀（早期 `words:[{word,sentence}]` 一页数十词过大，已废弃）。
- 必须只取**当前页**而非整章：EPUB.js 的 iframe 内是整章内容经 CSS 分栏分页，直接取 `body.innerText` 会把整章全文（可达数十 KB）上报。正确做法是经 `currentLocation()` 的 start/end CFI 用 `book.getRange()` 精确取当前页；取文失败时兜底取整章，**保证接口必定被调用**。
- 分词、句子上下文提取、陌生词判定、释义查询、历史归档**全部由 moon-well 完成**，与前端正则保持一致（`\b[A-Za-z][A-Za-z'’-]*\b`，丢弃单字母）。
- 每次遇到单词都归档：单词、句子上下文、用户、书籍 ID/名称、章节、页码、EPUB CFI、学习时间和次数；历史入 ES `reading_vocabulary` 索引，原 `vocabulary` 索引继续提供词汇释义。

### 4. 缓存与请求优化

- 翻页/翻回时若页面文本与上次一致（签名对比），**不重复请求 moon-well**，直接复用已缓存 records 重新标注（`lastPageTextSignature`）。
- 已在会话内返回过的记录缓存于 `vocabularyRecords`（word → record），翻回已读页时立即重标。
- 请求飞行期间发生翻页：标记待重检，请求结束后自动重检新页，避免漏标（`vocabularyRetryPending`）。

### 5. 异常与降级

- 未配置 moon-well 地址或令牌：阅读器保持原有行为，**不弹错误弹窗**；后端返回 503「not configured」。
- moon-well 不可达或超时：后端返回 503「service unavailable」，阅读器静默处理。
- 代理超时设置 15 秒，容忍 moon-well 冷启动（重启后首次连接 ES）的临时慢响应。
- 请求必须携带 CSRF token：EPUB 阅读器不加载 `main.js`（无全局 `$.ajaxSetup`），而服务端全局启用 CSRF，故前端显式附带 `X-CSRFToken`，否则生词标注在真实环境静默失效（曾出现 400）。生词标注、划词翻译、沉浸式翻译、段落朗读、书签**所有阅读器 POST 均须携带**；旧版本划词翻译曾遗漏（线上 400），bar-ui（音频阅读器）曾漏 3 处。
- **CSRF token 不设独立超时**：`WTF_CSRF_TIME_LIMIT=None`（`cps/__init__.py`）。阅读器页面长期保持打开、token 嵌入隐藏域无法刷新，flask-wtf 默认 1 小时会让超时后全部阅读请求 400（日志 `The CSRF token has expired.`）。CSRF 防护已由 HttpOnly + SameSite=Lax 的签名会话 cookie 承载，放宽为仅随会话生效；旧 token 无需刷新页面即恢复。
- **前端 CSRF 失败自愈**：`reloadIfCsrfBlocked()` 检测到服务端 CSRF 类 400（token 过期/会话重建后 token 不匹配）时刷新页面拿新 token（借助 localStorage 恢复原阅读位置），sessionStorage 标记防死循环；TTS 失败而非 CSRF 时降级浏览器语音。
- **令牌自动刷新**：moon-well access token 有效期 7 天且仅在 OIDC 登录回调时交换颁发。会话令牌收到 401 时代理自动调 `POST /auth/refreshToken`（refresh token 30 天，每次刷新同时轮换）换新并重试一次；刷新失败（30 天未使用）则清空会话令牌并返回 401「login expired, please sign in again」，用户重新登录即可恢复。客户端请求头自带 `authorization` 时不刷新，401 原样透传。

## 配置

在 magicbook 进程配置：

```bash
MOON_WELL_READING_URL=http://fnos:8082
```

调用 `/vocabulary/reading/**` 时使用 moon-well 标准 `authorization: Bearer <token>` 请求头。token 来自 Authentik OIDC 登录回调中经 `POST /auth/oidc/exchange` 交换得到的 moon-well JWT（存于服务端会话 `moonwell_access_token`），或由客户端请求头显式携带。moon-well 通过 JWT 的 `UserContext` 确定用户，客户端不能冒充其他用户。

## 接口设计

**请求**（magicbook `/ajax/reading-vocabulary` → moon-well `POST /vocabulary/reading/analyze`）：

```jsonc
{
  "bookId": 7,
  "bookName": "Sample Book",
  "chapter": "Chapter 1",
  "page": "3/120",
  "cfi": "epubcfi(...)",
  "pageText": "当前页完整文本（由 moon-well 分词）"
}
```

- magicbook 是**纯透传代理**：校验本地登录会话，通过 OIDC 登录时交换得到的 moon-well JWT（`authorization: Bearer`）鉴权，转发到 moon-well。
- **响应结构保持不变**，前端标注逻辑零改动。

**响应**（moon-well → magicbook → 前端标注）：

```jsonc
{
  "success": true,
  "code": 200,
  "result": [
    { "word": "serendipity", "unknown": true,
      "gloss": "n. 好运" }
  ]
}
```

> **R139（2026-10）**：上方示例中的 `translation/lastBookName/lastChapter/lastPage/lastStudyTime/studyTimes`
> 七个死字段已从契约删除（自 2026-09-14 起永不赋值）；moon-well VO 仅 `word/unknown`。
> **R236（2026-11）**：新增 `gloss`——词目中文首义项（词典文档缓存批量查询，屈折候选展开；
> 词典无文档为 null），服务阅读器行内小字释义（Word Wise 式，可选功能默认关）。

前端仅在 `unknown: true` 时用波浪线标注该词；阅读器设置开启「行内小字释义」且 `gloss`
非空时，波浪线词上方再浮一行小字（`data-gloss` 属性 + iframe 注入样式 `::after` 渲染，
`epub.js` `markVocabulary` 挂属性、`window.ReaderVocabGloss.remark` 切换重标）。

### moon-well 侧职责

- `extractWords(pageText)`：正则分词、去重、丢弃单字母（与前端一致）。
- `sentenceAround(text, start, end)`：提取每个词所在句子的上下文片段（至句读/换行，上限 500 字符）。
- 对每词：查历史（`reading_vocabulary` ES 索引）→ 查词库释义（`vocabulary` 索引）→ 写 ES 归档 → 统计 `studyTimes` → 返回 VO。
- 释义缺失时沿用历史释义，避免覆盖为空。
- 用户身份来自请求 `authorization: Bearer` JWT 的 `UserContext`，客户端不能通过 `userKey` 冒充其他用户。

## 划词标记（＋不认识 / －已认识）

翻译气泡内、发音按钮旁提供 ＋/－ 按钮，仅当选中文本是**单个英文单词**（首尾为字母，与分词 `\b` 边界语义一致）时显示；句子/短语不显示。

- **请求**（magicbook `POST /ajax/reading-word-mark`，`{word, unknown}`，unknown 必须为 JSON boolean）：
  - 服务端校验：word 必须是字符串且匹配 `^[A-Za-z](?:[A-Za-z'’-]*[A-Za-z])?$`（≤64 字符；null 会被 `str()` 转成 `"none"` 存脏词，必须先查类型）；归一化为小写 + 直撇号后转发。
  - `unknown: true` → moon-well `GET /vocabulary/unknown/{word}`；`false` → `GET /vocabulary/known/{word}`（word URL 编码拼 path，白名单正则防注入）。
- **前端生效**（epub.js）：标记成功后更新 `vocabularyRecords` 并同步当前页标注——＋触发 `markVocabulary` 补波浪线；－触发 `unwrapWordSpans` 解包该词全部标注 span（波浪线即时消失）。按钮互斥高亮当前状态，toast 反馈结果。
- 词形 key 三端一致：前端 `normalizedWord`（小写 + 弯撇号→直撇号）、magicbook 归一化、moon-well ES `reading_vocabulary` 索引。

## 划词气泡的关闭（含自动消失）

EPUB 正文渲染在 iframe 中，**iframe 内事件不冒泡到主文档**——气泡关闭必须在两个 document 上分别处理（曾因此出现「双击查词后点击正文，气泡常驻不消失」）：

| 触发 | 处理位置 |
|---|---|
| 主文档区域点击气泡外 | 主文档 `mousedown`（气泡自身点击经 `contains` 豁免） |
| iframe 正文内按下 | iframe `document` `mousedown`（正文内任何按下都意味着离开气泡） |
| 单击正文清除选区 / 超长选区 | `translateSelection` 所有「不弹气泡」路径统一 `closeTranslationPopover()` |
| 翻页 | `relocated` 事件（旧气泡坐标基于已换下的页面） |
| ESC | 主文档 + iframe `document` 的 `keydown` |

## ESC 快捷键（分层退出）

- **划词气泡**：主文档与 iframe 内按 ESC 均关闭气泡。
- **AI 伴读抽屉**（ai_chat.js，EPUB/TXT/PDF 三种阅读器通用）：ESC 关闭抽屉。
- **分层**：气泡与抽屉同开时一次 ESC 只关气泡。epub.js 的 ESC handler 关闭气泡后 `event.stopImmediatePropagation()` 阻断后注册的监听；ai_chat.js 侧另有 `window.ReaderTranslation.isOpen()` 兜底检查——两种注册顺序下分层均成立（`read.html` 中 epub.js 先加载；若顺序颠倒，`isOpen()` 检查仍先于 epub.js 的 handler 生效）。

## 当前范围

第一版接入 EPUB/KEPUB 阅读器，因为 epub.js 能直接访问当前章节 iframe 的 HTML 文本和 CFI 位置。PDF、TXT、漫画和音频阅读器尚未接入这套识词流程。

如果没有配置 moon-well 地址或令牌，阅读器保持原有行为，不显示错误弹窗。

## 段落批注

EPUB 阅读器为每个可识别段落提供 `✎` 批注按钮，并在阅读器标题栏提供「批」按钮查看本书批注。

- **段落批注**：点击段落旁的 `✎` 打开批注弹层，显示该段落已有批注，并可填写新批注；`Ctrl+Enter` 或 `Cmd+Enter` 提交，`Esc` 关闭。
- **本书批注**：点击标题栏「批」打开本书批注面板，按章节展示有批注的段落、批注人、批注时间和批注内容，最多展示 200 个段落。
- **段落键一致性**：前端使用与翻译/TTS 完全相同的 `paragraphSpeechText`（压缩空白、trim、最多 2000 字符）作为 `paragraph`，确保批注、翻译和音频命中 moon-well 的同一 ES 文档。
- **身份与时间**：magicbook 仅透传批注段落和内容；`nickName` 与 `annotatedAt` 由 moon-well 根据 JWT 用户和服务端时间生成，客户端不能伪造。
- **接口代理**：
  - `POST /ajax/reading-annotation-create`
  - `POST /ajax/reading-annotation-list-by-paragraph`
  - `POST /ajax/reading-annotation-list-by-book`
- **安全与降级**：所有批注 POST 显式携带 `X-CSRFToken`；代理沿用 moon-well JWT、401 刷新和 503 服务不可用处理。批注保存失败会提示用户，不静默丢失；浮层请求返回 CSRF 错误时自动刷新页面恢复 token。
