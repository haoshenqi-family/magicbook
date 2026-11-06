# LLD · R285 Buddy 头顶滚动复习气泡

> 状态：开发中（2026-11-06：编码与定向回归完成，待 merge 与真机验收）
> 需求基线：`docs/product/companion/requirements.md` §6 · HLD：[`../hld.md`](../hld.md) · AC：[`ac/acceptance.md`](./ac/acceptance.md)

## 1. 改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/templates/ai_chat_panel.html` | 在 `restore` 与 `drawer` 之间新增 `#ai-companion-review` 容器，登录且非匿名才渲染 |
| `cps/static/js/ai_chat.js` | 新增 R285 段（常量 / 状态 / 定位 / 渲染 / 加载 / tick / 认识 / 开关 / init），`init()` 增加 `initRollingReview()` 一行 |
| `cps/static/css/ai_chat.css` | 新增 `.ai-review*` 样式、`[hidden]` 显式覆盖、`bubbles-open` 让位、移动端触达盒 |
| `cps/templates/i18n_seed.html` | 新增 12 条 `t()` 词条（`Retry` 复用既有） |
| `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po` / `.mo` | 新增 12 条中文译文并 `pybabel compile -f` |
| `tests/test_r285_rolling_review.py` | 新增 9 条契约测试 |
| 文档 | L1 / L2 / L3 / 需求基线 / 本迭代 HLD·LLD·AC·plan / 1.0 plan / requests |

**`cps/routes/*` 与 `cps/web.py` 零改动；moon-well 零改动；无新增表、无新增端点、无新增后台任务。**

## 2. 常量与状态

```js
REVIEW_QUEUE_URL    = "/ajax/learning/srs/queue"   // 故意不带 ?limit=
REVIEW_MARK_URL     = "/ajax/reading-word-mark"
REVIEW_MAX          = 20
REVIEW_INTERVAL_MS  = 8000
REVIEW_PAUSED_KEY   = "calibre.ai.review.paused"
REVIEW_COLLAPSED_KEY= "calibre.ai.review.collapsed"
REVIEW_WORD_RE      = /^[A-Za-z](?:[A-Za-z'’\-]*[A-Za-z])?$/   // 同 _READING_WORD_RE
```

`review = {items, index, timer, loading, inFlight, paused, collapsed, failed, markError}`。
`markError` 单独留一份错误文案的原因：`reviewRender()` 每次都会重画状态行，直接写 DOM 会被下一帧抹掉。

## 3. 时序

**初始化**：`init()` → `initRollingReview()` → 读两个 localStorage flag → 绑 6 个按钮 →
绑 `resize` / wrap `pointerup` / `pagehide` → `setInterval(reviewTick, 8000)` → `reviewLoad()`。
容器不存在（匿名/登录页）时首行 return，不发请求。

**加载**：`MBApi.getJson(REVIEW_QUEUE_URL)` → 判 `resp.ok`（非 2xx 抛 `jsonMessage(raw)`
或本地兜底）→ `unwrap(resp.data)` 取 `result` 数组 → 非数组抛错 →
过滤空 `word` → Fisher-Yates 洗牌 → `slice(0, 20)` → `index=0`。
`.catch` 走 `reviewShowError()`（错误面板 + Retry），`.then` 复位 `loading` 并重绘。

**轮播**：`reviewTick()` 先过 `reviewShouldPause()`；命中任一暂停条件直接 return，
不推进、不重置计时、不发请求。否则 `index = (index+1) % items.length` 后 `reviewRender()`。

**认识**：`reviewMarkKnown()` → 缓存 `markedIndex = review.index` → 置 `inFlight` →
`MBApi.postJson(REVIEW_MARK_URL, {word, unknown:false})` → 判 `resp.ok` →
`api.unwrapStrict(resp.data)`（解包单点委托，非信封 / `success:false` 一律抛）→
成功 `items.splice(markedIndex,1)`（按需回退 index）+ `markError=""`；
失败只写 `markError`，**不 splice** → `.then` 复位 `inFlight` 并 `reviewRender()`。

**交叉审查后补的三条不变量**（2026-11-06）：

1. `reviewShouldPause()` 含 `review.inFlight`：上游标记代理超时 8s，请求在途时若让
   tick 推进 index，成功回来会按新 index 删掉**下一个词**，语义与数据相反。
   删词只用点击瞬间的 `markedIndex`。
2. `pagehide` 清 timer 后必须由 `pageshow`（`event.persisted`）经 `reviewStartTimer()`
   重建，否则 bfcache 后退回来轮播永久停摆。
3. `reviewPageActive()`：EPUB 正文在 iframe 内，焦点进去后顶层 `document.hasFocus()`
   可能为 false；仅当 `activeElement` 不是 `IFRAME` 时才判为窗口不活跃，避免误停。
   换词路径（tick / advance）还会清 `markError`，防止上一条失败原因挂到新词上。
   拖拽吸附的 0.22s 过渡由 `transitionend` + 260ms 兜底重算位置；复原动画结束后再校正一次。

## 4. 定位算法

```
rect = wrap.getBoundingClientRect()
leftSide = rect.left + rect.width/2 < innerWidth/2
left = clamp(leftSide ? rect.left : rect.right - width, 8, innerWidth - width - 8)
top  = rect.top - height - 12
below = top < 8  →  top = rect.bottom + 12
toggle .is-left / .is-below（小箭头方向）
```

`reviewRender()` 在 FAB `buddy-hidden` 时直接给容器加 `hidden` 并 return；
`hideBuddy` / `restoreBuddy` 的既有点击链后面各挂一个 `setTimeout(reviewRender, 0)`
（不改动既有函数），保证隐藏/复原后卡片立刻跟随。

## 5. 异常与边界

| 场景 | 处理 |
| --- | --- |
| 非 2xx / 非信封 / 非数组 / 网络异常 | 错误面板 + 上游 `message` + Retry；不进入空态 |
| 队列为空 | 状态行「暂时没有要复习的单词」，两个按钮 disabled，tick 暂停 |
| 词形不合法 / >64 字符 | 「认识」按钮 disabled 并给出 title，避免必然 400 |
| 「认识」失败 | 卡片保留、状态行红字 `is-error`、按钮恢复，可重试 |
| 上游 `meaning` / `contextSentence` 缺失 | 对应行留空，CSS `:empty` 隐藏 |
| localStorage 抛异常 | `try/catch` 吞掉，退化为本次会话有效 |
| 页面不可见 / 窗口失焦 / 伙伴隐藏 / 快捷气泡 / 抽屉 / 邮件弹层 | tick 暂停 |
| `prefers-reduced-motion` | 只弱化阴影，不关内容轮播 |
| 登录页 / 注册页 / 匿名阅读 | 模板不渲染容器，JS 首行 return |

## 6. 安全与契约

- 服务端字段全部 `textContent`；无 `innerHTML`。
- 解包 `MBApi.unwrapResult/unwrapStrict`、CSRF `MBApi.csrfToken()`（R177 单点），
  页面不得自带 `success === false` / `success !== true` 判读——`test_common_api_contract.py` 是反向守卫。
- 卡片点击与 `pointerdown` 都 `stopPropagation`，不穿透为 FAB 点击或拖拽。
- 卡片在 `bubbles-open` 时 `visibility:hidden`，与 R223 快捷气泡解耦。
- 无 `AudioContext` / `decodeAudioData` / `/tts` / `/vocabulary/detail` / `srs/answer` 调用。

## 7. i18n

12 条新词条 + 复用既有 `Retry`，全部 `t()`（调用时取词）：
`Rolling review` / `Pause review` / `Resume review` / `Collapse review` / `Show review` /
`Next word` / `I know this` / `Loading review words…` / `No words to review right now` /
`This word cannot be marked here` / `Could not load review words` /
`Could not mark this word as known`。
链路：`i18n_seed.html` 字典 → zh `.po` → `pybabel compile -d cps/translations -l zh_Hans_CN -f` → `.mo`。
Why 不用顶层 `mbT`：i18n_seed 在面板之后 include，脚本载入时 `mbT` 还是恒等函数。

## 8. 验证

- `node --check cps/static/js/ai_chat.js` 通过；`pybabel compile -f` 通过。
- 定向回归 **129 passed**（R285 12 例 + R227 语音 / i18n 三方 / CSP 反向守卫 /
  公共层解包单点 / FAB 动画 / 站点助手 / 阅读器验收 / learning 代理 / R284）。
- 全量 `pytest tests/ -q`：**1296 passed, 80 errors**；errors 均为
  `FileExistsError: EEXIST …/pytest-of-haoshenqi`（干净 worktree 的 pytest tmp 目录竞态，
  R144 同类），用独立 `--basetemp` 复验三个报错文件得 **25 passed**，与 R285 改动无关。
- i18n 三方逐一运行时校验（`.mo` 13 个 key 全部有中文）。
- 交叉审查（独立 Agent 视角）发现并已修复：标记/tick 竞态删错词、bfcache 停摆、
  iframe 焦点误停、拖拽过渡错位、markError 跨词残留、移动端触达盒；测试同步补强。
- **未真机验收**：需在登录态全站页面、EPUB/PDF/TXT 三种阅读器、伙伴拖拽/隐藏/快捷气泡、
  窗口切后台与 bfcache 后退等场景人工确认。

## 9. 已知前置缺陷（不属本轮范围）

`readpdf.html` 未引入 jQuery，但仍 include `ai_chat_panel.html`，面板末尾的 `ai_chat.js`
以 `jQuery` 为实参会抛 `ReferenceError`——**R285 之前 Buddy 面板在 PDF 阅读器就不可用**。
本轮不扩范围修 PDF 骨架，AC 单列一条要求真机确认；若确属缺失，另立需求补 jQuery 或让
`ai_chat.js` 无 jQuery 时安全降级。
