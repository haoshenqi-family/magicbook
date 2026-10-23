# reading · L2 接口说明

> 读者：调用者 / 集成者。magicbook 是阅读前端，本模块对 moon-well 是**薄代理层**：请求带当前用户的 moon-well JWT 转发，**token 不下发浏览器**。后端契约的唯一权威是 moon-well 对应 L2，本文件只维护「magicbook 端点 → moon-well 端点」的映射与超时口径。

## 能力边界

阅读器页（EPUB/PDF/TXT）与阅读相关代理、NCE 音频播放。词汇判定/详解/测试的后端语义不在本模块（见 vocabulary L2 接口说明与 moon-well）。

> R215（MB-14）为纯前端交互改造：翻译译文改为右侧译文栏、AI 面板改为桌面半屏停靠/移动底部抽屉；**不新增、不修改任何 moon-well 契约**。实现与边界见 [translation-rail L3](features/translation-rail.md) 与 [companion-panel L3](features/companion-panel.md)。

## 子功能概要

### 1. 阅读能力代理（cps/web.py，`/ajax/reading-*`）

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/reading-vocabulary` | `POST /vocabulary/reading/analyze` | 15s | 生词判定（容忍 moon-well 重启后 ES 首连慢响应）；epub.js 仍每页上送（喂阅读事件流 + AI 伴读生词上下文），仅波浪线标注下线 |
| `POST /ajax/reading-translate` | `POST /vocabulary/reading/translate` | 20s | 划词/选区翻译（**R141 起阅读器内置气泡已下线、本端点暂无调用方**；magiclens 直连 moon-well 不走此代理） |
| `POST /ajax/reading-translate-batch` | `POST /vocabulary/reading/translate-batch` | 20s | 段落批量翻译。R215 起前端只按「单个选中段」调用，译文渲染到右侧译文栏；端点形制与请求体不变 |
| `GET /ajax/reading-translate-all`（+ `/progress`） | 复用 translate-batch 链路 | — | 整页批量翻译与进度轮询 |
| `POST /ajax/reading-translate-book*`（`/status` `/cancel` `/retry`） | system LLM 任务队列（`/llm/task/*`）+ 完成事件写段落缓存 | — | 整本翻译：发起/进度/取消/重试 |
| `POST /ajax/reading-word-detail` | `GET /vocabulary/detail/{word}` | 120s | 单词详解（R124 对齐 magiclens v0.4.0；**R141 起内置「详」面板入口随气泡下线、本端点暂无调用方**） |
| `POST`（朗读代理 `/ajax/reading-tts`） | `POST /tts/speak` | 65s | 段落朗读，音频二进制透传；请求携带 `text` + `bookName`/`chapter`（各 trim 后截 200 字）——书籍上下文决定 moon-well 侧缓存分级：有上下文=书籍段落永久保留，无上下文=AI 临时语音 7 天清理 |
| `POST /ajax/reading-tts-cached` | `POST /tts/cached-audio` | 20s | 只读缓存取音频、miss 返回 404，**不触发合成**。R170 给伴读用：`synthesize_tts` 工具内已合成并扣过分，前端再走 `/tts/speak` 就是同一次朗读扣两遍 |
| `POST /ajax/reading-tts-book*`（`/status` `/retry` `/cancel`） | `POST /tts/speak`（daemon 逐段串行，`source=book-tts-batch`） | 单段 200s | 整本朗读预生成：管理员发起（`@admin_required`）、受理即返批次快照、合成在后台线程；命中缓存 0 扣，retry/重跑对已完成段免费快返。契约细节见 [whole-book-tts L3 §端点](../../project/_legacy/feat/whole-book-tts/design/whole-book-tts-design.md)（历史归档） |
| 段落「✨」AI 批注 | moon-well reading 伴读批注接口 | — | 背景/典故讲解，缓存语义见 moon-well reading HLD §4 |

- 鉴权：全部以**当前用户 JWT** 转发（`_moonwell_proxy`）；不走内网互信白名单——用户动作必须可归因。

### 1.1 整本连播（阅读器前端播放队列，R157）

标题栏「▶/❚❚/■」驱动 epub.js 播放队列，顺序逐段调用上面的朗读代理（同 `POST /tts/speak` 契约，**无新端点、无新契约**）：本章段耗尽自动 `rendition.next()` 翻章重建队列（空文字章节自动跳过、≤10 章），spine 尽头自动停；段内暂停/继续保留进度；当前块开播后才预取下一块（全程 ≤1 个在途合成——NAS 本地 TTS 是 CPU 瓶颈、MiMo 100 RPM）；>2000 字符长段切块连读（块的 moon-well 缓存键=切块原文，天然去重）；手动翻章/主题字号重渲染跟随重建（同章续听原块、换章从页首起播）；与单段朗读互斥让位。moon-well 与 web.py 零改动。

### 1.2 TED 原声伴听代理（R172，R200 改口径）

TED/博客类书的内容是**一段连续原声**（`ted-audio/<slug>.aac`），文本段落只是这段录音上的时间轴切片。故朗读必须分流：有原声走伴听，小说才走逐段 TTS。分流判据只能来自**运行时探测**（`/ajax/ted-audio` 是否返回 `audioUrl`），不能用 `calibre.bookFormat === 'TED'`——那是 Calibre 文件格式（epub/pdf），与 moon-well `BookFormatEnum.TED` 同名不同义，TED 书在 Calibre 里同样是 epub，该判断恒 false。

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/ted-audio` | `POST /book/ted-audio` | 15s | 取整段原声 `audioUrl` + 元信息（探测与播放起点） |
| `POST /ajax/ted-audio-paragraphs` | `POST /book/paragraph/list` | 15s | 段落时间轴 + 段落注册表（驱动 `.reading-tts-speaking` 高亮） |

- **入参口径（R200）**：浏览器只传 Calibre `bookId`；代理在本地库里解析出 `title`/`authors`，转发时改发 `{"bookName", "author"}`，**绝不再把 Calibre 书号当 moon-well 的 `bookId`**。两套自增序列只有巧合对齐才命中，错位时上游返 null、前端静默回落机器音（线上表现为「TED 仍播 TTS」）。
- **错误语义**：`bookId` 非数字 → 400（脏串不进上游）；本地库无此书 → 404（不把空书名送去上游当「未缓存」）；上游不可达 → 503。均带 `success:false`。
- 多作者以 `" & "` 连接，与 moon-well 导入时写入的 author 一致。

### 2. NCE 课级音频（`/nce/<book_id>`）

新概念英语课级播放页：音频存 MinIO（`magicbook/nce-audio/`），Range 流式播放 + manifest 缓存；方案 A 浏览器直连 MinIO。

### 3. 阅读进度与批注

| magicbook 端点 | 上游 | 说明 |
| --- | --- | --- |
| `POST /ajax/reading-progress` | **无（本仓 app.db）** | 账号级阅读位置（R213 / MB-17）：`{book_id, format, position, percent, page_current, page_total}` → `{success, percent, last_read_at}`；按 `(user_id, book_id, book_format)` upsert，`percent` 夹取到 0–100，`page_current` 不得超过 `page_total`。**唯一不代理 moon-well 的 reading 端点**——位置是阅读器自身状态，读写都在本进程 |
| 阅读位置恢复 | 同上表 | 阅读器进入时优先级：`reading_progress.position`（账户级，跨设备）→ 浏览器 localStorage（本机兜底）→ 书首 |
| Kobo 同步位置 | Kobo 通道自有 | `KoboReadingState.current_bookmark`（`progress_percent` / `content_source_progress_percent`），由 `cps/kobo.py` 读写；**网页端不写它**，两套位置互不覆盖 |

- 口径修订（R213，2026-10-23）：本节旧文「进度经 moon-well book 模块上报恢复」与实况不符——网页阅读器此前**没有**任何服务端位置，靠 epub.js 写 localStorage（设备级，换浏览器即丢）；`ub.ReadBook` 只有「未读/在读/读完」三态且 `last_time_started_reading` 仅 Kobo 通道写入。账号级位置自 R213 起由本表端点承载，与 moon-well 无关。
- 用户手写批注仍走 moon-well reading 段落批注接口（未变）。

### 4. 账号级 UI 偏好代理（`cps/routes/preferences.py`，R216）

引导已读与阅读主题存在 moon-well `user_ui_settings`（跨设备一致）；本仓只做鉴权转发。后端契约权威：moon-well R207 LLD（`docs/project/iterations/2026-10-ui-prefs/lld.md`，该模块暂无 L2）。

| magicbook 端点 | moon-well 端点 | 方法 | 超时 | 说明 |
| --- | --- | --- | --- | --- |
| `/ajax/ui-settings` | `/user/ui-settings` | GET | 8s | 读 `{onboardingSeen, onboardingSeenAt, readerTheme, updatedAt}`；未配置用户返回出厂视图（`false` / `null`），服务端不懒建行 |
| `/ajax/ui-settings/onboarding/close` | `/user/ui-settings/onboarding/close` | POST | 8s | 置账号级「引导已结束」，幂等：已 true 再调用不改首次时间 |
| `/ajax/ui-settings/reader-theme` | `/user/ui-settings/reader-theme` | POST | 8s | `{"theme":"darkTheme"}`；**代理层先按 5 个内置 key 白名单挡非法值 → 400**，不把脏值送上游成 500 |

- 三条全部 `@user_login_required`，带当前用户 JWT；401 / 上游 500 / 不可达 503 原样透传。
- `customTheme`（自定义颜色）**不在契约内**：只存浏览器 `localStorage`，任何一端都不落库。
- 消费侧失败口径：`GET` 读不到时引导**不自动弹**（fail closed）、主题保留本机值；`POST` 失败必须界面可见，不伪装成已保存。
- 页面路由：`GET /me` 渲染偏好页；`POST /me/preferences` 是本站原生表单（只写 `locale` 与 `default_language`，不代理 moon-well）。
- 阅读难度沿用既有端点：`GET /ajax/reading-settings`、`POST /ajax/reading-settings/hard-level`（见 vocabulary L2）。

## 调用方契约

- 依赖：moon-well（vocabulary/system/tts/reading/book）；失败语义沿用各后端契约（业务错误 HTTP 500 + `Result.code`）。
- **统一信封（X1 两端彩排实测，2026-10-16，详见 `docs/project/iterations/2026-10-arch-review/x1-contract-pair-rehearsal/lld.md`）**：
  后端 M4 起由框架兜底回 `{success, message, code, result, timestamp}`，本仓代理**原样透传 body 与状态码**——
  正常 200、凭证失效 401、上游业务失败 500、上游不可达由本仓自造 503 `{"success": false, "message": "… service unavailable"}`；
  若上游不是 moon-well（网关 HTML 等）则 404 + 非 JSON body 一并透传，**代理不把它包装成「无数据」**。
  消费侧口径：`common/api.js` 的 `unwrapStrict`（learning/credits）遇非信封即抛、`unwrapResult`（ai_chat）遇
  `success:false` 抛上游文案，但 **parse 失败返回 null 不抛**——用容错解包的页面必须自己判 `response.ok`。
- magicbook 内部：epub.js 渲染层与代理层解耦；i18n 经 `mbT()` 通道（language-i18n）。

## L3 与历史设计

- [阅读单词学习规格](../reading-vocabulary.md)（跨 reading / vocabulary 的静态实现说明，L3 性质）
- [阅读主题账号同步](../reading/features/reader-theme-sync.md)（R216：5 个内置主题跨设备、自定义仅本机、竞态口径）
- [引导导览](../learning/features/onboarding.md)（R216：账号级只自动邀请一次的状态机与失败口径）
- 历史设计（`docs/project/_legacy/feat/`）：[整本翻译设计](../../project/_legacy/feat/whole-book-translation/design/whole-book-translation-design.md) · [课级音频 LLD](../../project/_legacy/feat/nce-audio/design/lld.md)
