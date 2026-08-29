# 阅读器段落朗读（TTS）与沉浸式翻译 — 设计文档

日期：2026-08-29
状态：已批准（用户确认）

## 背景

magicbook（Calibre-Web 定制版）的 EPUB 阅读器已有生词标注与划词翻译能力。本次新增两个阅读功能：

1. **段落朗读**：每个自然段可通过 AI TTS 朗读，可配置 text-to-audio 模型。
2. **沉浸式翻译**：开启后在每个段落后追加 AI 中文译文，可随时关闭（类似沉浸式翻译插件）。

## 用户决策记录

| 决策点 | 结论 |
| --- | --- |
| TTS 方案 | AI TTS（OpenAI 兼容 `/audio/speech`）为主 + 浏览器 `speechSynthesis` 兜底，引擎可切换 |
| 翻译链路 | moon-well 新增批量翻译接口，一次 LLM 调用翻译整页段落 |
| 目标语言 | 固定英→中（与划词翻译一致） |
| TTS 配置入口 | 复用 `/ai/admin` 全局配置，管理员统一管理 |
| 朗读按钮显示 | hover 段落时浮现小图标，不打断阅读 |
| 翻译开关 | 阅读器顶部工具栏图标按钮，状态存 localStorage，译文带缓存 |

## 架构

```
magicbook 前端 (read.html + js/reading/epub.js)
  ├─ 每段 hover 浮现朗读按钮 → POST /ai/tts → 播放 mp3（失败降级 speechSynthesis）
  └─ 工具栏"译"开关 → POST /ajax/reading-translate-batch → 段落后插入译文

magicbook 后端
  ├─ POST /ai/tts            → TTS Provider（OpenAI 兼容 /audio/speech），内存 LRU 缓存
  ├─ POST /ajax/reading-translate-batch → 代理 moon-well 批量翻译（复用 _moonwell_proxy）
  └─ /ai/admin               → 新增 TTS 配置块（AiProvider 表 provider_name="tts" 专用行）

moon-well
  └─ POST /vocabulary/reading/translate-batch → 一次 LLM 调用批量翻译，返回同序数组
```

## 详细设计

### moon-well：批量翻译

- `ReadingTranslationBatchRequest`：`paragraphs: List<String>`（1~20 项，每项 1~2000 字符，Bean Validation 校验）。
- `ReadingVocabularyService.translateBatch()`：构造编号列表 prompt（要求只返回 JSON 数组、同序同量、简洁自然中文）→ `llmFacade.simpleCall` → 容错解析（剥 markdown 围栏、数量不匹配时截断/补空）。
- `ReadingVocabularyController` 新增 `POST /vocabulary/reading/translate-batch`，返回 `Result<Map>`（`{"translations": [...]}`）。
- 复用现有 JWT 拦截器鉴权与全局异常处理。

### magicbook：TTS 后端

- `AiProvider` 表新增专用行 `provider_name="tts"`，复用 `api_base / api_key_encrypted` 列，`models_json` 存 `{"model": "...", "voice": "...", "models": [...], "voices": [...]}`——无数据库迁移。
- `cps/ai/tts.py`：`synthesize_speech(api_base, api_key, model, voice, text, timeout) -> bytes`，OpenAI 兼容 `POST {api_base}/audio/speech`，`response_format=mp3`。
- `POST /ai/tts`（登录用户）：校验文本 1~2000 字符 → 取 TTS 配置 → 合成 → 流式返回 `audio/mpeg`；内存 LRU（128 条，text hash → bytes）。未配置返回 JSON 错误。
- `/ai/admin` 表单新增"AI 朗读服务"配置块（api_base/api_key/model/voice，测试合成按钮）。

### magicbook：批量翻译代理

- `POST /ajax/reading-translate-batch`（登录用户）：校验 1~20 段、每段 ≤2000 字符 → `_moonwell_proxy("/vocabulary/reading/translate-batch", payload, 60, ...)`。

### magicbook：前端

- **段落工具注入**：`reader.rendition.on('rendered')` 中对 iframe 文档的 `p/li/blockquote/h1-h6` 等有文本块级元素注入朗读按钮；CSS 注入 iframe，段落 `:hover` 时浮现；翻页重渲染自动重新注入。与生词标注共存（互不干扰）。
- **朗读**：全局单例 `Audio`，一次一段；播放中可停止、切段自动停止；AI 失败 toast 并自动降级 `speechSynthesis`（en 声音）重试一次；段落 >2000 字符截断。
- **沉浸式翻译**：工具栏"译"按钮开关（localStorage 记忆）；开启时收集当前页段落 → 批量翻译 → 每段下插入 `<div class="reading-translation">`（小字号浅色，随主题）；译文缓存 localStorage（书 key + 段落文本 hash，上限 500 条 LRU）；关闭立即移除译文但保留缓存；翻页时开关开着自动翻译新页。
- **设置**：阅读设置弹窗新增朗读引擎选择（AI 朗读 / 浏览器本地），localStorage 记忆。
- `window.calibre` 新增 `readingTtsUrl / readingTranslateBatchUrl / ttsEnabled`。

## 错误处理

- 新接口均需登录；AJAX 显式带 `X-CSRFToken`。
- API key 仅服务端加解密。
- moon-well 401 → 代理自动刷新 token；失败提示重新登录。
- 翻译失败 → 译文区显示"翻译失败，点击重试"。

## 测试

- moon-well：`ReadingVocabularyServiceTest`（mock LlmFacade）覆盖正常 JSON / 围栏包裹 / 数量不匹配 / 空输入 / 参数校验。
- magicbook：pytest mock requests，覆盖 TTS 路由校验与合成调用、批量代理参数校验。
- 浏览器手工验收：hover 按钮、播放/停止、引擎切换、翻译开关、缓存、翻页重注入。

## 明确不做（YAGNI）

- 整章连播/自动翻页朗读、逐句高亮。
- 目标语言配置（固定英→中）。
- TTS 音频磁盘持久化（仅内存缓存）。
