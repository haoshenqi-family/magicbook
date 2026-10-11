# response 归档：R138（2026-10-08）

> 从 response.md 原样搬移（2026-10-11 R152 写入使窗口达 11 个 request，按「写入即检查」搬最旧条目）。只搬移原文，未总结、未改写、未改编号。

## 2026-10-08（R138 朗读请求补 bookName/chapter）

### R138（朗读请求补 bookName/chapter——书籍段落音频不再被当临时语音清理）

- **背景**：moon-well R130 排查（同一段落连听两次不走缓存）顺带发现——`epub.js` 的 `speakWithAi` 只发 `{text}`，而 moon-well R128 的缓存分级按「有无书籍上下文」决定去向，于是**阅读器里每一段音频都被判成 AI 临时语音**，落 `reading-tts/temp/<日期>/`、7 天后被每日任务清理；L1 写的「书籍段落永久缓存、重听零等待」在阅读器链路上并不成立（翻译链路早就在发 bookName/chapter，朗读漏了）。
- **改动**：①`cps/static/js/reading/epub.js` `speakWithAi` 请求体补 `bookName: calibre.bookName || ''` 与 `chapter: currentChapterTitle()`（与 `translateParagraphJob` 同口径，翻页后 `#chapter-title` 随 MetaController 修正保持新鲜）；②`cps/web.py` `reading_tts` 代理按翻译路由同规格清洗两字段（`str(... or "").strip()[:200]`）——这两个值会写进 ES 段落文档，不能由客户端无限撑大，缺省补空串保持「无上下文=临时档」的原语义；③L1/L2 补缓存分级依赖调用方携带上下文的契约说明，moon-well `docs/tts/hld/hld.md` 同步注明「阅读器已携带、AI 伴读不携带」。
- **验证**：开发态闸门 `.venv/bin/python -m pytest tests/test_reading_tts.py` = 10 通过（新增 2 例：上下文原样转发含 trim、超长截 200 且非字符串归一；改 1 例断言裸 text→带两字段）；受影响模块回归 `test_no_duplicate_js_lines + test_reading_settings + test_reading_translation(+_r75) + test_reading_vocabulary + test_reading_tts` = **63 通过 0 失败**。未跑全量（正式发布时按 R131 两级闸门补跑）。
- **边界**：`paragraphSpeechText` 的 `\s+`→单空格归一在 moon-well 侧再 trim，缓存键与后端一致，本次不动；PDF/TXT 阅读器无段落朗读入口（`readingTtsUrl` 仅 epub.js 与 read.html 使用）；magiclens 网页划词朗读无书籍概念，继续走临时档，是正确语义不是缺口。
- **部署状态**：仅本地提交，**未 push**（push develop 触发 fnOS 构建自动上线，待用户单独确认）。
- **文档落位注**：`docs/readme/reading.md`（L1）与 `docs/reading/hld/hld.md`（L2）目前仍是并行会话未提交的 L1/L2 骨架（两个目录尚未纳入 Git），本次两处文档行留在工作区随其批次落地，避免把他人整份新文档代提交。
- **总结**：requests.md 占号 R138（第 4 行「当前最大」随之更新；同文件 135–137 三条与 response.md R135 一节为并行会话未提交内容，随本次提交代为落地，未改写其文字）；response.md 追加本条，窗口 9 条 ≤10 未触发搬移；冲突记录：R138 未被占用。
