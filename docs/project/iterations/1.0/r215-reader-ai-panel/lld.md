# LLD — R215 阅读器与 AI 伴读面板

> 状态：**开发中（2026-10-23，代码已落 worktree，待验收）**
> 对应 HLD：[`hld.md`](./hld.md) · 验收：[`ac/acceptance.md`](./ac/acceptance.md)
> 迭代 1.0 · PJM MB-14 · Ship MAGICBOOK-222
> 实现范围：EPUB 阅读器（`read.html`）为主；AI 面板改动对 `readpdf.html` / `readtxt.html` 生效，但桌面「推挤正文」的布局契约只在 EPUB 生效（其它阅读器保持覆盖，见 §4.6）。

## 1. 文件清单

| 动作 | 路径 | 说明 |
| --- | --- | --- |
| 新增 | `cps/static/js/reading/reader-toolbar.js` | 顶栏窄屏折叠 / 「更多」菜单 / 标签状态；无跨模块别名、无 `init` |
| 改 | `cps/templates/read.html` | `#main` 加 `reader-main` 类；顶栏标签 + `#title-more`；译文栏 DOM；移除自动隐藏相关注释 |
| 改 | `cps/static/css/reader.css` | 阅读器作用域内的顶栏、译文栏、面板布局、移动端覆盖 |
| 改 | `cps/static/css/ai_chat.css` | 桌面 50vw 停靠、移动 55vh 抽屉、头部标签、FAB 环/标签 |
| 改 | `cps/static/css/onboarding.css` | `#onb-help` 避让页码并让位侧栏 |
| 改 | `cps/static/js/reading/reader-tts.js` | 段尾 4 图标 + 触屏「⋯」菜单；翻译图标改为选中该段 |
| 改 | `cps/static/js/reading/reader-immersive.js` | 翻译模式 / 译文栏 / 段落选中 / 缓存；删除正文流内译文插入 |
| 改 | `cps/static/js/reading/epub.js` | rendered 钩子绑定段落点击；设置项联动改为划词气泡；移除旧批量翻译调用 |
| 改 | `cps/static/js/ai_chat.js` | 思考中前置与计时；侧栏互斥事件；placeholder 分格式；FAB 标签 |
| 改 | `cps/templates/ai_chat_panel.html` | 头部按钮文字/aria、FAB 标签节点 |
| 改 | `cps/templates/i18n_seed.html` + `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po` | 新增/改写文案 |
| 新增 | `tests/test_reader_r215_ui.py` | 顶栏/译文栏/思考中/面板契约的静态守卫 |
| 改 | `docs/project/iterations/1.0/plan.md` | MB-14 行补设计文档与状态 |
| 交付时 | `docs/product/readme/reading.md`、`docs/product/reading/interface.md`、`docs/product/reading/features/*.md` | 四问回填（能力/契约/实现/LLD） |

## 2. 顶栏（`reader-toolbar.js` + `reader.css`）

### 2.1 模板

`read.html` 的 `#main` 改为 `<div id="main" class="reader-main">`，仅作为 CSS 作用域，不影响 `readcbr.html`。

`#title-controls` 内每个工具改为：

```html
<a id="immersive-translate" class="tb-tool" aria-pressed="false"
   title="{{_('Translation mode')}}">
  <span class="tb-icon">译</span><span class="tb-label">{{_('Translate')}}</span>
</a>
```

- 保留全部既有 ID（`immersive-translate` / `whole-book-translate` / `tts-book` / `bookmark` / `setting` / `fullscreen`），`onboarding.js` 的锚点与 `tests/test_onboarding_tour.py` 依赖它们。
- `#tts-book` / `#tts-book-stop` 的图标文本由 `reader-tts.js` 的 `ttsButtonsRender` 动态写入（`btn.textContent = '▶'`）。加标签后必须改为写内层 `.tb-icon`（`btn.querySelector('.tb-icon').textContent = …`），否则每次状态刷新都会把「朗读」标签抹掉。
- 末尾新增 `<a id="title-more" class="tb-tool tb-more">…</a>` 与空容器 `<div id="title-more-menu" hidden></div>`。
- `#metainfo` 增加 `min-width:0`，书名/章名 `text-overflow:ellipsis`。

### 2.2 CSS

作用域统一为 `.reader-main #titlebar ...`，不修改 `main.css`：

| 规则 | 桌面 | ≤767px |
| --- | --- | --- |
| `#titlebar` | flex 三段；`opacity:.85`，hover 1；`height:auto; min-height:56px` | 同左，`min-height:52px` |
| `.tb-tool` | `min-width:36px; min-height:36px; opacity:1` | `min-width:44px; min-height:44px` |
| `.tb-icon` | `font-size:24px; line-height:1` | 24px |
| `.tb-label` | `display:inline`，12px | `display:none` |
| `#title-more` | `display:none` | `display:inline-flex` |
| `#title-more-menu` | — | `position:fixed; top:56px; right:12px; min-width:180px` 的纵向菜单 |

删除 `#titlebar a` 的二次 `opacity:.5`：新规则只作用于 `.tb-tool`，旧规则由更高优先级覆盖（`.reader-main #titlebar a.tb-tool{opacity:1}`）。

### 2.3 JS

`reader-toolbar.js`（IIFE，载入即执行，无 `window` 导出，避免触发「声明 init 必须显式调用」守卫）：

1. 记录 `#title-more` 前所有节点的原始父节点与顺序：`[bookmark, setting, fullscreen, whole-book-translate(可选)]`。
2. `sync(e)`：`matchMedia('(max-width:767px)')` 为真时把上述节点 `append` 到 `#title-more-menu`；为假时按记录顺序插回 `#title-more` 前。
3. 点击 `#title-more` 切换菜单 `hidden`；点击外部 / Escape 关闭。
4. `resize` 监听用 `requestAnimationFrame` 节流；节点搬家时其原有事件监听不受影响。
5. 不复制节点，避免 ID 重复与监听丢失。

## 3. 段尾工具（`reader-tts.js`）

`injectParagraphTools` 保持「4 个隐藏 span + 1 个菜单按钮」：

- 4 个 span 仍带 `.reading-para-btn` + 专类，title/aria-label 补全；桌面 hover 显示 24px 图标（`READER_TOOLS_STYLE` 内改 `font-size:1.5em; width:24px; height:24px`，触屏 `@media(hover:none)` 下 `display:none`）。
- 新增 `<span class="reading-para-menu-btn" role="button" aria-label="...">⋯</span>`：
  - 触屏（`hover:none`）显示，44×44；桌面 `display:none`。
  - 点击 → `openParagraphMenu(el, menuBtn)`：外层 `document.body` 建 `.reading-para-menu`，按 iframe 矩形定位（复制 `reader-annotations.js` 的坐标换算），含 4 个带文字按钮。
  - 菜单按钮点击时对对应的隐藏 span 调 `.click()`，复用现有朗读/翻译/批注/AI 逻辑，不复制实现。
- 翻译 span 的点击改为 `RI.translateParagraph(el, trBtn)`（见 §4；`btn` 参数保留兼容，函数内部只选中该段并打开右栏，不再内联插译文）。

`READER_TOOLS_STYLE` 仍由 `ReaderCore.injectToolsStyle` 注入 iframe；新增的菜单样式写在 `reader.css`（外层文档），因为菜单挂在外层 `body`。

## 4. 翻译模式与译文栏（`reader-immersive.js`）

### 4.1 状态

```js
var RAIL_MODE_KEY = 'calibre.reader.translationRailMode'; // 新键，不复用旧 immersiveTranslate
var railMode = false;        // 是否翻译模式
var selectedEl = null;       // 当前选中段落（iframe 内元素）
var railRequestSeq = 0;      // 选中/请求序号，后选覆盖先选
```

- 旧键 `calibre.reader.immersiveTranslate` 不再读取；初始化时 `localStorage.removeItem` 一次，避免旧语义残留。
- 缓存沿用 `calibre.reader.translation.<bookKey>`（`{paragraphHash: text}`），不迁移。

### 4.2 开关

`#immersive-translate` 点击：

1. `railMode = !railMode`，写新键。
2. `aria-pressed`、`.active`、文案 `翻译` / `翻译中` 同步。
3. 开启：`openRail()`（显示空态「点击正文段落查看译文」），toast「翻译模式已开启」；关闭：`closeRail()`、清除选中高亮、toast「翻译模式已关闭」。
4. 开关只切模式，不批量翻译任何段落。

### 4.3 选中与请求

`bindContent(content)` 在每个 `rendered` 的 iframe document 上绑定 `click`：

- 模式关闭 → 直接返回。
- `content.window.getSelection().toString()` 非空 → 返回（划词优先）。
- `event.target.closest('a, button, .reading-para-btn, .reading-para-menu-btn, .reading-translation')` 命中 → 返回。
- `target.closest(PARAGRAPH_SELECTOR)` 且是叶子段落 → `selectParagraph(el)`。

`selectParagraph(el)`：

1. `railRequestSeq++`；旧 `selectedEl` 移除 `.reading-para-selected`；新元素加类（样式：`outline:2px solid rgba(74,144,217,.55); outline-offset:2px`）。
2. `selectedEl = el`；`selectedText = paragraphSpeechText(el)`；`selectedChapter = host.currentChapterTitle()`。
3. `openRail()`；右栏头部显示 `selectedText` 前 40 字；正文区先渲染 loading。
4. 命中缓存 → 直接渲染；否则 POST `calibre.readingTranslateBatchUrl`，body `{paragraphs:[text], bookName, chapter}`。
5. 响应回来时校验 `seq === railRequestSeq && selectedEl === el && el.isConnected`，满足才渲染；否则只写缓存。
6. 失败：CSRF 自愈优先；否则右栏渲染错误 + 「重试」按钮（重试复用同一段）。

翻页 / 章节重渲染**不清空**选中与右栏（用户可继续对照上一段）；关闭模式或另选段落才替换。若元素已 `!isConnected`，右栏保留文本、头部标注「该段已不在当前页」。

### 4.4 右栏 DOM（`read.html`）

```html
<aside id="translation-rail" hidden aria-label="{{_('Translation')}}">
  <header>
    <span id="translation-rail-title">{{_('Translation')}}</span>
    <button id="translation-rail-close" type="button" aria-label="{{_('Close')}}">×</button>
  </header>
  <div id="translation-rail-source"></div>
  <div id="translation-rail-body"></div>
</aside>
```

状态：`empty`（提示）/ `loading`（「翻译中…」）/ `text`（译文）/ `error`（错误 + 重试）。

### 4.5 面板互斥

- 打开译文栏：`document.dispatchEvent(new CustomEvent('reader:panel-open', {detail:{kind:'translation'}}))`；监听 `reader:panel-open` 且 `kind === 'ai'` 时只 `closeRail()`（保留 `railMode`，不派发 close）。
- AI 面板同理：打开时派发 `kind:'ai'`，译文栏收到后收起；AI 关闭时派发 `reader:panel-close`，译文栏若 `railMode` 为真则重新打开。
- 避免递归：收到对方 open 时只做「收起自己」，不再派发新事件。

### 4.6 布局

`body[data-side-panel]` 表示有侧栏：

- 桌面（>900px）且 `kind=translation`：`--side-panel-width: clamp(300px, 32vw, 420px)`；`#main.reader-main{width:calc(100% - var(--side-panel-width)); left:0; right:auto}`。
- 桌面 `kind=ai`：`--side-panel-width:50vw`。
- ≤900px：`#main` 宽度 100%；`#translation-rail` 改底部抽屉（`top:auto; bottom:0; width:100vw; height:50vh; border-radius:16px 16px 0 0`）。
- 宽度切换不加 transition；落定后 `window.dispatchEvent(new Event('resize'))` 触发 epub.js 重分页（它监听 window resize）。
- PDF/TXT 没有 `#main.reader-main`，AI 面板仍以 50vw 覆盖，不改它们的布局。

## 5. AI 面板（`ai_chat.css` + `ai_chat.js` + `ai_chat_panel.html`）

### 5.1 布局

- 桌面：`#ai-companion-drawer{width:50vw; max-width:50vw; height:100vh}`；打开时 body `data-side-panel="ai"`。
- ≤900px：`top:auto; bottom:0; width:100vw; height:55vh; border-radius:16px 16px 0 0`，顶部加 36×4 的视觉拖拽条（`::before`，不做手势）。
- 打开/关闭流程统一走 `setPanelState(kind)`：设置/清除 `body.dataset.sidePanel`，派发 open/close 事件，落定后 resize。

### 5.2 头部与 FAB

- `ai_chat_panel.html` 的 4 个操作按钮加 `<span class="ai-ctl-label">新建/重命名/删除/记忆</span>`；≥900px 显示文字，窄屏只留图标 + `aria-label` + `title`。
- FAB：`#ai-companion-fab` 加品牌色外环（box-shadow 2 层）+ `#ai-companion-fab-label`（「伴读」小标签）。桌面常显；移动端首次进入显示，首次打开抽屉后写 `localStorage['calibre.ai.fabLabelSeen']=1` 并隐藏。裂图/未装备仍回落「AI」文字。

### 5.3 思考中

`sendMessage` 改为：

1. 同步 `beginThinking()`：创建 assistant 气泡（「思考中 · 0s」）、启动 1s 计时器、FAB 加 `buddy-thinking`、`sending=true`、禁用发送。
2. `Promise.race([getPageContextAsync(), timeout(1200)])`；超时返回 `""`，请求照发。
3. `streamChat(text, pageCtx, thinkingState)`：复用同一气泡；首个 `delta` / `tool_call` / `final` / `error` 任一到达即 `stopThinking()`（停表、移除 typing 占位、FAB 退出 thinking）。
4. 计时文案「思考中 · Ns」；`N` 每秒刷新。

### 5.4 placeholder 口径

- 模板默认改 `Ask about this chapter...`（EPUB）。
- `ai_chat.js` 初始化时按 `AICompanion.detectFormat()` 覆盖：`pdf` → `Ask about the current page...`；`txt` → `Ask about this text...`；`epub` 保持 chapter。
- 三个 msgid 进 `i18n_seed.html` + 中文 `.po`。

## 6. 幽灵「?」（`onboarding.css`）

```css
#onb-help{left:auto; right:16px; bottom:88px;}
@media (max-width:767px){#onb-help{right:16px; bottom:76px;}}
body[data-side-panel] #onb-help{display:none;}
```

- 不改 `onboarding.js`：入口仍恰好追加一次，`tests/test_onboarding_tour.py` 不变。
- 彻底去留/并入「更多」菜单由 R216 处理；本条只保证不与页码、FAB、侧栏重叠。

## 7. 守卫与测试

| 测试 | 处置 |
| --- | --- |
| `tests/reader_js_modules.py` | 自动读取 `read.html` 的脚本顺序，新增 `reader-toolbar.js` 后仍按顺序拼接；确认新文件排在 `reader-core.js` 之后、`epub.js` 之前 |
| `tests/test_reader_module_surface.py` | `ALIASES` 不变（新模块无跨模块别名、无 `init`）；`test_声明_init_的模块必须被显式调用` 仍只允许 `ReaderImmersive` |
| `tests/test_onboarding_tour.py` | 顶栏 ID 与 `#onb-help` 追加逻辑保持不变 |
| `tests/test_reader_lens_handoff.py` | 保留 `getElementById('immersive-translate')` |
| 新增 `tests/test_reader_r215_ui.py` | ① 顶栏有 `.tb-label` / `#title-more` / 原有 ID；② `reader-immersive.js` 不再包含正文流内 `insertTranslation`，含 `translation-rail` 与模式键；③ 段落点击守卫含选区/链接判断；④ `ai_chat.css` 含 50vw / 55vh / `data-side-panel`；⑤ `sendMessage` 中 `beginThinking` 调用先于 `getPageContextAsync`；⑥ placeholder 三个口径；⑦ `#onb-help` 右移且侧栏打开时隐藏 |
| 反向变异 | 逐条注入旧行为（恢复双重 opacity、把译文插回正文、把思考中移回 streamChat）确认报红 |

开发态闸门：`node --check` 全部改动 JS + 上述 pytest 文件全绿。正式发布态按仓规跑全量。

## 8. 偏差表（相对 MB-14 原文）

| MB-14 原文 | 实际实现 | 原因 |
| --- | --- | --- |
| 逐段翻译「写预留占位」 | 译文右栏，正文零插入 | 分页列布局下任何流内高度变化都会重分页；占位只能减少次数不能消除（用户拍板改形态） |
| AI 面板「可拖宽/停靠」 | 桌面固定 50vw 停靠，不可拖 | 用户拍板固定半屏 |
| 段尾「≥44px 或收进段落菜单」 | 桌面四图标 24px；触屏 44px 菜单 | 兼顾桌面效率与触屏触达（用户拍板） |
| 幽灵「?」处置 | 仅位置避让 | DOM 归属 `onboarding.js`，R216 将重做；避免两单同时改守卫断言 |

## 9. 风险与回滚

- 风险：`#main` 宽度变化触发 epub.js 重分页，个别书在两栏模式下可能落到异常页；回滚开关 = 关闭侧栏（模式状态与选中状态均不落库）。
- 风险：点击即译误触；已用「模式开关 + 选区/链接/按钮排除」收敛，真机用三指/拖选各测一次。
- 回滚：纯前端改动，revert merge 即可；localStorage 新键不影响旧版本（旧键不读取）。
