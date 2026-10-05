# US4 magicbook 代理层 + /reading/settings 测试 UI - 详细设计

> 上游：主 LLD（moon-well `vocab-size-test-lld.md`）§6 契约、本文档承接 magicbook LLD §2–§4。依赖后端 US1–US3 已部署方可联调，但代码可先行（入口按钮区合入时机见主 magicbook LLD §7）。

## 1. 代理层（`cps/web.py`）

四个路由，完全照 `reading_settings_get/update`（web.py:535-553）模式，薄透传零业务：

```python
@web.route("/ajax/vocab-test/start", methods=["POST"])            # → POST /vocabulary/test/start
@web.route("/ajax/vocab-test/answer", methods=["POST"])           # body 含 {"sessionId": id, "seq": N, "answer": 0|1}
@web.route("/ajax/vocab-test/finish", methods=["POST"])           # body 含 {"sessionId", "addUnknownToNotebook"}
@web.route("/ajax/vocab-test/history", methods=["GET"])           # → GET /vocabulary/test/history
```

- **对账修订（2026-10-05，实现前）：目标路径是平铺的，不带 `{sessionId}`**。US3 交付的 `VocabularyTestController` 只有
  `POST /vocabulary/test/{start,answer,finish}` + `GET /vocabulary/test/history` 四个固定路径（主 LLD §6「去 @PathVariable」的定稿），
  sessionId 一律走请求体。原稿第 16 行的 `_moonwell_proxy(f"/vocabulary/test/{sid}/answer", ...)` 会打到不存在的 URL，
  代理层 path 是常量、不做路径拼接。history 也不带 `limit` 参数（后端默认 10 条，前端不翻页）。
- **answer 必带 `seq`**（对账修订）：后端 DTO `seq @NotNull @Min(1)` 是幂等锚点，缺它直接 HTTP 400。前端必须持有
  `question.seq` 并在重试时原样回传，服务端据此区分「重发旧题（回放）」与「跳题（50304）」。请求体刻意不带 word。
- 校验：answer 仅校验 `answer ∈ {0,1}`、`seq ≥ 1`、`sessionId` 为正整数，非法即 `jsonify({"success": False, ...}), 400`（对齐 web.py:549-551 风格）；其余透传。**业务错误不由代理层翻译**：后端所有 `BusinessException` 都以 HTTP 500 + `Result.code` 出口（`GlobalExceptionHandler` 既有行为），代理原样透传状态码与响应体，判读交给前端（§2.3）。
- 超时：start/finish/history 10s；answer 5s（答题是内存态机 + 单行 insert，短超时快失败）。
- ⚠️ **落地修订（2026-10-05，实现后）：首屏不在服务端拉 history**，原稿的 `_vocabtest_history_fetch()` 已删除。
  - Why: 测试历史只是卡片摘要，服务端同步拉等于给 `/reading/settings` 首屏再加一个上游超时预算（档位 10s + 历史 10s，最坏 10s×2 串行），
    而这条页面已经在 `load_error` 上背过一次依赖 moon-well 的风险。改判为**前端异步拉取**（`vocab-test.js` 页面加载后 GET `/ajax/vocab-test/history`，
    失败/非 2xx/结构不符一律静默保持无历史态），项目内已有同模式先例：成就中心页数据全走 `/ajax/achievements-*`，路由本身不碰上游。
  - 顺带暴露的既有测试约束：`tests/test_reading_settings.py::test_page_renders_with_settings` 的 `fake_proxy` 对**每一次**调用都断言
    `method=="GET" and path.endswith("/settings")`，服务端多拉一次 history 直接把这条既有测试打红。这不是测试过严，而是它在替我们守首屏调用次数——
    所以本次没有改别人的测试，改的是自己的设计（另起文件 `tests/test_vocab_test_proxy.py` 里新增 `test_page_renders_card_with_single_upstream_call`
    把「首屏只允许一次上游调用」固化成契约）。
- 透传形态（⚠️ 落地修订）：四条路由一律 `return _moonwell_proxy(...)` **原样返回**，不做 `body, status, headers = ...` 解包。
  `_moonwell_proxy` 正常路径返回三元组，但「未配置 base url / `RequestException`」两条分支返回的是 `(jsonify(...), 503)` **二元组**；
  按三元组解包会抛 `ValueError` → 用户侧 500 白页，前端连降级分支都进不去。原稿第 25 行只提醒了 `_moonwell_settings_fetch()` 那类
  「解包后自处理」的调用方要用 `except (ValueError, TypeError)` 兜住，而视图型路由的兜法就是不解包。
  该坑由 `test_unreachable_upstream_returns_503_json_not_500`（四条路由参数化）固化。
  ⚠️ 遗留观察（未在本次改）：既有 `reading_settings_get()`（web.py:542）仍是解包写法，上游不可达时会 500；属既有代码，留给后续单独修。

## 2. 模板结构（`reading_settings.html`）

### 2.1 测试卡片（档位 panel 之后，同 `panel panel-default` 体系）

```
panel: Vocabulary Size Test
  p.text-muted: 一句话说明 + "About 2–4 minutes, 20–40 words"
  [if last]  help-block: Last result: <b>~8,600</b> (7,200–10,000) · Oct 4, 2026
             [if capped] 显示 "25,000+"（无区间）
  checkbox#vt-add-unknown（默认勾选）: "Add unknown words to my notebook"
  button#vt-start .btn.btn-primary: "Start test"
  a#vt-toggle-history: "History" → 折叠 ul（日期 · 估算 · 题量，来自首屏 history；为 null 时整个 History 链接隐藏）
```

- **时长/题量文案对账修订（2026-10-05，用户确认）**：原稿「~4 min, 40–50 words」与后端实测不符——US2 机器人对拍（真实词表、5 个画像 ×200 场）平均 **20–38 题**、硬上限 70。定稿按实测写「2–4 分钟 · 20–40 题」，宁可少承诺。进度条分母没有服务端字段（`Progress{answered, known, band}`），按 40 作弱对比刻度，不断言「共 N 题」。

- 文案全部 `{{_()}}` 包裹、英文 msgid（页面现状单语纪律，见 magicbook LLD §2 视觉约束）；新增串需补 zh 翻译（`cps/translations`，参照 language-i18n 既有做法），未翻译前默认显示英文不阻塞。
- `#vt-add-unknown` 状态记忆：`localStorage["vtAddUnknown"]`，读不到默认 true。Why: 服务端 per-user 偏好需要新存储面，本期一人一设备场景 localStorage 足够。

### 2.2 答题浮层与结果视图（同模板内隐藏容器，modal 样式复用项目现有 overlay/modal 类）

- 浮层 DOM：进度条（`.vt-progress`）、`#vt-word`（超大字号）、`#vt-sentence`（灰）、两键 `#vt-known` / `#vt-unknown`、右上 `#vt-exit`、`#vt-error-line`。
- 结果 DOM：`#vt-size`（大字）、`#vt-range`、`#vt-capped-note`、条形图容器 `#vt-band-chart`（8 行 `.vt-bar`，`width:p%` 内联 + 秩区间标签，纯 CSS）、`#vt-notebook-line`（"N new words added to your notebook"，finish 响应 `addedToNotebook`）、`#vt-done`。
- 浮层跟随宿主主题：不自造配色，蒙层/文字/按钮全部继承现有 modal 与 `text-*`、`btn-*` 类。
- ⚠️ **落地修订 1（2026-10-05，caliBlur 截图实测）：浮层结构从自造 `.vt-scrim`+`.panel` 改为 bootstrap 原生 `.modal/.modal-dialog/.modal-content/.modal-body`，显隐用 `jQuery('#vt-overlay').modal('show'|'hide')`。**
  Why: 首版自造蒙层在 `config_theme=1`（caliBlur）下拿到「浅色 panel + 主题白色文字」——caliBlur 的深色规则是**按组件类名**下发的，对 `.modal-content/.modal-body/.modal-backdrop` 有成套规则（`grep -c modal-dialog cps/static/css/caliBlur.css` = 94 条），对自造 `.panel` 蒙层一条都没有，于是词头、按钮、`~8,600`、图表标签全部不可读。复用 modal 才真的「跟随宿主主题」，本页 `<style>` 也因此只剩纯布局规则。
- ⚠️ **落地修订 2（2026-10-05，同一批截图）：`#vt-overlay > .modal-dialog { margin-top: 70px; }`。**
  Why: caliBlur 在 `caliBlur.css:5491` 把 `.modal-dialog` 的上外边距从 bootstrap 的 `30px auto` 改成 `0 auto 60px`，弹层顶到视口上沿、被 60px 固定导航栏压住（`--dump-dom` 实测 dialog `y:0`，默认主题 `y:30` 也仍与 51px 导航栏带重叠）。用 id 选择器抬特异度（0,1,0 → 1,1,0），两个主题统一留出导航栏高度。
  顺带记坑：caliBlur 的 `body.blur .row-fluid .col-sm-10 { animation: fadeIn 1s }`（`caliBlur.css:236`）在动画期间给内容区造出**层叠上下文**（`opacity<1`），浮层的 `z-index:1050` 被关在里面、被导航栏 `z-index:9` 盖住；无头 Chrome 的 `--virtual-time-budget` 会把 CSS 动画冻结在半透明态，拍到的正是这个过渡态。夹具里用 `el.style.animation='none'` 关掉它才能反映稳态（`tests/vt_us4_dump_fixture.py` DRIVE 段）。
- ⚠️ **落地修订（2026-10-05，截图实测发现）：`hidden` 属性在本页不足以隐藏节点，卡片内所有靠 `hidden` 切换显隐的节点统一带 `.vt-el` 类，由模板 `<style>` 里的 `.vt-el[hidden] { display: none; }` 兜住。**
  Why: `{% block header %}` 在 `layout.html:18` 排在 `bootstrap.min.css`（第 17 行）**之后**，属同一层 author 样式表，同特异度后出现者胜——
  我们给蒙层写的 `.vt-scrim{display:flex}` 会盖掉 normalize 的 `[hidden]{display:none}`，bootstrap 自己给 `.help-block` 写的 `display:block` 同理。
  后果是「隐藏态」的浮层与 `#vt-last-line`/`#vt-capped-note` 一进页面就显示（首屏被一层全屏蒙层盖住）。
  纯源码审查与 pytest 都抓不到（模板断言只看属性存在），这是本机静态夹具截图的价值所在。
  规则化：新增需要 JS 显隐的节点时，带 `.vt-el`，不要依赖 `hidden` 单打独斗。
- **`#vt-notebook-line` 显示规则（2026-10-05 用户确认）**：只有 `addedToNotebook >= 1` 才渲染该行；`null`（本次没执行落本：开关关闭、或此前已落过一次的重复提交）与 `0`（执行了落本但本会话没有生词）**都静默**。Why: 「加了 0 个词」不是用户要的信息，两种「没有新增」在结果页读起来是同一件事；而后端仍保留 null/0 的区分，那是审计语义，不上屏。

### 2.3 JS 状态机（定稿：拆独立文件 `cps/static/js/vocab-test.js`）

> 2026-10-05 用户确认。模板现 137 行，状态机 + 渲染 >200 行，内联会让设置页模板翻倍。
> **代价（必须一起做，否则本地化静默倒退）**：静态 JS 拿不到 Jinja 的 `_()`，所有用户可见串走 R112 的
> `mbT(msgid)` 种子通道（`cps/templates/i18n_seed.html`），并且要把 `cps/static/js/vocab-test.js`
> 追加进 `tests/test_i18n_seed_contract.py` 的 `JS_FILES` 硬编码清单——那是源码级契约（key 与 `_()` 实参逐字符一致、
> 每个 `mbT` 用到的 msgid 在种子与 zh 译文里非空）。不加进去，AC-C8 就是假绿。

```
states: idle → asking(currentQuestion) → scoring → result | error(可重试)
```

- **错误判读一律看 `data.code`，不看 HTTP 状态**（对账修订）：后端 `BusinessException` 全部以 **HTTP 500 + `Result.code`** 出口（`GlobalExceptionHandler` 既有行为），参数校验才是 400 + `code=400`，未登录是 401。所以 `response.ok===false` 只表示「不是 2xx」，不区分业务语义；`Result` 信封是 `{success, code, message, result}`。
- `start()`：POST start → 存 `{sessionId, question}` → asking；登录过期按 401 处理（见下方交叉审查修订 2），**50301**（词表未就绪）→ 卡片内 `setStatus` 提示，不进入浮层。
- `answer(known)`：**在途锁**（同一题未收到响应前忽略重复提交，含双击与键盘连击）→ POST answer（body 带 `seq`）→
  - `finished=true`：本地调 `finish()`。注意此时后端会话**已由状态机自然终止并写好估算**，那次 `finish` 的作用是按开关真正落生词本 + 取回 Report（`VocabTestViews.AnswerResult.estimation` 与 Report 字段名不同，见 §4）；
  - 否则渲染下一题（服务端为准，前端**不预生成**任何题）。
  - **50302**（不存在/非本人/已作废/已超时）：直接关浮层回 idle（刷新卡片态）；
  - **50304**（题号错位，seq 跳到前面）：按响应里的当前待答题号重新对齐后继续答，**不丢弃会话**（US3 专门把它从 50302 拆出来的原因）；
  - 其余失败（网络/5xx 无业务码）：`#vt-error-line` "Something went wrong — retry this word"，按钮重试**同一请求**（同 seq 重发由后端 US2 §4 回放，不重复计题）。
- `finish()`：POST finish（body 带 `addUnknownToNotebook`）→ result 视图渲染 → 更新卡片 Last result 区（不整页刷新）。重复调用（刷新结果页/网络重试）是幂等回放，`addedToNotebook` 会变 null，**不能再显示落本提示**，也不得二次落本（后端令牌保证）。
- 键盘：`document.keydown`，仅 asking 态挂载处理；`←/J`→known、`→/K`→unknown、`Esc`→exit。
  - **IME 守卫对账修订（2026-10-05）**：原稿说「复用项目 R114 既有守卫工具函数」——现实是 `cps/static/js/ime_guard.js` 是无 API 的 IIFE，且只守 `target.tagName ∈ {INPUT, TEXTAREA}` 的捕获阶段拦截；本浮层没有可聚焦输入框、监听挂在 document（target=body），**不经过那个守卫**。所以这里自带 3 行判定 `if (e.isComposing || e.keyCode === 229) return;`（与 R114 同口径：既看 `isComposing` 也认 keyCode 229 的浏览器形态），不是新发明规则。AC-C3 仍需用中文输入法实测确认无串扰。
- `exit()`：无请求（后端懒 abandoned），直接回 idle。Why 不发 abandon 请求：省一个端点，30 分钟超时语义已覆盖。
- CSRF：三处 POST 均带 `X-CSRFToken`，取法照模板 74-77 行 hidden input 惯例（浮层无 form，token 从卡片 form 内那个 input 取）；失败自愈沿用 80-88 行模式（`vtCsrfReloaded` 独立标记键）。

### 2.4 交叉审查修订（2026-10-05，独立评审后落地）

评审在实现里挑出 2 高 4 中，全部按下列口径修掉（`cps/static/js/vocab-test.js`）：

1. **在途响应作废（高）**：Exit / Esc / 50302 关浮层后，已发出的 answer/finish 请求的迟到响应仍会执行 `renderQuestion`/`renderResult`，把 `state` 复活成 `asking`/`result` 而 modal 已隐藏——后果是 Start 按钮因 `state!=='idle'` 永久失效（`result` 态下连 Esc 都救不了，只能刷新），且方向键会在看不见的面板上继续提交答案。修法：`closeOverlay()` 递增 `epoch`，三个请求在发出时捕获 `mine = epoch`，`.then`/`.catch` 首行 `if (stale(mine)) return;`。作废判定放在清锁之前是安全的：`closeOverlay` 本身已经把 `inFlight` 归零，不会漏锁。
2. **登录过期判读（高）**：magicbook 的未登录是 `before_request` **302 → 登录页**，fetch 跟随后拿到 `200 + HTML`，`JSON.parse` 失败 → `payload=null` → 旧 `codeOf` 直接返回 `http`（200）→ 取 `.result` 抛 TypeError 进 catch，表现为「永久重试」。修法：`post()` 里带出 `toLogin = /\/login(\?|#|$)/.test(response.url)`，`codeOf` 见 `toLogin` 即按 401 处理；同时非 JSON 的 200 响应返回 `0`（不是 200），走通用失败分支。
   ⚠️ 原稿这里写的「401 走全局登录过期跳转（项目既有 fetch 约定）」**是失实引用**：`ai_chat.js`/`epub.js` 里没有这样一条全局约定。项目里真实存在的口径是 `onboarding.js:620` 用 `xhr.responseURL.indexOf("/login")` 嗅探被登录页兜走，本修法沿用同一判据。
3. **上游文案不上屏（中）**：`messageOf()` 优先把后端中文 `message`（如「词汇量测试暂不可用：分级词表未就绪」）直接显示到卡片，既绕过 `mbT`/`_()` 本地化（与 AC-C8、页面单语纪律冲突），也把内部文案透给用户。修法：删掉 `messageOf`，三处失败提示一律用 `mbT` 定稿文案；`message` 只在 50304 里用来主题号。
4. **50304 无数字时的死链（中）**：后端把 50304 复用在两种文案上——「题号错位，当前应答第 N 题」与「该题正在提交，请重试」（`VocabularyTestService` 的提交互斥）。后者没有数字，旧 `alignSeq` 走 `failAction(null)`：点亮可点击的错误行但 `retry=null`，点了没反应。修法：`alignSeq(known, message)` 解析不到数字时退化为**同 seq 重发**（`sendAnswer(known)`），语义上正好对应「正在提交，稍后重发」。
5. **finish 的 50302 无限重试（中）**：`sendFinish` 对所有非 200 一律 `failAction(sendFinish)`，会话已作废时重试永远不会成功。修法：finish 单列 50302 → `closeOverlay()` + 卡片提示，与 answer 同口径。50303（不足一组）仍留在浮层可重试。
6. **`vtCsrfReloaded` 永不复位（中）**：置位后不再清除，且二次 CSRF 失败静默 `return`（按钮恢复、无提示），下次真过期会被「已刷过一次」分支吞掉。修法：`post()` 里只要拿到可解析的信封就 `removeItem('vtCsrfReloaded')`（拿到 JSON = 这一关过了）。
7. 顺带（低）：顶格文案 `'25,000+'` 原本硬编码三处，改 `cappedLabel()` 从 `BAND_UPPER` 末位推导；`tests/test_vocab_test_proxy.py` 里 `assert "50302" not in message` 是无意义断言，换成「上游 message 原样透传」的等值断言。

**核对后不改的两条**：① `answer` 请求体是 **Integer 0/1**（`VocabTestAnswerRequest.answer` 带 `@Min(0) @Max(1)`），不是布尔——代理与 JS 都按 0/1 发，评审任务书里我写的「布尔」是口误，代码正确；`start` 的 `result` 实为 `{sessionId, question, progress}`（`VocabTestViews`），JS 取用一致。② `_vt_positive_int` 不设上限：雪花 id 的上界校验没有信息量，超大值由后端反序列化直接拒，代理加区间只是噪音。

## 3. 改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/web.py` | +4 代理路由（`/ajax/vocab-test/{start,answer,finish,history}`，一律原样透传 `_moonwell_proxy` 返回值）；`reading_settings()` **不改**（历史改前端异步拉，见 §1 落地修订） |
| `cps/templates/reading_settings.html` | +卡片、+浮层/结果容器（bootstrap modal 结构），`<script src=vocab-test.js>`；模板 137→245 行（DOM＋`<style>`，状态机不在页内） |
| `cps/static/js/vocab-test.js` | 新建 446 行，§2.3 状态机（`mbT()` 取词）；浮层显隐走 `jQuery(...).modal('show'|'hide')` |
| `cps/templates/i18n_seed.html` | 新增本特性 msgid 种子条目（JS 侧文案唯一通道） |
| `cps/static/css/*`（以现有组织为准）或模板 `<style>` | `.vt-progress`/`.vt-bar` 少量样式（≤40 行）＋ `.vt-el[hidden]` 兜底（见 §2.2 落地修订）；实际落在模板 `<style>`，14 条规则（1 条 `hidden` 兜底 + 1 条 modal 上边距修正 + 12 条纯布局），无新配色、无自造蒙层 |
| `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po` | 新增 20 条 msgid 译文 + `pybabel compile -l zh_Hans_CN`（只有 `zh_Hans_CN` 由本项目维护，`zh_Hant_TW` 等走上游，不动）。**改 po 一律写临时文件原子替换**（language-i18n LLD §8 截断事故），译文字典留 `docs/temp/scripts/vt_us4_i18n_patch_po.py`。两个坑（实测）：① 本仓库 babel 的签名是 `write_po(fileobj, catalog, ...)`，参数写反不会报错、会在迭代时报 `io.UnsupportedOperation`；② `width` 必须与 po 生成口径一致（R112 用 76），`width=None` 会把全文件长串重排成单行，凭空 150+ 行无关 diff，正好撞并行会话冲突面 |
| `tests/test_i18n_seed_contract.py` | `JS_FILES` 追加 `cps/static/js/vocab-test.js`，否则新 JS 的本地化契约无人守 |
| 测试 | 新建 `tests/test_vocab_test_proxy.py`（照 reading-settings 代理既有测试风格，**另起文件防并行会话冲突**——见项目共存纪律） |

## 4. 与后端联调核对单（2026-10-05 按 US3 交付物逐字段核实，取代原「待核对」清单）

出参形状以 `VocabTestViews` + `VocabTestEstimator` 源码为准，全部 camelCase，外层套 `Result{success, code, message, result}`：

1. `Question{word, sentence, seq, band}`；`Progress{answered, known, band}`（无总数分母，进度条按固定刻度弱对比）。
2. `AnswerResult{question, finished, progress, estimation}`：`finished=true` 时 `question=null`，前端即调 finish。
3. ⚠️ **两个形状的字段名不同**：`answer` 给的 `Estimation{size, ciLow, ciHigh, capped, reason, bandResults}` 字段是 `size`；
   `finish`/`history` 给的 `Report{sessionId, status, startedAt, finishedAt, questionCount, knownCount, estimatedSize, ciLow, ciHigh, capped, finishReason, addUnknown, bandResults, addedToNotebook}` 字段是 `estimatedSize`。
   结果视图**只从 Report 渲染**（那次 `finish` 必然返回 Report），不要把 `estimation.size` 当 Report 字段用。
4. `BandResult{band, questions, known, rate, contribution}`：条形图用 `rate`（0–1 小数，×100 显示），8 行含未测档（未测低档也在数组里，`questions=0`）。
5. `finish` 幂等回放同一报告（前端网络重试路径依赖）；`addedToNotebook` 非空当且仅当本次调用真的落本（§2.2 显示规则）。
6. 请求体键名：answer = `{sessionId, seq, answer}`，finish = `{sessionId, addUnknownToNotebook}`（必填，缺省等于替用户决定）；报告回显键是 `addUnknown`，与请求键不同名。
7. history 是 `List<Report>`，最近 10 条、`startedAt` 降序、`addedToNotebook` 恒为 null；首屏取 `[0]` 作 Last result。
8. 错误码演练（全部 HTTP 500 + `Result.code`，代理透传不翻译）：**50301** 词表未就绪、**50302** 会话不可用（不存在/非本人/已作废/已超时）、**50303** 答题数不足（门槛是累计 ≥6 题即一个完整探测组，**不是 0 题**——AC-B4 需同步）、**50304** 题号错位。

## 5. 验证方法（2026-10-05 修订：明确本机可验证范围）

- 单元（本机交付门槛）：代理路由参数校验与透传、降级路径、未登录（mock `_moonwell_proxy`）；`i18n_seed` 三条契约；全量 pytest 绿。
- 视觉（本机可做，已做）：夹具生成器 `tests/vt_us4_dump_fixture.py`（文件名不带 `test_` 前缀，`pytest tests/` 不自动收集，显式点名才跑）→ `docs/temp/scripts/vt_us4_shots.sh`（`PAGES`/`STATES` 可用环境变量只重拍受影响视图）→ 两套主题 × 5 态共 10 张，落 `docs/temp/vt_us4_shots/`。
  - 截图新增坑（实测）：`--virtual-time-budget` 不推进 CSS 动画，caliBlur 的 `body.blur .row-fluid .col-sm-10 { animation: fadeIn 1s }` 会冻结在半透明，`opacity<1` 造出层叠上下文，把浮层的 `z-index:1050` 关进 `.col-sm-10` 内、被 `z-index:9` 的固定导航栏盖住——这是**夹具假象**不是产品缺陷，夹具 DRIVE 段里用 `el.style.animation='none'` 关掉才能拍到稳态。定位类问题不要肉眼猜，`--dump-dom` + 注入探针读 `getBoundingClientRect` 一次就能定死。
  - 拍到并已修的产品缺陷两个：① `.vt-el[hidden]` 兜底（§2.2 落地修订）；② 浮层改 bootstrap modal + `#vt-overlay > .modal-dialog{margin-top:70px}`（§2.2 落地修订 1/2）。
  - 拍到但**不属本特性**的既有缺陷（记录不修）：caliBlur 下 `/reading/settings` 的两张 `.panel` 卡片是「浅色面板 + 深色主题控件」，`btn-primary`（既有的 Save、新增的 Start test）与 `text-muted` 历史行在该主题里对比度不足。同页既有 Save 按钮同症状，属主题/页面级问题，本特性不自造配色去打补丁。
- ⚠️ **端到端在本机不可做**（对账修订，取代原稿「moon-well 本地起 + 样本词表」）：moon-well 的数据源由 Nacos 生产 `moon-well.yaml` 下发，本地起服务即连生产库 `magichouse`，不是可写测试的库。所以 AC-C2 完整答题流、AC-C4 拔线重试、AC-C6 落本联调、`15-vocab-test.sh` 全部**留到后端部署后**（fnOS 或带测试库的环境）执行，验收报告须显式标注「本机未验证」而不是当作通过。
- 后端部署前置（否则前端一调用就错，属 US3 遗留清单）：生产 Nacos `moon-well.yaml` 若定义 `resource.ignoring.internalUri` 是**整体覆盖**本地列表，必须同步加 `/vocabulary/test/**`；`app.auth.internal-trust-enabled` 生产实态待测。
- 合入纪律：US4 代码可进本地 `develop`，**不 push**——后端未上线时点入口即 500，与主 LLD §7「入口按钮区在后端就绪前不合入」同源，也与本次「暂不 push」的决定一致。
- 回归：档位设置卡片、IME 守卫无串扰（浮层的 document 监听与 `ime_guard.js` 的 INPUT 域互不影响）、`load_error` 场景测试卡片仍可用。
