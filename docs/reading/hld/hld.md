# reading · HLD（设计概要）

> 读者：模块调用者/集成者。magicbook 是阅读前端，本模块对 moon-well 是**薄代理层**：请求带当前用户的 moon-well JWT 转发，**token 不下发浏览器**。后端契约的唯一权威是 moon-well 对应 L2，本文件只维护「magicbook 端点 → moon-well 端点」的映射与超时口径。

## 能力边界

阅读器页（EPUB/PDF/TXT）与阅读相关代理、NCE 音频播放。词汇判定/详解/测试的后端语义不在本模块（见 vocabulary HLD 与 moon-well）。

## 子功能概要

### 1. 阅读能力代理（cps/web.py，`/ajax/reading-*`）

| magicbook 端点 | moon-well 端点 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/reading-vocabulary` | `POST /vocabulary/reading/analyze` | 15s | 生词判定（容忍 moon-well 重启后 ES 首连慢响应）；epub.js 仍每页上送（喂阅读事件流 + AI 伴读生词上下文），仅波浪线标注下线 |
| `POST /ajax/reading-translate` | `POST /vocabulary/reading/translate` | 20s | 划词/选区翻译（**R141 起阅读器内置气泡已下线、本端点暂无调用方**；magiclens 直连 moon-well 不走此代理） |
| `POST /ajax/reading-translate-batch` | `POST /vocabulary/reading/translate-batch` | 20s | 段落批量翻译 |
| `GET /ajax/reading-translate-all`（+ `/progress`） | 复用 translate-batch 链路 | — | 整页批量翻译与进度轮询 |
| `POST /ajax/reading-translate-book*`（`/status` `/cancel` `/retry`） | system LLM 任务队列（`/llm/task/*`）+ 完成事件写段落缓存 | — | 整本翻译：发起/进度/取消/重试 |
| `POST /ajax/reading-word-detail` | `GET /vocabulary/detail/{word}` | 120s | 单词详解（R124 对齐 magiclens v0.4.0；**R141 起内置「详」面板入口随气泡下线、本端点暂无调用方**） |
| `POST`（朗读代理） | `POST /tts/speak` | 65s | 段落朗读，音频二进制透传；请求携带 `text` + `bookName`/`chapter`（各 trim 后截 200 字）——书籍上下文决定 moon-well 侧缓存分级：有上下文=书籍段落永久保留，无上下文=AI 临时语音 7 天清理 |
| 段落「✨」AI 批注 | moon-well reading 伴读批注接口 | — | 背景/典故讲解，缓存语义见 moon-well reading HLD §4 |

- 鉴权：全部以**当前用户 JWT** 转发（`_moonwell_proxy`）；不走内网互信白名单——用户动作必须可归因。

### 2. NCE 课级音频（`/nce/<book_id>`）

新概念英语课级播放页：音频存 MinIO（`magicbook/nce-audio/`），Range 流式播放 + manifest 缓存；方案 A 浏览器直连 MinIO。

### 3. 阅读进度与批注

进度经 moon-well book 模块上报恢复；用户手写批注走 moon-well reading 段落批注接口。

## 调用方契约

- 依赖：moon-well（vocabulary/system/tts/reading/book）；失败语义沿用各后端契约（业务错误 HTTP 500 + `Result.code`）。
- magicbook 内部：epub.js 渲染层与代理层解耦；i18n 经 `mbT()` 通道（language-i18n）。

## L3 索引

- [整本翻译设计](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/whole-book-translation/design/whole-book-translation-design.md)
- [阅读单词学习规格](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/reading-vocabulary.md)
- [课级音频 LLD](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/nce-audio/design/lld.md)
