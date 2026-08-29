# 阅读单词学习（划词翻译）

EPUB 阅读器自动识别当前可见页面的英文单词，将页面文本上交给 `moon-well`，由其对每个单词分词、查释义、判定陌生词并回传标注所需数据；陌生词在阅读器内以波浪下划线标识，悬停或点击可查看释义与历史学习信息。

## 功能要求

### 1. 核心目标

- 读者在阅读 EPUB 时，**自动**标记当前页中的「陌生/待学单词」（无需手动划选）。
- 对陌生词提供释义、上一次学习记录（书籍/章节/页/时间/次数）的即时查看。
- 完善的学习闭环：首次标记 → 释义展示 → 学习历史与次数随每次出现递增。

### 2. 交互要求

- 陌生词以**波浪下划线** + `cursor: help` 标识，悬停高亮背景（见 `reader.css` 的 `.reading-vocabulary-unknown`）。
- 点击陌生词弹出释义；若无释义则提示「点击查看学习记录」，有历史则附「上次：<书> · <章节>」。
- 每个词仅包一层 span，禁止出现嵌套标注（已在 `markVocabulary` 中跳过已标注的文本节点）。

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
- 代理超时设置 15 秒，容忍 moon-well 冷启动（重启后首连 ES/Nacos）的临时慢响应。
- 请求必须携带 CSRF token：EPUB 阅读器不加载 `main.js`（无全局 `$.ajaxSetup`），而服务端全局启用 CSRF，故前端显式附带 `X-CSRFToken`，否则生词标注在真实环境静默失效（曾出现 400）。
- **令牌自动刷新**：moon-well access token 有效期 7 天且仅在 OIDC 登录回调时交换颁发。会话令牌收到 401 时代理自动调 `POST /auth/refreshToken`（refresh token 30 天，每次刷新同时轮换）换新并重试一次；刷新失败（30 天未使用）则清空会话令牌并返回 401「login expired, please sign in again」，用户重新登录即可恢复。客户端请求头自带 `authorization` 时不刷新，401 原样透传。

## 配置

在 magicbook 进程配置：

```bash
MOON_WELL_READING_URL=http://fnos:8082
```

调用 `/reading-vocabulary/**` 时使用 moon-well 标准 `authorization: Bearer <token>` 请求头。token 来自 Authentik OIDC 登录回调中经 `POST /auth/oidc/exchange` 交换得到的 moon-well JWT（存于服务端会话 `moonwell_access_token`），或由客户端请求头显式携带。moon-well 通过 JWT 的 `UserContext` 确定用户，客户端不能通过 `userKey` 冒充其他用户。

## 接口设计

**请求**（magicbook `/ajax/reading-vocabulary` → moon-well `POST /reading-vocabulary/analyze`）：

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
    { "word": "serendipity", "translation": "好运", "lastBookName": "...",
      "lastChapter": "...", "lastPage": "...", "lastStudyTime": "...",
      "studyTimes": 2, "unknown": true }
  ]
}
```

前端仅在 `unknown: true` 时用波浪线标注该词；`translation` 为空时回退「点击查看学习记录」。

### moon-well 侧职责

- `extractWords(pageText)`：正则分词、去重、丢弃单字母（与前端一致）。
- `sentenceAround(text, start, end)`：提取每个词所在句子的上下文片段（至句读/换行，上限 500 字符）。
- 对每词：查历史（`reading_vocabulary` ES 索引）→ 查词库释义（`vocabulary` 索引）→ 写 ES 归档 → 统计 `studyTimes` → 返回 VO。
- 释义缺失时沿用历史释义，避免覆盖为空。
- 用户身份来自请求 `authorization: Bearer` JWT 的 `UserContext`，客户端不能通过 `userKey` 冒充其他用户。

## 当前范围

第一版接入 EPUB/KEPUB 阅读器，因为 epub.js 能直接访问当前章节 iframe 的 HTML 文本和 CFI 位置。PDF、TXT、漫画和音频阅读器尚未接入这套识词流程。

如果没有配置 moon-well 地址或令牌，阅读器保持原有行为，不显示错误弹窗。
