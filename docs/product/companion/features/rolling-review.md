# 滚动复习（Buddy 头顶文字词卡）

> 读者：改 `ai_chat.js` 的 `initRollingReview` / `reviewRender` / `reviewPosition`，或 `ai_chat.css` 的 `.ai-review*` 的人。
> 状态：现行（2026-11-06 R285 上线；2026-11-08 R289 正文升级为单词详情分页轮播，开发完成待真机验收）。
> 需求基线：[`../requirements.md`](../requirements.md) §6；接口：[`../interface.md`](../interface.md) §滚动复习；本次实现：[`../../../project/iterations/2026-11-rolling-review/r285-rolling-review/lld.md`](../../../project/iterations/2026-11-rolling-review/r285-rolling-review/lld.md)（R285）· [`../../../project/iterations/2026-11-rolling-review/r289-detail-pages/lld.md`](../../../project/iterations/2026-11-rolling-review/r289-detail-pages/lld.md)（R289）。

## 实现方式

### 1. 挂载与定位

- 容器 `#ai-companion-review` 放在 `#ai-companion-root` 下（`restore` 与 `drawer` 之间），
  **不放进 `#ai-companion-fab-wrap`**。Why：wrap 上绑了 `mouseenter → openBubbles()` 与
  `pointerdown → 拖拽`，卡片放进去会出现「鼠标移到卡片上，快捷气泡展开把卡片遮住」，
  还会抢走伙伴的拖拽命中区。同理卡片用 `position: fixed` 而非 `absolute`。
- `reviewPosition()` 按 `wrap.getBoundingClientRect()` 算 `left/top`：默认贴 FAB 右上，
  FAB 吸附到屏幕左半时改贴左（`.is-left`），上方空间不足时翻到球下方（`.is-below`）。
  `resize` 与 wrap 的 `pointerup`（拖拽结束）都重算。
- 模板用 `{% if current_user.is_authenticated and not current_user.is_anonymous %}` 守卫；
  `initRollingReview()` 首行 `if (!root) return`，匿名阅读页不发任何请求。
- `#ai-companion-root { all: initial; }` 会盖掉 UA 的 `[hidden] { display:none }`，
  因此 CSS 显式写了 `.ai-review[hidden], .ai-review [hidden] { display:none !important; }`。
- 快捷气泡展开时 `#ai-companion-fab-wrap.bubbles-open ~ .ai-review { visibility:hidden }` 让位；
  FAB 被隐藏（`.buddy-hidden`）时 `reviewRender()` 直接给卡片加 `hidden`。

### 2. 数据与轮播

- 数据源：`GET /ajax/learning/srs/queue`，**不带 `?limit=`**（代理用扁平路径、不透传 query，
  上游默认 20）。`MBApi.getJson` → 判 `resp.ok` → `unwrap()` 取 `result` 数组。
- 过滤 `word` 非空 → Fisher-Yates 洗牌 → `slice(0, 20)`。上游是确定性排序
  （`lastReviewedAt DESC, dueAt ASC`），随机只在前端做。
- `REVIEW_INTERVAL_MS = 8000`，`setInterval(reviewTick, …)`；`pagehide` 清掉计时器。
  队列在页面生命周期内**只拉一次**，重新可见不重拉（不轮询），刷新靠 Retry 或换页。
- 显示字段只有 `word` / `meaning` / `contextSentence` / `contextBook`，全部 `textContent`。
  **不调** `/vocabulary/detail/{word}`：队列自带中文首义项与阅读原句，两者都不触发 LLM；
  详解端点缓存 miss 会现场生成（15~30s 且计费），与「不出声、不计费」冲突。
- 状态行：`review.markError`（「认识」失败原因）优先；空队列显示「暂时没有要复习的单词」，
  加载中显示「正在加载复习单词…」。队列失败走独立的错误面板 + Retry，不伪装成空态。

### 2.1 R289 详情分页轮播（正文升级）

- 队列拉到后，前端把 20 个词 POST 给 `POST /ajax/vocabulary/detail-cached-batch`
  （对端 moon-well R248 `POST /vocabulary/detail/cached-batch`，**只读缓存、绝不触发生成**；
  result 键 = 归一请求词，未命中的词不出现）。这是滚动复习与「详解」唯一的交点。
- 有缓存详解的词：正文升级为**分页详情**——「基本意思」（前 2 个义项）+ **1 个随机模块**
  （词源/搭配/词形变化/同义词/反义词/俚语/冷知识中随机取一，用户 2026-11-08 拍板：
  六板块全上一个词要停 30~60 秒，太长就成了阅读任务），每词最多 4 页；词面常驻页眉，
  进度显示 `词序/总数 · 页序/页数`。8s 一 tick 先在当前词内翻页，翻完才换下一个词。
- 每页渲染硬钳 3 行（`.ai-review-detail` 的 `-webkit-line-clamp: 3`）；词源按句切页
  （约 60 个中文字/页，280px 卡 ≈ 21 字/行 × 3 行）；页内多段用 `\n` 分行（`pre-line`）。
- 没有缓存详解的词（batch 响应里没有）：保持 R285 简卡（义项 + 原句 + 出处），
  一个 tick 一个词。详情批量接口失败/超时同样全员回退简卡——详情是增强层，
  轮播与「认识」不依赖它；失败的可观测性由代理端日志承担。
- 模块标签（词源/搭配/同义词…）内联在页首（`标签：内容`）；「Etymology/Synonyms/Antonyms」
  复用存量词条，「Collocations/Word forms/Slang/Fun facts」为 R289 新增（种子+PO+MO 三方）。

### 3. 暂停条件

`reviewShouldPause()` 命中任一条本次 tick 直接 return（不推进、不重置计时、不发请求）：
`review.loading` / `review.failed` / 手动暂停 / 收起 / 队列为空 /
`document.visibilityState === "hidden"` / `!document.hasFocus()` /
FAB `buddy-hidden` 或 `bubbles-open` / AI 抽屉 `open` / 邮件弹层可见。

### 4. 认识

- 点「认识」→ `MBApi.postJson("/ajax/reading-word-mark", {word, unknown:false})`，
  与阅读器划词气泡的「－认识」是**同一个后端端点**，零后端改动。
- 成功（HTTP ok 且 `MBApi.unwrapStrict` 通过）后只从本地 `review.items` 移除该词并推进；
  **不调** `/learning/srs/answer`，不重排 FSRS、不计 x/20。
- `known/{word}` 在 moon-well 侧是 `@Async AFTER_COMMIT` 把调度行毕业 `MASTERED`，
  返回 200 时未必已落库，所以本地立即移除才是唯一即时反馈（下次进页面队列自然不再有它）。
- 失败：保留词卡，状态行红字显示上游 `message`；`review.markError` 让错误跨多次
  `reviewRender()` 存活，直到下一次成功操作或重新加载。

### 5. 开关与本机状态

| key | 含义 |
| --- | --- |
| `calibre.ai.review.paused` | 暂停 / 继续（卡片上的 ❚❚ / ▶） |
| `calibre.ai.review.collapsed` | 收起 / 展开；收起态只留一枚显示剩余词数的小圆点 |

默认展开且不暂停；只写 localStorage，不跨设备、不写账号档案。

## 边界条件

- 不出声、不计费：代码里没有 `AudioContext` / `decodeAudioData` / `/tts` 任何调用。
- R289 详情**只读缓存**：只调 `/ajax/vocabulary/detail-cached-batch`；逐词详解代理
  `/ajax/reading-word-detail` 与上游 `/vocabulary/detail/{word}` 仍是禁区（miss 即计费），
  R285 守卫测试把这两条路径钉在禁区里。
- 详情随机模块按「队列加载」定格：同一轮 20 词的模块选择固定，下次拉队列重洗；
  标记「认识」移除词时页表同步删除，页码归零。
- 不做查词记录：`vocabulary_study_history` 虽有表，但无倒序接口、无索引、划词路径不写入，本轮不扩。
- 「今天应该复习」= `due_at <= now` 的全部到期积压（含历史欠账），不是今日新增到期。
- 「认识」≠ 完成一次 SRS 复习；今日进度 x/20 不变，这是上游 `known/{word}` 的既有语义。
- 词形不合法（不匹配 `_READING_WORD_RE` 或 >64 字符）时禁用「认识」按钮，避免必然 400。
- 伙伴可拖拽到四边、可隐藏并跨页保持；卡片位置与可见性都跟随。
- 登录页 / 注册页 / 匿名阅读页不挂载卡片。
- 标记请求在途（`review.inFlight`）也算暂停：上游超时 8s，若让 tick 推进 index，回来会删错词；删词只用点击瞬间的 `markedIndex`。
- `pagehide` 清 timer 后由 `pageshow`（`event.persisted`）重建，否则 bfcache 后退回来轮播永久停摆。
- EPUB 正文在 iframe 内，焦点进去时顶层 `hasFocus()` 可能返回 false；`reviewPageActive()` 把 `activeElement === IFRAME` 仍视为页面内活跃。
- **已知前置缺陷**：`readpdf.html` 未引入 jQuery 却 include 面板，`ai_chat.js` 以 `jQuery` 为实参会抛 `ReferenceError`——R285 之前 Buddy 面板在 PDF 阅读器就不可用。本轮不扩范围，见 [LLD §9](../../../project/iterations/2026-11-rolling-review/r285-rolling-review/lld.md)。
- 解包与 CSRF 一律委托 `MBApi`（R177 单点契约），页面不自带 `success === false` 判读。
- 所有新增文案走 `t()`（调用时取词）+ `i18n_seed.html` + zh `.po` + 编译后的 `.mo`；
  用顶层 `mbT` 会在脚本载入时被固定成恒等函数，新词条等于没加。

## 失败与降级

| 场景 | 行为 |
| --- | --- |
| 队列接口非 2xx / 非信封 / 非数组 | 错误面板显示上游 `message`（或本地兜底文案）+ Retry，不显示「没有单词」 |
| 详情批量接口失败 / 超时 / 非信封 | 静默回退简卡（义项+原句+出处），轮播与「认识」不受影响；代理端日志可查 |
| 某词无缓存详解（batch 响应缺失） | 该词保持简卡；有缓存词的分页展示不受影响 |
| 队列为空 | 状态行「暂时没有要复习的单词」，按钮禁用，不启动推进 |
| 某词缺 `meaning` / `contextSentence` | 该行留空并由 `:empty` 隐藏，词本身照常显示 |
| 「认识」上游失败 / 积分或登录态异常 | 状态行红字保留原因，词卡不移除，按钮恢复可重试 |
| localStorage 不可用 | `try/catch` 吞掉，退化为「本次会话内有效」 |
| 浏览器 `prefers-reduced-motion` | 本功能无装饰动画，仅弱化阴影；定时换词不关闭（是内容轮播不是动效） |

## 测试锚点

- `tests/test_r285_rolling_review.py`：挂载位置与登录守卫、只消费既有端点、20 上限与洗牌、
  暂停条件、`textContent` 渲染、失败不移除词、错误/空态可见、CSS 让位与 `[hidden]`、i18n 三方。
- `tests/test_buddy_voice.py` / `tests/test_i18n_seed_contract.py`：全量 `t()` 词条与种子/PO/MO 一致。
- `tests/test_common_api_contract.py`：解包与 CSRF 单点未被破坏。
- `tests/test_csp_media.py`：本轮没有放宽 `media-src`（根本不播音频）。
