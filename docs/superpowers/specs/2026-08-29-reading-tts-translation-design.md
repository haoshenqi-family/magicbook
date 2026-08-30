# 阅读器段落朗读（TTS）与沉浸式翻译 — 设计文档

日期：2026-08-29
状态：已批准（用户确认）

> **变更记录（2026-08-29 v2）**：TTS 链路改为 **moon-well 中转 + 阿里云百炼（DashScope）**。
> magicbook 放弃直连 OpenAI 兼容 `/audio/speech` 的适配（`cps/ai/tts.py`、`/ai/tts`、
> `/ai/test_tts`、admin TTS 面板均已移除；旧 `provider_name="tts"` 行在下一次保存
> admin 配置时清理）。原因：百炼 TTS 走 DashScope 私有协议（嵌套请求体 + 非流式
> 返回 `output.audio.url` OSS 链接需二次下载），且 TTS 仅在百炼北京地域可用，
> 统一由 moon-well 适配可复用其鉴权与配置体系。原设计中的 TTS 段落已按此更新。

> **变更记录（2026-08-30 v3）**：翻译交互改为**段落级按钮 + 手动整页翻译**。
> 原实现翻页/新章节自动整页批量翻译，一次 LLM 请求翻译整页导致卡顿。现改为：
> 每段末位「译」按钮（与朗读按钮并列）单击仅翻译该段（优先命中缓存，瞬时显示）；
> 工具栏「译」保留为手动「翻译本页」（点击批量翻译当前可见页，再点移除译文）；
> 翻页/新章节只回填已缓存译文，**不再自动发起任何 LLM 请求**。批量翻译接口
> （`/ajax/reading-translate-batch`）复用不变，单段即 `paragraphs:[text]`。

## 背景

magicbook（Calibre-Web 定制版）的 EPUB 阅读器已有生词标注与划词翻译能力。本次新增两个阅读功能：

1. **段落朗读**：每个自然段可通过 AI TTS 朗读，可配置 text-to-audio 模型。
2. **段落翻译/整页翻译**：每段末位按钮单击追加 AI 中文译文（再点取消）；工具栏「译」手动批量翻译当前页，可随时关闭（类似沉浸式翻译插件）。

## 用户决策记录

| 决策点 | 结论 |
| --- | --- |
| TTS 方案 | ~~AI TTS（OpenAI 兼容 `/audio/speech`）~~ **v2：moon-well 中转到阿里云百炼** + 浏览器 `speechSynthesis` 兜底，引擎可切换 |
| 翻译链路 | moon-well 批量翻译接口；~~开启后翻页自动整页翻译~~ **v3：段落按钮单段翻译 + 工具栏手动整页翻译，翻页仅回填缓存** |
| 目标语言 | 固定英→中（与划词翻译一致） |
| TTS 配置入口 | ~~复用 `/ai/admin` 全局配置~~ **v2：moon-well `tts:` 配置（环境变量 DASHSCOPE_API_KEY 等）** |
| 朗读按钮显示 | hover 段落时浮现小图标，不打断阅读 |
| 翻译入口 | 段落末位「译」按钮（hover 浮现）+ 工具栏「译」整页开关，状态存 localStorage，译文带缓存 |

## 架构

```
magicbook 前端 (read.html + js/reading/epub.js)
  ├─ 每段 hover 浮现 ▶ 朗读按钮 → POST /ajax/reading-tts → 播放 mp3（失败降级 speechSynthesis）
  ├─ 每段 hover 浮现「译」按钮 → 单段翻译（缓存命中即时显示，否则 POST /ajax/reading-translate-batch）
  └─ 工具栏「译」→ 手动批量翻译当前可见页；翻页仅回填缓存（不请求）

magicbook 后端
  ├─ POST /ajax/reading-tts → 代理 moon-well /tts/speak（二进制透传，复用 _moonwell_proxy + binary）
  └─ POST /ajax/reading-translate-batch → 代理 moon-well 批量翻译（复用 _moonwell_proxy）

moon-well
  ├─ POST /vocabulary/reading/translate-batch → 一次 LLM 调用批量翻译，返回同序数组
  └─ POST /tts/speak → 适配百炼 DashScope 非实时合成（含音频下载 + LRU 缓存）
```

## 详细设计

### moon-well：批量翻译

- `ReadingTranslationBatchRequest`：`paragraphs: List<String>`（1~20 项，每项 1~2000 字符，Bean Validation 校验）。
- `ReadingVocabularyService.translateBatch()`：构造编号列表 prompt（要求只返回 JSON 数组、同序同量、简洁自然中文）→ `llmFacade.simpleCall` → 容错解析（剥 markdown 围栏、数量不匹配时截断/补空）。
- `ReadingVocabularyController` 新增 `POST /vocabulary/reading/translate-batch`，返回 `Result<Map>`（`{"translations": [...]}`）。
- 复用现有 JWT 拦截器鉴权与全局异常处理。

### moon-well：百炼 TTS（v2 新增）

- `TtsProperties`（`@ConfigurationProperties(prefix="tts")`）：`api-key / base-url / model / voice / timeout-ms`，环境变量 `DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL / TTS_MODEL / TTS_VOICE / TTS_TIMEOUT_MS`。
- `ReadingTtsService.speak(text)`：DashScope 非实时协议 `POST {base}/api/v1/services/audio/tts/SpeechSynthesizer`（嵌套 `input`：text/voice/format=mp3）→ 解析 `output.audio.url` → 下载音频字节。`SHA-256(text|model|voice)` 为键的 LRU 缓存（128 条）。未配置 api-key 抛 `GlobalException`（全局异常处理器返回 JSON+500）。
- `ReadingTtsController`：`POST /tts/speak`，JWT 拦截器自动鉴权，成功返回 `audio/mpeg` 字节。

### magicbook：TTS 代理（v2 替换原直连方案）

- `POST /ajax/reading-tts`（登录用户）：校验文本 1~2000 字符 → `_moonwell_proxy("/tts/speak", payload, 65, binary=True)`。
- `_moonwell_proxy` 增加 `binary` 参数：按原始字节透传响应体（音频/JSON 错误均适用），令牌 401 自动刷新逻辑不变。
- 前端 `ttsConfigured` 改为登录即可用（AI 朗读依赖 moon-well 会话令牌，与阅读词汇功能同源）。
- ~~`cps/ai/tts.py`、`/ai/tts`、`/ai/test_tts`、admin TTS 面板~~（已移除，见变更记录）。

### magicbook：批量翻译代理

- `POST /ajax/reading-translate-batch`（登录用户）：校验 1~20 段、每段 ≤2000 字符 → `_moonwell_proxy("/vocabulary/reading/translate-batch", payload, 60, ...)`。

### magicbook：前端

- **段落工具注入**：`reader.rendition.on('rendered')` 中对 iframe 文档的 `p/li/blockquote/h1-h6` 等有文本块级元素注入朗读按钮与段落翻译按钮；CSS 注入 iframe，段落 `:hover` 时浮现；翻页重渲染自动重新注入。与生词标注共存（互不干扰）。
- **朗读**：全局单例 `Audio`，一次一段；播放中可停止、切段自动停止；AI 失败 toast 并自动降级 `speechSynthesis`（en 声音）重试一次；段落 >2000 字符截断。
- **段落翻译**：每段末位"译"按钮（与朗读按钮并列，悬停浮现），单击仅翻译该段（单段请求，优先命中缓存）；已有译文时再点一次取消该段译文；失败时译文区显示"翻译失败，点击重试"。
- **整页翻译**：工具栏"译"按钮（localStorage 记忆）为手动全部翻译——开启时批量翻译当前可见页并逐段插入 `<div class="reading-translation">`（小字号浅色，随主题），关闭立即移除译文。翻页/新章节不再自动发起整页批量请求（避免卡顿），仅回填已缓存译文；译文缓存 localStorage（书 key + 段落文本 hash，上限 500 条 LRU），关闭不清缓存。
- **设置**：阅读设置弹窗新增朗读引擎选择（AI 朗读 / 浏览器本地），localStorage 记忆。
- `window.calibre` 新增 `readingTtsUrl / readingTranslateBatchUrl / ttsConfigured`。

## 错误处理

- 新接口均需登录；AJAX 显式带 `X-CSRFToken`。
- 百炼 DASHSCOPE_API_KEY 仅配置在 moon-well 服务端，不进 magicbook。
- moon-well 401 → 代理自动刷新 token；失败提示重新登录。
- TTS 失败（JSON 错误透传）→ 前端 toast 并降级浏览器语音；翻译失败 → 译文区显示"翻译失败，点击重试"。

## 测试

- moon-well：`ReadingVocabularyServiceTest`（mock LlmFacade）覆盖批量翻译各分支；`ReadingTtsServiceTest`（spy 覆写 RestTemplate 工厂）覆盖 DashScope 协议、音频下载、缓存复用、未配置、解析/网络失败。
- magicbook：pytest mock requests，覆盖 `/ajax/reading-tts` 代理校验与二进制透传、批量代理参数校验。
- 浏览器手工验收：hover 按钮、播放/停止、引擎切换、段落「译」按钮（翻译/取消/缓存命中/失败重试）、工具栏整页翻译开关、翻页重注入与缓存回填（无自动请求）。

## 明确不做（YAGNI）

- 整章连播/自动翻页朗读、逐句高亮。
- 目标语言配置（固定英→中）。
- TTS 音频磁盘持久化（仅内存缓存）。
