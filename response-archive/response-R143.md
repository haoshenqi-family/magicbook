# response 归档：R143（2026-10-10）

> 从 response.md 原样搬移（2026-10-11 R157 写入使窗口达 11 个 request，按「写入即检查」轮转最早一条。只搬移原文，未总结、未改写、未改编号。）

## 2026-10-10（R143：修正 R141 的隐藏边界——段落翻译恢复）

### R143（只隐藏 magiclens 已经做了的部分，不重复、不打架）

- **用户纠偏原文**：「不对，现在 magicbook 段落翻译不见了。我的想法是 magiclens 已经做了的部分 magicbook 就先隐藏掉，不要重复，不要打架」。R141 我按用户选的「阅读器 AI 能力整体让位」把段落悬停「译」按钮一起收了，**是我把边界划过头**——用户这条把口径钉死为「**只下线 magiclens 已实现的**」。
- **依据（先查对方能力表再划界）**：magiclens `README.md` 当前状态表——划词翻译 ✅、单词详解 ✅、生词智能高亮 ✅（v0.5.0；v0.7.2 起明确支持 magicbook 阅读器 iframe 正文）、标记认识/生词 ✅，而 **「段落整页翻译｜规划 P1｜`translate-batch`」尚未实现**。故：气泡 + 波浪线继续下线，段落「译」按钮恢复。
- **交付**：`epub.js` 开关改名 `READER_BUILTIN_AI_UI_ENABLED` → **`LENS_OVERLAP_UI_ENABLED`**（名字如实描述它管的是「与 lens 重叠的那两块 UI」，不再是含义过宽的「AI 能力」），闸门口径注释重写并把「magiclens 未做的一律保留」写进保留清单；`injectParagraphTools` 里段落 `.reading-translate-btn` 的注入**去掉开关门控**，恢复无条件注入；`translateSelection` / `markVocabulary` 两处闸门不变。
- **测试反向锁定**：`tests/test_reader_lens_handoff.py` 原 `test_paragraph_translate_button_not_injected`（锁「不注入」）改为 `test_paragraph_translate_button_not_gated`，断言注入条件里**不得出现开关名**——R141 这个越界错误以后被改回来会直接红。文件 docstring 同步改写边界口径。开发态跑 `test_reader_lens_handoff + test_reading_vocabulary + test_no_duplicate_js_lines + test_i18n_seed_contract + test_onboarding_tour` → **63 passed**；`node --check epub.js` 通过。
- **文档三级回改**：L1 `docs/readme/reading.md` 补回「段落翻译」条目、`docs/readme/readme.md` 模块表改「段落/整页/整本翻译」并修快速开始第 2 步（该步 R141 时漏改，仍写着「划词即翻译、生词自动标波浪线」）；L2 `docs/vocabulary/hld/hld.md` 能力边界补「段落/整页翻译不在隐藏范围」；L3 `docs/reading-vocabulary.md` 状态注记重写为「R141 设、R143 收窄」并记录越界教训。全仓已无 `READER_BUILTIN_AI_UI_ENABLED` 残留引用（仅 `tests/__pycache__` 编译产物）。
- **复探上游（校准昨日记录）**：本日用同一浏览器探针重测——`POST /ajax/reading-translate-batch` **200**，返回真实译文（昨日为 500「翻译服务暂时不可用」，已不复现，疑与 R142 会话定位的 LLM/TTS 额度与超时链路同源，非本仓改动所致）；`POST /ajax/reading-translate` 200（词典）；`POST /ajax/reading-word-detail` 仍 **401 code 102「未登录」**（该端点当前无前端调用方，不影响段落翻译恢复）。结论：**恢复段落「译」按钮后，线上点开应有真实译文**。
- **待验收**：恢复后的段落「译」按钮只能在部署后于真浏览器看到（本机无 calibre 书库）；本轮改动当时**已提交未推送**。（后续状态见下一条「上线与真浏览器实测」——已推已验。）
- **总结**：requests.md 本条 R143（占号前先确认 142 已被并行会话占用，续编 143 并即刻单独 commit 锁号）；冲突记录：本条写入前 `response.md` 已被 R142 会话追加 25 行（整本 TTS 预热），采用 append 未触碰其内容；`docs/readme/reading.md`、`docs/vocabulary/hld/hld.md` 仍是 R129 会话 untracked 文件中的改动，随本轮一并提交时会在提交信息注明代提交归属。
- **上线与真浏览器实测（同轮，用户发话 push）**：推前跑全量 `pytest tests/` → **388 passed / 0 failed**（先 `git fetch` 确认 ahead 2 / behind 0，基线即待推内容）；推 `d0310ad9..0f6f7a8d`，fnOS 第 2 次探测命中：线上 `epub.js` 含 `LENS_OVERLAP_UI_ENABLED = false` 且已无旧开关名、段落按钮注入条件不再带开关（112,213 → 112,540 字节）。`/read/146/epub` 实测：段落「译」按钮 **23 个**（与朗读/批注/伴读同数，即每段都在）、生词波浪线 span 仍 **0**、内置气泡仍不出现；点某段「译」→ `POST /ajax/reading-translate-batch` **200**，1.2s 后该段下方渲染出真实中文译文；数秒后再查该 div 已消失——是既有的「译文自动隐藏（默认每 100 词 5 秒、最短 5 秒）」设计行为，非本次缺陷。踩坑记录：前一次探针脚本自身点了两次（展开后又被其清理逻辑收起）且超出 15s 上限，先把证据搞混过，判据要回到网络状态码 + 单次动作。
