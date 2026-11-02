# 阅读器四项增强设计（划词词典发音 / 上下文翻译 / 并发整页翻译 / AI 伴读上下文）

日期：2026-08-30
前置：`2026-08-29-reading-tts-translation-design.md`（v3：段落级翻译按钮）
关联：moon-well `docs/feat/nacos-prompt-registry/design/nacos-prompt-registry-design.md`（用户已有设计，本设计与其对齐）

## 1. 背景与目标

1. **划词翻译（单词）改用免费在线词典**：不再依赖 ES 词典（解耦家里 ES 部署），显示简洁译文并支持发音。
2. **段落翻译带书籍上下文**：LLM 知道当前书名与章节，人名/地名/术语译法全书一致。
3. **整页翻译改逐段并发**：一次 LLM 请求翻译整页太慢太卡；改为每段一个请求并发执行，响应到达即渲染。
4. **AI 伴读注入章节与生词**：system prompt 告诉 LLM 当前章节、当前页用户不熟悉的单词。
5. **以上系统提示词全部模板化**：Nacos Prompt Registry + 本地默认；Nacos 存在则覆盖本地，Nacos 稍后接入。

## 2. 用户决策记录

| 决策点 | 用户选择 |
|---|---|
| 词典来源 | 放弃有道（需付费凭证）；放弃 ES 词典；改用免费在线词典 |
| 词典选型 | 金山词霸 suggest 接口（无 key、中文释义、实测覆盖好）；查不到降级 LLM |
| 句子/短语划词 | 保留现有 LLM 翻译 |
| 单词发音 | 浏览器 speechSynthesis（金山接口无音频字段） |
| 生词来源 | 当前页陌生词（vocabularyRecords unknown=true，上限 30） |
| 模板语法 | 对齐用户自己的 nacos-prompt-registry 设计：`{{var}}`、静态默认清单、`render(key, vars)` 签名 |

## 3. 金山词霸词典（moon-well）

- 端点：`https://dict-mobile.iciba.com/interface/index.php?c=word&m=getsuggest&nums=1&is_need_mean=1&word={word}`
- 响应：`{"message":[{"key":"word","paraphrase":"n.词义…"}]}`
- 新增 `vocabulary/service/IcibaDictClient`（@Component）：
  - `lookup(word)`：仅接受 `message[0].key` 与查询词大小写不敏感相等的记录（suggest 会模糊匹配，防串词）；`paraphrase` 空视为未命中
  - LRU 缓存 512 条（accessOrder，含未命中占位）；3s 超时；任何异常静默返回 null（不阻断业务）
  - `buildRestTemplate()` 包级可见，测试可覆写
- `ReadingVocabularyService.translate()`：单词正则命中 → iciba 释义（source="dictionary"）；未命中/查不到 → 原有 LLM 路径。**ES 词典不再参与划词翻译**（analyze 生词标注链路不变，仍走 ES）。

## 4. 段落/整页翻译（moon-well + magicbook）

### 4.1 请求上下文

- `ReadingTranslationBatchRequest` 新增可选 `bookName`、`chapter`（各 ≤200 字符，@Size 校验 + 服务端防御截断）
- magicbook `/ajax/reading-translate-batch` 透传两字段（trim + 截断 200）；超时从 60s 降为 20s（现在是单段一次调用）
- 前端（单段按钮与整页并发）随请求发送 `calibre.bookName` + `currentChapterTitle()`

### 4.2 整页翻译并发（magicbook epub.js）

- `applyImmersiveTranslation` 重写：收集可见未翻译段落后，**并发池（限 4）**逐段调用 `paragraphs:[text]`（复用现有批量接口，后端零改动）
- 每段独立成功/失败：成功即渲染 + 写缓存；失败显示「翻译失败，点击重试」（现有逻辑）
- `translationInFlight` 语义改为「仍有段落在飞行中」；全部完成后处理 `translationRetryPending`

## 5. AI 伴读上下文（magicbook）

- epub.js 在 `window.AICompanion` 上注册（复用 ai_page_extract.js 桥接模式）：
  - `getChapter()` → `currentChapterTitle()`
  - `getUnfamiliarWords()` → `vocabularyRecords` 中 `unknown=true` 的词，上限 30
- `ai_chat.js` 聊天请求新增 `chapter`、`unfamiliar_words` 字段
- `/ai/chat` 路由提取两字段（chapter 截断 200，生词列表清洗后上限 30）传入 `build_system_prompt`
- system prompt 新增「## Current Chapter」「## Unfamiliar words on this page」两节，LLM 可主动用简单方式解释生词

## 6. 提示词模板（两仓库，同一模型）

对齐用户已有设计 `nacos-prompt-registry-design.md`：`{{var}}` 语法、静态默认清单、优先 Nacos 覆盖本地、Nacos 稍后接入。

### 6.1 moon-well `system/llm/prompt/`

| 类 | 职责 |
|---|---|
| `PromptDefinitions` | 静态默认模板清单（key + template + 变量说明）。key：`reading-paragraph-translate`（带书名/章节）、`reading-paragraph-translate-plain`（无上下文兜底） |
| `PromptRenderer` | `@Service`，`render(key, vars)`：`{{var}}` 替换。**模板解析留有 Nacos 覆盖缝**——接入 Registry 后此处优先读 Nacos，业务调用点零改动 |

将来接入时与 `NacosPromptRegistryService.render(key, vars, fallbackTemplate)` 对接：本类的模板解析即 fallback 分支。

模板内容（默认）：

```text
# reading-paragraph-translate
你是一位专业译者，正在翻译英文书籍《{{bookName}}》的「{{chapter}}」章节。
将后面编号的英文段落翻译成简洁、自然的中文：人名、地名、专有名词的译法保持与全书一致。
只返回一个 JSON 字符串数组：数组第 i 项是第 i 段的中文翻译，不要解释，不要 markdown 代码块。

# reading-paragraph-translate-plain
将后面编号的英文段落翻译成简洁、自然的中文。
只返回一个 JSON 字符串数组：数组第 i 项是第 i 段的中文翻译，不要解释，不要 markdown 代码块。
```

书名/章节缺失时以「未知书籍」「未知章节」占位。编号段落列表由代码追加在模板之后。

### 6.2 magicbook `cps/ai/prompts.py`

- `DEFAULT_PROMPTS` 字典 + `render_prompt(key, **variables)`（`{{var}}` 替换）
- key：`chat-system` —— 现有 build_system_prompt 的完整文本模板化，占位符 `{{title}}/{{authors}}/{{tags_section}}/{{description_section}}/{{chapter}}/{{page_context}}/{{unfamiliar_words}}/{{memory}}/{{extra_section}}`
- 条件段（tags/description/extra）由调用方预计算为变量值，模板保持 Registry 单模板模型
- 预留 Nacos 覆盖缝（`get_prompt(key)` 函数内先查注册表，稍后接入）

## 7. 划词翻译发音（magicbook epub.js）

- 翻译气泡新增 🔊 按钮（`.translation-speak`，reader.css）：点击用 `window.speechSynthesis` 朗读**选中的原文**
- 提取 `buildEnglishUtterance(text)`（含英文音色挑选），`speakWithBrowser` 与气泡发音共用
- 单词/句子气泡均可用（发音对象是选中文本本身）

## 8. 错误处理

| 场景 | 行为 |
|---|---|
| 金山词典超时/异常/未命中 | 静默降级 LLM 翻译，不 500 |
| 金山返回模糊匹配（key 不等） | 视为未命中 |
| 并发翻译单段失败 | 仅该段显示重试提示，其余段不受影响 |
| chapter 解析失败（无 TOC） | 发送空串，moon-well 用「未知章节」占位 |
| 模板 key 缺失 | moon-well 抛 IllegalArgumentException（配置错误应显式失败）；magicbook KeyError 同理 |
| CSRF 过期 | 现有 reloadIfCsrfBlocked 自愈逻辑复用 |

## 9. 测试计划

- moon-well（JUnit + Mockito）：
  - `IcibaDictClientTest`：释义解析、key 不匹配拒绝、异常静默、缓存命中（二次调用零网络）、未命中缓存
  - `ReadingVocabularyServiceTest`：新增 translate 单词词典命中/未命中降级 LLM；translateBatch 带书名章节 → prompt 捕获断言；无上下文 → plain 模板
  - `PromptRendererTest`：变量替换、未知 key 抛错
- magicbook（pytest）：
  - `test_ai_memory.py`：chapter/生词注入、缺省占位
  - 新增 `test_ai_prompts.py`：render_prompt 替换
  - `test_reading_tts.py`：batch 代理透传 bookName/chapter、超长截断
- 前端：`node --check epub.js`；浏览器手工验收（词典气泡+发音、段落上下文翻译、并发整页、伴读上下文）

## 10. 部署变更

- 无数据库变更、无新增环境变量（金山词典无凭证）
- moon-well 与 magicbook 均需重新部署镜像
- Nacos Prompt Registry 接入后：控制台建 `reading-paragraph-translate` / `reading-paragraph-translate-plain` / `chat-system`（magicbook 侧另议）即可在线改提示词
