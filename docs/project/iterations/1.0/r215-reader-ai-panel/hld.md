# HLD — R215 阅读器与 AI 伴读面板：控件可见性、面板停靠、状态反馈、翻译重排

> 状态：**定稿（2026-10-23 用户三轮拍板）· 开发中**（见 §4）
> 迭代：1.0 · PJM 工作项 [MB-14](https://haoshenqi.pingcode.com/pjm/workitems/SE5FkqOT)（用户故事）· Ship 需求 MAGICBOOK-222
> 来源：首访体验 QA 报告 §五、§八（`docs/project/qa/2026-10-23/2026-10-23-qa-report.md`，截图 `b1-reader.png` `c2-translate.png` `c3-ai-panel.png` `d1-ai-15s.png` `f2-mobile-reader.png`）
> 关联：R203（译文段落别名修复，已 merge）· R206（伙伴 FAB，已上线）· R211（自助注册超管，已上线；QA 看到「整本译」是它的副作用）· R214（书籍详情，开发中，与本条无同文件重叠）· R216（引导收敛，将重做 `onboarding.js`，本条只避让不改语义）

## 1. 目标与范围

把阅读器从「功能强但控件不可发现」收敛为「触屏可点、状态可读、面板不挡正文、翻译不抖」。范围按 QA 六条交付拆成六块，全部是前端（模板 / CSS / JS），不改后端接口。

| # | 交付 | 现状病根 | 量级 |
| --- | --- | --- | --- |
| A | 顶栏控件可见 | 双重透明度 0.25 + 18×19 图标盒 + 无响应式 | M |
| B | 段尾工具可点 | 4 个 `<span>` 塞进段落，`.8em` 字形、仅 `title`、占行内宽度 | M |
| C | 翻译不抖 | 译文插进分页流，1 行占位变 N 行 → epub.js 重分页 | L |
| D | AI 面板停靠 | 固定 420px 纯覆盖；移动端 100vw×100vh 全屏 | M |
| E | 状态反馈 | 先取页面上下文再出「思考中」；开关态只有边框变化 | S |
| F | 语义与避让 | FAB 白圈像 spinner；幽灵「?」与页码撞位；placeholder 口径与回答范围不符 | S |

**不在本条范围**：PDF/TXT 阅读器的译文栏（它们没有 `reader-immersive.js`，本轮只共享 AI 面板改造）；整本翻译 job 链路；R216 的引导收敛与 `/me` 改版；面板拖拽（已拍板不做）。

## 2. 现状诊断（代码事实，2026-10-23 核查）

| # | 事实 | 证据 | 影响 |
| --- | --- | --- | --- |
| ① | `#titlebar{opacity:.5}` 与 `#titlebar a{opacity:.5}` 相乘 | `cps/static/css/main.css:37-66` | 实际对比度 0.25；QA 的「极浅」是两处透明度叠加，不是图标资源问题 |
| ② | 图标盒 18×19 + padding 4 | 同上 `:57-66` | 触达 26×27，远低于 44px；字形被 `overflow:hidden` 裁在 13px 左右 |
| ③ | `#title-controls` 只有 `float:right` | `main.css:207-209` | 没有窄屏折叠策略，加标签后必然挤压书名 |
| ④ | 段尾 4 按钮以 `<span>` append 进段落 | `cps/static/js/reading/reader-tts.js:65-118` | 按钮是正文流的一部分；`opacity:0` 仍占行内宽度，字形 0.8em，触屏只有 `title` |
| ⑤ | 译文 `insertTranslation` 先 remove 再 insert | `cps/static/js/reading/reader-immersive.js:80-91` | 每次响应都改一次流内高度 |
| ⑥ | 批量翻译先插 1 行「Translating…」再逐段替换 | `reader-immersive.js:261-304` | 分页列布局下每次高度变化都重分页 → 整页抖动 |
| ⑦ | 译文缓存为 localStorage `{paragraphHash: text}` | `reader-immersive.js:47-64` | 可复用到右栏；格式不需要迁移 |
| ⑧ | AI 抽屉固定 420px / 100vh，无 resize | `cps/static/css/ai_chat.css:38-51` | 直接覆盖书页；QA 的「正文被截断」 |
| ⑨ | 移动端抽屉 100vw×100vh | `ai_chat.css:137-163` | 打开即全屏，无法边读边问 |
| ⑩ | 「思考中」在 `streamChat` 里才创建 | `cps/static/js/ai_chat.js:381-405` | `getPageContextAsync()` 先 await，PDF 取页文本慢 → 15 秒空白 |
| ⑪ | EPUB 页面上下文取整个当前章节 | `cps/static/js/ai_page_extract.js:16-33` | 回答覆盖整章，placeholder 却写「current page」 |
| ⑫ | FAB `has-buddy` 白底 + 浅色头像 | `ai_chat.css:17-36` | 像加载中的 spinner；R206 头像本身已上线 |
| ⑬ | 幽灵「?」`left:16 bottom:16 34px` | `cps/static/css/onboarding.css:287-308` | 与页码 `left:12 bottom:2`（`reader.css:263-269`）撞位 |
| ⑭ | 「译」开关激活态只有橙色描边 | `cps/static/css/reader.css:223-234` | 开/关不可一眼分辨 |

## 3. 方案

### 3.1 布局（2026-10-23 验收回滚，最终口径）

> 原「AI 半屏停靠 + 译文右栏占宽」方案被用户连续否决。最终：**翻译恢复段内内联、AI 恢复覆盖式抽屉**，正文宽度不再因任何面板变化。

- 译文：直接插入段落下方（R183 原实现），接受 epub.js 重分页；无右栏、无点段选中。
- AI 面板：桌面右侧 420px 固定浮层；≤600px 为 100vw×100vh 全屏抽屉；不参与正文布局。
- 不再使用 `data-side-panel` 布局变量与 `reader:panel-open/close` 事件。

### 3.2 顶栏

- `#titlebar` 改 flex 三段：左（菜单）/ 中（书名 + 章名，可截断）/ 右（工具，不换行）。
- 桌面：图标 24px + 中文文字标签（翻译 / 朗读 / 书签 / 设置 / 全屏），触达 ≥36px；基部透明度 .85、hover 1，删除链接层二次 `opacity`。
- ≤767px：隐藏文字标签，触达 44px；主位只留「翻译 / 朗读 / 更多」，其余（书签 / 设置 / 全屏 / 整本翻译）由 JS 移入 `#title-more-menu`，关闭时移回原位（节点搬家而非复制，避免 ID 重复）。
- 保留既有 ID（`immersive-translate` / `bookmark` / `fullscreen` 等）——`onboarding.js` 的导览锚点和 `tests/test_onboarding_tour.py` 依赖它们。
- 作用域：只改阅读器模板（`read.html` / `readcbr.html`），CSS 用 `body.reader` 或 `#main` 前缀收窄，避免污染书库页。

### 3.3 段尾工具

- 桌面（`hover:hover`）：hover 段落时显示 4 个 24px 图标（朗读 / 翻译 / 批注 / AI 伴读），点击语义不变。
- 触屏（`hover:none`）：只显示一个 44px 的「⋯」按钮；点开弹出四项带文字的菜单（复用批注弹层的定位方式：节点挂外层 `document.body`，按 iframe 矩形换算坐标）。
- 菜单与按钮都在段落尾部行内：桌面四图标 `opacity:0` hover 显现（仍占行内宽度），触屏换成 44px「⋯」。
- 「翻译」项/图标直接触发该段的段内译文（见 §3.4）。

### 3.4 翻译：恢复段落下方内联（2026-10-23 验收回滚）

**交互**（与 R183 一致）：

1. 顶栏「译」开关：开启 = 批量翻译当前可见页，译文逐段插入各段下方；关闭 = 移除所有译文。
2. 段尾「译」按钮：单段翻译，译文插入该段下方；再点一次收回；命中缓存即时显示。
3. 翻页/重渲染：`epub.js` 调 `RI.restoreCachedTranslations` 只回填已缓存译文。
4. 译文块按设置自动隐藏；`.reading-translation` 三态样式恢复。

**已知代价**：译文属于正文流，插入/替换会引起 epub.js 重分页抖动。用户 2026-10-23 验收时明确「宁可重分页」也要回到这个形态，故不做占位/右栏替代。

**缓存**：`calibre.reader.translation.<bookKey>`（`{hash: text}`），与原实现一致。

### 3.5 AI 面板

> **2026-10-23 验收回滚**：原方案「桌面 50vw 停靠 + 正文缩宽 / 移动 55vh 底部抽屉」被用户否决，恢复为覆盖式抽屉。以下为回滚后的口径。

- 桌面：右侧 420px 固定浮层（`position:fixed`，覆盖在正文上），不改变 `#main` 宽度、不触发 epub.js 重分页。
- 移动 ≤600px：100vw×100vh 全屏抽屉（恢复 R215 之前的形态）。
- 头部：桌面显示文字标签（新建 / 重命名 / 删除 / 记忆），窄屏保留图标但补 `aria-label` + `title`；关闭按钮 44px 触达。
- FAB：保留头像，外圈加品牌色环 + 阴影；桌面 hover 显示「伴读」文字；移动端首次进入显示「伴读」小标签，首次打开后只留头像（localStorage 记一次）。裂图/未装备仍回落「AI」文字。
- 与译文栏不再互斥：AI 浮层直接覆盖在右栏之上，关闭后右栏原样可见。

### 3.6 状态反馈与口径

- **思考中**：`sendMessage` 同步插入气泡并启动计时器（「思考中 · Ns」），同时给 FAB 加 `buddy-thinking`；页面上下文提取加 1200ms 超时竞速，超时以空 `pageText` 继续请求；首个 delta / tool_call / final / error 任一到达即停表并复用同一气泡。
- **翻译开关**：文案「翻译」，激活时实心底 + 文案「翻译中」+ `aria-pressed=true`；进入/退出各一次 toast（「翻译模式已开启：点击段落查看译文」/「翻译模式已关闭」）。
- **placeholder**：按格式分口径——EPUB「询问本章内容…」、PDF「询问当前页…」、TXT「询问本文…」；由 `ai_page_extract.js` 的 `detectFormat()` 在面板初始化时设置，模板默认给 EPUB 口径。

### 3.7 幽灵「?」与 FAB 避让

- `#onb-help` 从 `left:16/bottom:16` 移到 `right:16/bottom:88`（FAB 上方），`left:auto`；移动端 `bottom:76`。
- 任一侧栏打开时隐藏（`body[data-side-panel] #onb-help{display:none}`），避免压在抽屉上。
- **不改 `onboarding.js` 的 DOM 归属**（R216 将重做）；本条只做 CSS 避让，`#onb-help` 仍恰好追加一次。

## 4. 拍板记录（2026-10-23）

| # | 问题 | 结论 |
| --- | --- | --- |
| 1 | 翻译防抖 | ~~左正文右译文栏~~ **已被 2026-10-23 验收否决**：恢复段落下方内联，接受重分页 |
| 2 | AI 面板桌面形态 | ~~固定半屏停靠，不可拖；移动端 55vh 底部抽屉~~ **已被 2026-10-23 验收否决并回滚**：桌面 420px 覆盖式抽屉 / 移动全屏 |
| 3 | 段尾按钮 | 桌面 hover 四图标；触屏单个 44px 菜单 |
| 4 | 开工基线 | 现在开工；R214 若先合并在验收前拉齐基线复跑 |
| 5 | 译文栏粒度 | ~~仅选中段~~ **已作废**（右栏整体回滚） |
| 6 | 段下内联译文 | ~~全部移入右栏~~ **已回滚**：恢复段下内联 |
| 7 | 右侧共存 | ~~译文栏与 AI 面板互斥显示~~ **已作废**（无译文栏） |
| 8 | 移动译文栏 | ~~底部抽屉 50vh~~ **已作废**（译文段内，无右栏） |
| 9 | 翻译触发 | ~~开关即模式、点段落选中~~ **已回滚**：顶栏开关整页自动翻译；段尾「译」单段 |

## 5. 依赖与风险

- **R214 并行**：R214 改 `detail.html` + 新增 `cps/reading_insight/`，与本条无同文件重叠；`cps/web.py` 若两边都动，合并时按小冲突处理。R214 完成后在验收前 `merge origin/develop` 复跑。
- **R216 重叠**：`onboarding.css/js` 归 R216；本条只改 CSS 位置，不改 JS 语义与守卫断言。
- **重分页**：译文回到段内后，插入/替换仍会触发 epub.js 重分页；用户 2026-10-23 验收明确接受该代价。AI 面板覆盖式，不触发重分页。
- **i18n**：新增/改写的文案进 `i18n_seed.html` 与 `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po`，跑 `test_i18n_seed_contract.py`。
- **守卫测试**：`tests/reader_js_modules.py`（装配顺序）、`tests/test_reader_module_surface.py`（导出面/别名）、`tests/test_onboarding_tour.py`（help 入口恰好一次、顶栏锚点存在）会命中，必须同步修改而非绕过。

## 6. 边界（不做）

- 不做面板拖拽调宽；不做 AI 面板全屏切换。
- 不做 PDF/TXT 的译文栏；不做整本翻译 UI 改版。
- 不做 R216 的引导文案统一、`/me` 偏好页、伙伴 IP 替换。
- 不新增后端接口，不改翻译/TTS/批注的请求形制。
