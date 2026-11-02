> 归档：R205（每日学习「单词编故事」Hub 第八张卡）原样搬移自 `response.md`。
> 2026-10-23 R212 写入触发轮转搬移，只搬移原文、不总结、不改写。

## 2026-10-22（R205：每日学习「单词编故事」——Hub 第八张卡 + 子页面 + SSE 代理）

### R205（承接 moon-well R200；用户：「每日学习新增一个功能，单词编故事，根据我最近需要复习的单词或者我指定的一批单词，让 AI 编一个小故事来帮助我记忆理解。」）

- **页面**：`/learning/story`，双入口（今天到期的词一键 / 粘贴词表），默认 6 词、上限 8；结果面板含标题、正文（目标词加粗）、词表卡（释义 / 原句 / `missing` / `uncached` 标签）、整篇朗读与入账提示；历史点击取详情回看。
- **代理**：`/ajax/learning/story/generate|generate/stream|history|detail`。写作专用 SSE 代理泛化为 `_llm_sse_proxy(path, label, payload_builder)`；`_story_payload` 只放行 `source/count/words/cefrLevel`，manual 的整段粘贴折成单元素 list，词长 ≤2000；detail 的 id 只认数字。
- **前端复用**：`postSse` 下沉 `learning-common.js`，写作页改为 `MB.postSse`；故事页只在建连失败 / 未收到首事件时回退 JSON，收到 `status`/`ping` 后断网不重试（故事可能已落库并入账）。
- **Hub / i18n / 配图**：中枢新增第八张卡（`data-key="story"`、`data-strand="language"`）与 `story.webp`；seed/po/mo 补齐 19 条模板词条与 8 条 JS 词条。`generate_i18n_seed.py` 修两处：mbT 双引号内含撇号漏扫、回填未转义（后者会写坏 Jinja 字典）。
- **测试**：定向 5 文件 **104 passed**（story / pages_static / hub_cards / writing_sse / i18n_seed_contract）；额外 `test_nav_settings_dropdown.py` + `test_no_duplicate_js_lines.py` **8 passed**。覆盖登录、页面元素、due 白名单、manual 折叠、非法 payload、SSE 头/事件/401 刷新、历史与 detail、50524 透传、卡片顺序与文案译文。
- **边界（如实）**：未起浏览器真机走完整链路——朗读出音、词汇股徽章 +2 分钟、历史回看均依赖登录后的真人验收；页面与静态资源已确认上线。
- **上线**：全量 **684 passed**；push `a4b1a53b..c6489147`；部署后 `/static/js/learning-story.js` 200（9,313 B），`/learning/story` 302 → `/login?next=%2Flearning%2Fstory`（登录门槛正常）。
- **台账**：requests.md 占号 R205（跨仓 moon-well R200）；分支 `feature/r205-word-story`，worktree `../magicbook-word-story` 原样驻留待验收；merge 本地 develop **`b44e20ad`**。
