# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）
- `response-archive/response-R70-R80.md`：R70–R80（2026-09-22 ～ 2026-09-28；含 R70/R71 历史重复条与 R74 补写条，见文件头说明）
- `response-archive/response-R81-R101.md`：R81–R101（2026-09-27 ～ 2026-09-30；含 R88/R90/R98 补记与重复编号，原样搬移）
- `response-archive/response-R102-R110.md`：R102–R110（2026-09-30 ～ 2026-10-01；R110 条目含 R107/R109 代提交，R120 触发轮转搬入）
- `response-archive/response-R111-R119.md`：R111–R119（2026-10-02 ～ 2026-10-05；2026-10-08 R129 补账搬移）
- `response-archive/response-R120-R125.md`：R120–R125（2026-10-06 ～ 2026-10-07；R135 写入触发搬移，含 R134 登记的窗口欠账补账）
- `response-archive/response-R126-R131.md`：R126、R127、R128、R129、R131（2026-10-07 ～ 2026-10-08；2026-10-09 R141 写入触发轮转搬移，清掉 R134 登记的窗口欠账）
- `response-archive/response-R132-R133.md`：R132、R133（2026-10-08；2026-10-10 R143 写入触发轮转搬移）
- `response-archive/response-R134.md`：R134（2026-10-08；2026-10-10 R144 写入触发轮转搬移，其父级日期标题随节一并搬移）
- `response-archive/response-R143.md`：R143（2026-10-10；2026-10-11 R157 写入触发轮转搬移）

---

> 归档索引：[response-R01-R31.md](response-archive/response-R01-R31.md) · [response-R32-R49.md](response-archive/response-R32-R49.md) · [response-R50.md](response-archive/response-R50.md) · [response-R51-R70.md](response-archive/response-R51-R70.md) · [response-R70-R80.md](response-archive/response-R70-R80.md) · [response-R81-R101.md](response-archive/response-R81-R101.md) · [response-R102-R110.md](response-archive/response-R102-R110.md) · [response-R111-R119.md](response-archive/response-R111-R119.md)（2026-10-08 R129 补账搬移）· [response-R120-R125.md](response-archive/response-R120-R125.md)（2026-10-08 R135 写入触发搬移，含 R134 登记的窗口欠账补账）· [response-R126-R131.md](response-archive/response-R126-R131.md)（2026-10-09 R141 写入触发轮转搬移）· [response-R132-R133.md](response-archive/response-R132-R133.md)（2026-10-10 R143 写入触发轮转搬移） · [response-R134.md](response-archive/response-R134.md)（2026-10-10 R144 写入触发轮转搬移） · [response-R135-R137.md](response-archive/response-R135-R137.md)（2026-10-10 R147 写入触发轮转搬移，含 R145/R146 两次写入的窗口欠账补账） · [response-R138.md](response-archive/response-R138.md)（2026-10-11 R152 写入触发轮转搬移） · [response-R139.md](response-archive/response-R139.md)（2026-10-11 R153 写入触发轮转搬移） · [response-R140.md](response-archive/response-R140.md)（2026-10-11 R153 复核后的补搬——R152 写入时搬走 R138 后窗口仍为 11） · [response-R141-R142.md](response-archive/response-R141-R142.md)（2026-10-11 R155 集成时窗口超限搬移）

## 2026-10-10（R144 每日学习「今日复习 x/20」改版）

### R144（同源 moon-well R143 后端配套：进度式统计头 + 继续复习入口）

- **需求**：moon-well R143 评估通过并已实施（排序/stats 新字段/常量），本仓交付前端半边——「今日到期 1949」压垮用户，改「今日复习 x/20」进度式；队列打空但仍有逾期积压时给「继续复习」，替换失实的「Nothing due right now」。
- **现状根因**（评估轮已查明）：统计头 `dueNow` 是「公元 1 年～now 全部逾期积压」（非今日口径）；阅读标生词即建 `dueAt=now` 调度行，只标不复习 → 1949 纯欠账。队列前端本来就 `?limit=20`，做完 20 张却显示「Nothing due」——余量明明还有 1900+，属于失实承诺。
- **改动**：
  - `learning.html`：统计头第一格「Due now」→「Today's review」（zh「今日复习」），元素 id `ln-due-now`→`ln-today-review`（诚实命名）；`ln-empty` 后新增 `ln-today-done` 完成态面板（「Daily review target reached. Keep going?」+「Continue reviewing」按钮）。
  - `learning.js`：`renderStats` 改渲染 `min(todayReviewed, todayTarget) + '/' + todayTarget`（旧后端无新字段时显示「–」按缺数降级）；新增 `lastStats` 缓存，`nextCard` 队列打空时按 `dueNow>0` 分流「完成态+继续」vs「真没了 Keep reading」；队列加载抽成 `loadQueue()` 供初载与继续按钮共用，`renderQueue` 开新批时收起完成态。
  - i18n：messages.po 增 3 词条（Today's review/Daily review target reached. Keep going?/Continue reviewing）并 `pybabel compile` 重编 .mo（gettext 实测三词条全部命中）；新字符串全走模板 `_()`，JS 未增 mbT 字面量，i18n_seed.html 无需动。旧「Due now」词条留 po 不删（历史词条不回改）。
- **契约依赖**：moon-well stats 增 `todayReviewed`/`todayTarget`（服务端常量 `DAILY_REVIEW_TARGET=20`，前端不写死分母）；queue 排序 R143 起最近学过优先（本仓无感知，行为变化）。部署顺序：先 moon-well 后 magicbook；先发本仓则统计头显示「–」，行为可接受。
- **测试**：开发态闸门 R131——`test_i18n_seed_contract.py` + `test_learning_proxy.py` 22 例、`test_memory_gating.py` 13 例＝ 35 例 0 失败；发布态全量 `pytest tests/` ＝ **363 过 / 25 失败**。25 个失败逐一定性为**与本轮无关的本地环境问题**：失败全落在 reading-vocabulary/tts/translation/book-finished/translate 域（本轮零改动），报错均为登录会话 401；干净 HEAD worktree 复跑同批用例 34 全过、再把本轮 4 个运行期文件（learning.js/html/po/mo）拷入 worktree 复跑 **81 全过**——失败源为工作区本地未跟踪运行态（`app.db` 等，gitignore、不进 commit 与 fnOS 构建），非代码回归。
- **git 纪律**：工作区有并行会话未提交内容（requests.md 的 R145 条目、docs 若干 M、若干未跟踪 L1/归档文件），本轮提交逐文件挑选、requests.md 构造 blob 只含 R144 行。
- **文档**：L1 `docs/readme/learning.md` 两处——复习队列描述加「刚学过、昨天学过的词优先出现」与「达标后可继续加练」，统计改「今日复习进度（x/20…）」。magicbook 无 learning L3（接口契约文档在 moon-well L2/L3，已同步）。
- **部署状态**：**已上线**。`0f6f7a8d..76c7cdaa` push（含此前会话遗留的两条 R143 docs 提交一并随推），17:08 `build END OK (76c7cdaa)` → `app-manager deploy SUCCESS` → 容器 healthy；后端配套 moon-well R143 于 17:20 跟进上线（3029ef8，见其仓 response.md）。统计头 x/20 数字与「继续复习」按钮待用户登录页真机验收（未登录探针只到代理层）。
- **冲突记录**：无。窗口检查：本条写入前窗口为 R134–R143 共 10 条，R134 已按「写入即检查」原样搬移至 `response-archive/response-R134.md` 并登记归档索引，窗口现为 R135 起最近 10 个 request（R138/R139/R140 均为历史同日独立条目）。
- **总结**：requests.md 占号 R144；本条为回应；待用户动作：验收页面（真机）+ 决定 push 时机。

## 2026-10-10（R145：moon-well 全 token 化——代理只认 Bearer，系统身份改 mk- key）

### R145（全 token 化：_moonwell_proxy 废除 X-User-* 互信，一律持凭证调用）

- **同源改造**：moon-well R145 同轮废除内网互信（身份头是「声称的身份」，R144b 已实证 Traefik 剥离中间件无效、可被公网伪造；用户拍板项目未上线不管历史，直接废除）。本仓角色：所有 moon-well 调用改为持凭证。
- **`_moonwell_proxy` 改版**：用户会话透传 `moonwell_access_token`（401 自动刷新一次保留）；会话无 token 干净 401「moon-well 登录已失效，请重新登录」——不再静默降级发互信头（这正是 R144 word-detail 401 的祸根形态）。整本翻译 daemon 快照与 toggleread 桥接从 identity_headers 快照改为 bearer_token 快照；桥接无 token 跳过并留痕（书架归属跟用户走）。
- **系统身份**：启动恢复线程/连接器闭包改用 magicbook-system 服务账号的 mk- API key（fnOS `.env` `MOONWELL_SYSTEM_TOKEN`，moon-well user_id=6 已落库实测 200）。裸 daemon 分支手拼 JSON 不走 jsonify（无 app 上下文会 RuntimeError，R78 同类教训）。`cps/ai/proxy.py` SSE 薄代理同步去身份头、无 token 401。
- **配套**：fnOS `tts-warm/tts_warm.py` 改读 `MOONWELL_SYSTEM_TOKEN`；conftest 给登录客户端注入占位会话 token（贴近真实登录态：登录时 id_token 自动 exchange）。
- **测试**：全量 388/388 绿；受影响用例按新契约改写（Bearer 断言替代互信头断言；R51/R52/R78 三个 daemon 回归用例改为 token/mk- 形态，回归语义不变）。
- **部署**：先于 moon-well 上线（新代理对旧后端完全兼容），push 夹带并行会话已完成未推的 R143 docs ×2 与 R144 学习页 feat 提交（逐笔判类留痕）。
- **待用户动作**：存量已登录会话若原本没有 moon-well token（历史登录/交换失败），首次用阅读功能会提示「请重新登录」——重登即自动换新 token，无需其他处理。

## 2026-10-10（R147：四仓 worktree 规范落地——临时即删模式）

### R147（为四个项目添加 worktree 使用说明：临时模式 vs 占用池模式）

- **结论与依据**：选定**方式一「一任务一临时 worktree，合并后即删」**（收尾闸门 + 长任务例外登记），不采用方式二「固定 worktree 池循环占用」。依据是本机实证：moon-well 2026-10-10 实测两个已完全合并的 worktree 无人收尾、一个落后 origin/develop 3 提交、其中 feat/r145 还带未提交的 compose/hld 改动——池模式三大风险（残留继承/漂移腐化/占用无判定依据）本机已各有一例；而本仓 R144 正是靠干净 HEAD worktree 复跑才把 25 个测试失败定性为本地运行态污染——干净检出本身就是被验证过的价值。冷启动不构成选池模式的理由（本仓 venv 实测可跨 worktree 复用）。
- **落地改动（五处）**：家族根 `AGENTS.md` 新增「Git Worktree 开发纪律」统一口径节 + 文档规范共性纪律增第 ⑥条；四仓 AGENTS.md 各新增「🔀 Git Worktree 使用规范」节。本仓细则要点：worktree 建仓库外兄弟目录（`magicbook-<slug>`）；分支从 `origin/develop` 最新点切出；收尾闸门固定为 merge → `worktree remove` → `branch -d`（只用小写 `-d`，未合并被拒即停下排查；`-D` 属破坏性操作需用户确认）；主检出 `.venv` 实测可复用（`../magicbook/.venv/bin/python -m pytest`）；worktree 内无运行态数据正是 R144 干净复跑的原理。
- **编号说明**：原按同源预留 R146，占号时发现已被并行会话的「MagicLens 接管检测」占用，按纪律续编 **R147**；同源任务 moon-well R146 / magiclens R38（同理续编）/ app-manager R38。
- **窗口**：本条写入前窗口实存 12 个 request 的回应（R135–R146；R145/R146 两次写入均超窗未轮转，属欠账），本条一并补账——R135/R136/R137 三节原样搬移至 `response-archive/response-R135-R137.md` 并登记归档索引，窗口恢复为最近 10 个 request（R138–R147）。
- **总结**：requests.md 占号 R147；本条为回应 + 窗口欠账补账；冲突记录：R146 编号冲突（并行会话占用，已按纪律续编，未回改他人条目）。本任务只改文档与对话记录，未动任何代码。

### R146（让位从写死改为探测 MagicLens 的接管标记）

- **需求**：能否检测——发现装了 magiclens 就隐藏，否则不隐藏。跨仓同源：magiclens R37（v0.8.6）负责写标记。
- **为什么这个需求是对的**：R141 的静态开关把「装了扩展」当成「这条能力在此处通」。两轮之前它就不成立——v0.8.5 之前扩展装着、iframe 拖选却不通（`about:srcdoc` frame 注入不进去），而写死的开关已经把内置气泡关掉，用户看到的是「选中单词毫无反应、波浪线却正常」。检测的语义因此定为**接管状态**而非存在状态。
- **交付**：`epub.js` 删掉 `LENS_OVERLAP_UI_ENABLED`，改为两个探测，粒度对应两套属主——`lensOwnsSelection(content.document)` 读本帧 `data-magiclens-selection`（决定内置划词气泡）、`lensOwnsHighlight()` 读顶层 `data-magiclens-highlight`（决定内置波浪线，其引擎随 Alt+U/域名禁用/登出自清标记）。读不到就保留内置，覆盖四种情况：未装扩展 / 扩展过旧（<0.8.6 无标记）/ 该 frame 注入失败 / 用户关了高亮。标记值是扩展版本号，排障看 DOM 属性即可分辨属于哪一种。段落「译」按钮、整页/整本翻译、朗读、批注、伴读、右键菜单、`inspectVocabulary` 每页上送均不受影响。
- **测试**：`tests/test_reader_lens_handoff.py` 按新语义重写（探测函数与属性名、两处门控点、`inspectVocabulary` 不被门控、**不得残留静态开关**的反向锁、段落按钮不被门控），加 `test_reading_vocabulary + test_no_duplicate_js_lines + test_i18n_seed_contract` 一起跑 → **44 passed**；`node --check epub.js` 通过。开发态口径（用户未提正式发布）。
- **文档**：L1 三处（`readme.md` 概览与快速开始第 2 步、`readme/reading.md`、`readme/vocabulary.md`）改为「装了才接管，没装时阅读器自带」；L2 `docs/vocabulary/hld/hld.md` 能力边界、L3 `docs/reading-vocabulary.md` 状态注记同步（并保留 R141 原分析、以删除线标注旧落点）。
- **⚠️ 上线顺序（必须先扩展后本站）**：现在线上扩展是 **v0.8.5，它不写任何标记**。若先推 magicbook 这版，探测恒为假 → 内置气泡与波浪线全部回来，而 v0.8.5 扩展仍在同页画它自己那份 → **双气泡、一词双线重现**，正是 R141 当初要消除的现象。正确顺序：① magiclens 0.8.6 发出并让用户在 `chrome://extensions` 重载 + 刷新页面；② 再推 magicbook `develop`（push 即触发 fnOS 构建上线）。本轮 magicbook 改动**已提交未推送**（`b3f7fd5f`）。
- **编号更正（教训入档）**：本轮初稿在代码注释与 L1/L2/L3 里都写成 **R144**，占号时才发现 144/145 已被并行会话占用（每日学习页改版 / moon-well 全 token 化）。已把我写的 8 处 R144 全部改为实际号 R146（占号 commit `7cca2b2f`），他人条目一字未动。**下次动笔前先占号并 commit，再往代码注释里写编号。**
- **总结**：requests.md 本条 R146；response.md 本条使窗口达 10 个 request 的回应（R135–R146，其中 R142 含补记），未超 10，无需搬移；冲突记录：本轮唯一并发问题是编号撞号（已按纪律更正而非回改他人条目）。

## 2026-10-11（R151：四股台账前端——计划行 actual/budget + 阅读活跃心跳）

### R151（四股时间预算实装统计·magicbook 侧，随 moon-well R150 后端）

- **交付**（worktree `../magicbook-strand-ledger`，分支 `feat/r151-strand-ledger`）：
  - **`cps/static/js/reading/reading_time_tracker.js`（新）**：阅读活跃心跳——页面可见且最近 3 分钟内有交互（翻页/滚动/点击/按键/触摸，capture+passive 监听）才计活跃；30s 结算、每累计 300s 批量 POST `/ajax/learning/strands/reading`；`pagehide` 用 `fetch keepalive` 补发 ≥30s 的尾巴；上报失败静默丢弃（宁低估不重试堆积、不打断阅读）。vanilla JS 零依赖（readtxt/readpdf 无 jQuery），read/readpdf/readtxt 三模板已挂（readcbr/readjvu 暂不挂）。
  - **模板**：readtxt.html / readpdf.html 补 `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`（全局 CSRFProtect 强制 POST 校验，原两模板无 csrf 输入）；read.html 在 epub.js 后挂 tracker。
  - **`cps/web.py`**：新增 `/ajax/learning/strands/reading` 代理——seconds 域校验 30..600（bool/非整数/越界一律 400 不打上游）、bookId 可选纯数字；`_moonwell_proxy` 5s 短超时（心跳失败静默语义）。
  - **`cps/static/js/learning.js`**：四股行改 actual/budget——`标签 earned/budgetmin`（如「阅读输入 10/5min」）；earned 为 null（ES 降级或旧后端）显示 `–` 自动退回旧口径；零新增 i18n 词条。
- **测试**：`tests/test_learning_proxy.py` 增 4 例（合法转发含 bookId、无 bookId 省字段、seconds 域外 400×9、bookId 非法 400×5）+ 登录门槛断言加新端点；与 `test_i18n_seed_contract` 合跑 26 passed（复用主检出 `.venv`，R146 纪律）；`node --check` 两份 JS 通过。
- **跨仓同源**：moon-well R150（台账/心跳/汇总后端，同日交付）。
- **归档更正**：初稿曾自建 `response-archive/response-R135.md` 并宣称本条写入触发 R135 搬出——rebase 时发现 R147 会话已先行做过 `response-R135-R137.md` 轮转（含 R145/R146 欠账补账），我的归档文件冗余，已删除并沿用其索引；本条写入后窗口为 R138–R151 共 10 个 request，未超限。
- **总结**：requests.md 本条 R151；response.md 本条（本节为 rebase 残留补录）；冲突记录：requests.md 冲突（147–149 并行条目与我的 151 同区）按两侧保留解决。

## 2026-10-11（R152：说与写页面——写作工坊 / AI 口语陪练 / 复述训练）

### R152（B1 输出训练前端，随 moon-well R150 四股台账后端；P2）

- **交付**（worktree `../magicbook-speaking-writing`，分支 `feat/r152-speaking-writing`，基于 origin/develop 8c8a2ea；**worktree 驻留不关——用户指令：完成后由用户确认关闭**）：
  - **`cps/templates/speaking_writing.html`（新）**：三 tab（写作工坊 / AI 口语陪练 / 复述训练），bootstrap tabs + 面板结构与 csrf 输入，静态文案走 Jinja `_()`。
  - **`cps/static/js/speaking_writing.js`（新）**：三面板小状态机——写作（出题→初稿→批改渲染→修订→进步确认→历史）、口语（场景/风格→开聊→消息流含分层反馈→结束出报告→历史回放）、复述（粘贴段落→4/3/2 倒计时逐轮→纯指标回执→AI 总结）；统一 Result 信封解析、在途锁防 LLM 端点连击；mbT 词条 24 个。
  - **`cps/web.py`**：`/learning/speaking-writing` 页面路由 + 12 个 B1 代理（写作 4 / 口语 5 / 复述 3）。通用 `_b1_payload` 白名单裁剪（未知键不透传、字符串限长 200–20000、durationMs/round 保 int 透传、minutesPerRound 1..30 域校验），LLM 密集端点 90s 超时、指标端点 15s。
  - **`cps/templates/layout.html`**：Settings 菜单加 `top_speaking_writing` 入口（Daily Learning 之下）。
  - **i18n**：i18n_seed.html 增 23 条 JS 词条；messages.po 增 67 条（模板 `_()` + JS `mbT` 全覆盖），pybabel 重编 mo；test_i18n_seed_contract 的 JS_FILES 纳入 speaking_writing.js（R116/R132 先例）。
- **测试**：`test_learning_proxy.py` 增 7 例（10 端点登录门槛、白名单裁剪、缺必填 400×5、超长文本 400、整数字段保型、minutesPerRound 域校验×6、页面渲染断言），加 i18n 契约、no_duplicate_js_lines、nav_settings 共 **40 passed**；`node --check` 通过。
- **范围说明**：口语与复述 P2 用打字转写（ASR 待百炼订阅开通后接 LEARNING_ASR_API_KEY 即可升级为真开口）；朗读 coach 回复暂用纯文本（TTS 自动播放属 P3 打磨）。
- **总结**：requests.md 本条 R152；response.md 本条使窗口达 11，按写入即检查把 R138 原样搬移至 response-archive/response-R138.md 并登记索引，窗口 R139–R152；冲突记录：无。

## 2026-10-11（R153：P3 输出训练扩展——计时重读/听写/周视图/coach 朗读）

### R153（计时重读 + 听写 tab、四股周视图、coach 回复 TTS；随 moon-well R152 查词补报端点）

- **交付**（worktree `../magicbook-fluency`，分支 `feat/r153-fluency`，基于 origin/develop 2a3d6f84；worktree 驻留待用户确认）：
  - **web.py**：新增 6 个代理（listening materials/paragraphs/dictation-check、rrr record/trend/recommend）+ strands/summary 周视图代理；`_b1_payload` 扩展布尔（addUnknown）与 order 整数字段。
  - **speaking_writing.html/js**：新增「计时重读」「听写」两个 tab——RRR：素材选择（tts 书源）→ 段落列表（或「含到期词的段落」推荐直取 trend 正文）→ 计时朗读三遍（mode=ALOUD，durationMs 实测）→ 每轮 WPM + 首次/最佳/提升趋势；听写：ted 素材 → 段落音频播放（audioUrl+起止裁剪，缺省走 /ajax/reading-tts 兜底合成）→ 词级 diff 四色渲染（MATCH/WRONG/MISSING/EXTRA）→ 漏错词一键入复习队列。**coach 回复自动朗读**：复用阅读 TTS 代理（AI 临时语音档），面板开关。
  - **learning.html/js**：统计头下新增「四股周视图」面板——近 7 天各股入账堆叠条（段宽按当日预算归一，title 显 单股 实际/预算，右侧当日合计分钟），随计划加载刷新，ES 降级整面板隐藏。
- **依赖**：moon-well R152（/learning/strands/lookup，magiclens 补报用）已先行上线 f39c899；本仓零 moon-well 阻塞。
- **测试**：`test_learning_proxy.py` 增 6 例（6 端点登录门槛、听写 bool/int 透传、非法类型×3 本地 400、RRR 整数保型、两页面渲染断言），合计 46 passed；`node --check` 两份 JS 通过；i18n 契约 5 例（种子 +11、po +21，mo 重编）。
- **范围说明**：影子跟读（shadowing evaluate 需浏览器录音上传基建）本轮明确不做；magiclens 直连查词补报由 moon-well R152 + magiclens 侧后续任务落地。
- **总结**：requests.md 占号 R153；本条为回应；冲突记录：无。归档：窗口未超（R139–R153 仍在 10 窗内）。

## 2026-10-11（R154：导航层级修正——学习入口一级平铺 + 学习页直达说与写）

### R154（用户反馈：学习入口藏 Settings 里层级不对）

- **交付**（worktree `../magicbook-learning-nav`，分支 `feat/r154-learning-nav`，基于 origin/develop 37edb78；worktree 驻留待用户确认）：
  - **layout.html**：「每日学习」「说与写」从 Settings 下拉撤出，提为左侧一级导航（与高级搜索平级，登录后可见，移动端只留图标）；收纳注释同步更新（R154 例外，防后人按旧口径收回去）。
  - **learning.html**：Today's Plan 面板标题右侧加「Speaking & Writing →」直达跳转（练完复习接输出，零新增词条，"Speaking & Writing" 复用既有 po 词条）。
- **测试**：`test_nav_settings_dropdown.py` 增 1 例（两项全页各出现一次且不在下拉块内，防回流）；`test_learning_proxy.py` 页面渲染断言扩为含跳转链接；合计 46 passed。
- **总结**：requests.md 占号 R154；本条为回应；冲突记录：无。归档：窗口未超。

## 2026-10-11（R155：worktree 规范微调——merge 后保留待验收，验收通过后删除）

### R155（worktree 收尾闸门改两段式：merge 后保留等验收）

- **用户指令**：不要 merge 即删除 worktree，改为 merge 后保留等用户验收，验收通过后再删除。规范主体（临时 worktree、非占用池、从 origin/develop 切、仓库外兄弟目录）不变，只改收尾时序。R152 已出现「worktree 驻留不关（完成后由用户确认关闭）」的在例——本次修订正是把这一实际工作方式回写为正式规范。
- **落地改动**：家族根 `AGENTS.md`「Git Worktree 开发纪律」收尾闸门改两段式（merge 后 worktree 原样保留等验收）+ 台账条目改「驻留台账」+ 证据条补记本次用户修订；四仓 AGENTS.md 同步微调。本仓细则新增「验收期驻留（正常状态）」：登记分支名与合并 commit，验收通过后立即删除；并写明本仓验收优势——干净 worktree ＋ 主检出 `.venv` 复用＋拷贝当轮运行期文件即可真机整站验收（R144 已验证）。
- **窗口**：与远端 R153/R154 集成后窗口含 R141–R155 共 12 个 request，把最旧的 R141、R142 两节原样搬至 `response-archive/response-R141-R142.md` 并登记索引，窗口恢复 10 个（R143–R155）；此前本条初版已搬 R139/R140（当时窗口 11）。
- **编号说明**：本条与并行会话的 P3 输出训练（R153）、导航层级修正（R154）集成时发现同号 153 已被先行推送占用，按纪律续编 155；同源任务 moon-well R153 / magiclens R41 / app-manager R39。
- **总结**：requests.md 占号 R155（与并行会话 P3 输出训练撞号 153 后按纪律续编）；本条为回应；冲突记录：R153 撞号如上。本任务只改文档与对话记录，未动任何代码。

## 2026-10-11（R156：词汇量测试「细筛」入口——代理透传/前后对照/细档图）

### R156（细筛前端：magicbook 侧交付，跨仓同源 moon-well R155）

- **交付**（worktree `../magicbook-vocab-refine`，分支 `feat/r154-vocab-refine`，基于 origin/develop 37edb778；merge commit 1d8309f1，worktree 驻留待用户验收）：
  - **代理**：`/ajax/vocab-test/start` 增 refine 标志透传——只认显式布尔 true，其余（缺省/false/字符串）一律按标准测试转发空体，语义分叉只在 moon-well 一处。
  - **vocab-test.js**：卡片（有标准结果时）与结果页各一个细筛按钮（报告 `testType` 驱动显隐，对细筛结果不提供二次细筛）；50305（无可细筛基座）回卡片态提示；细筛结果渲染「上次估算」对照行；掌握度图标签按报告 `bandRanges` 秩区间标注（细档序号只在会话档位表内有意义），后端未升级时退回硬编码档名。
  - **模板/i18n**：两个按钮 + 对照行落 reading_settings.html；`Refine test / Previous estimate / Take a standard test first…` 三词条进种子与 zh po/mo。
- **测试**：代理透传矩阵用例 +1（true→透传、false/"yes"/缺省→空体）；i18n 种子契约对新词条自动生效；全量 pytest 407 例绿。
- **编号说明**：本任务原占 154（与并行导航修正撞号），占号条目在工作区被并行提交操作清除；按「不改既存、续编空号」纪律落为 156，既有 commit 内 R154 文案不改。
- **总结**：requests.md 续编 R156 占号；本条为回应；冲突记录：无（合并为真 merge 无内容冲突；stash 恢复的并行未提交改动原样留在工作区，归其 owner）。归档：窗口 R147–R156 共 10 条未超窗。

## 2026-10-11（R157：整本连播（听书）——顺序逐段朗读整本书，随时暂停）

### R157（R155/R156 评估结论落地：moon-well 零改动，播放队列全部在阅读器前端）

- **需求**：为书籍增加一个整本阅读功能：按照顺序一段一段持续朗读，随时可以暂停。（编号说明：R155 评估轮占号 155 及其回应条目曾被并行提交操作清除；155/156 已被并行会话的 worktree 规范/词汇细筛占用，按「不改既存、续编空号」纪律落为 157。评估结论在 moon-well response.md R156 有留档。）
- **交付**（worktree `../magicbook-whole-book-read`，分支 `feat/r157-whole-book-read`，基于 origin/develop 41918028）：
  - **moon-well 与 web.py 零改动**（评估已证：/tts/speak 同步音频 + SHA-256(原文) 永久缓存 + 顺序串行天然合规）；
  - `epub.js` 新增独立播放队列状态机 `bookPlayer`（与单段朗读 `activeTts` 互斥让位）：collectParagraphElements 收集本章段落 → 归一化 + 2000 字符切块（句读优先断句，长段不再静默截断）→ 逐块 `POST /ajax/reading-tts` → Audio(blob) 播放 → ended 接下一块；本章耗尽 `rendition.next()` 等 `rendered` 重建队列，spine 尽头自动停并提示「已到全书末尾」；
  - 暂停/继续：`audio.pause()/play()` 段内保留进度；合成期间暂停 = 就位 blob 不开播，点击即续；
  - 预取：当前块 onplay 后预取下一块，全程 ≤1 个在途合成（NAS 本地 TTS CPU 瓶颈、MiMo 100 RPM）；
  - 视图跟随：当前段不在可见页才 `display(段落实时 CFI)` 跳页（实时 CFI 无旧 CFI 越界毒化显示队列风险）；
  - 章界：空文字章节（纯图片封面页）自动跳过（≤10 章上限）；20s 未渲染按翻章失败收尾；
  - 手动导航跟随：rendered 非 internalNav → 重建队列——同章重渲染（字号/主题/分栏）按 lastStartedText 续听原块、换章从新页顶部起播；章内翻页不打断播放；
  - UI：标题栏 `#tts-book`（▶/❚❚ 切换）+ `#tts-book-stop`（■，连播中显示）；当前段 `.reading-tts-speaking` 高亮；8 条新文案走 mbT 五步链；
  - 文档：L1 reading.md 朗读条目扩写+整本连播、L3 深入阅读加链；L2 reading hld 新增 §1.1（无新契约）；L3 `docs/feat/whole-book-listening/design/whole-book-listening-design.md` 新建（状态行已上线）。
- **测试**：i18n seed 契约 5 例绿（JS 字面量 ⊆ seed = po = mo，8 条新词条四层一致）；test_reading_tts + test_csp_media + test_nav_settings_dropdown 20 例绿（代理层零改动回归）；node --check 过；epub.js 全模块通读交叉审查一轮（据此修出：空文字章自动跳过、emptySkips 初始化与重置、FireWaiters 唤醒链抽取）。
- **归档**：本条使窗口达 11，最早一节 R143 原样搬至 `response-archive/response-R143.md` 并登记索引，窗口 R144–R157。
- **总结**：requests.md 占号 R157（在 worktree 内落盘，随本分支 merge 入 develop，避开主检出并行覆写区）；本条为回应；冲突记录：R155 评估轮的占号/回应曾被并行提交清除（已在编号说明留痕），本轮在干净基线重落为 157；worktree 交付后驻留等用户真机验收（AC 见 L3 design §4），验收通过后按两段式闸门收尾。
- **验收与收尾（同日回填）**：用户确认验收通过（2026-10-11「此任务完成的非常好，可以收尾」）——按两段式闸门收尾：worktree `../magicbook-whole-book-read` 已 `git worktree remove`、分支 `feat/r157-whole-book-read` 已 `branch -d` 删除（内容已随 e6a51c48 并入 develop 并部署上线，线上冒烟见前文）。

## 2026-10-11（R156：麦克风按钮可用性修正——带标签/状态自更新/用法提示）

### R156（用户反馈：「只有一个空白按钮」不会用）

- **交付**（worktree `../magicbook-mic-ux`，分支 `feat/r156-mic-ux`，基于 origin/develop ac10e64c；worktree 驻留待用户确认）：
  - 两个麦克风按钮从纯图标改为 **图标 + 文字标签**（「语音输入」），图标字体缺失时也不再是空按钮；
  - 状态全部自更新在按钮上：空闲「语音输入」→ 录音中红底「录音中 0:12 · 再点停止」→「转写中…」（转写期间防连点禁用）→ 回填后复原；
  - 口语面板加一行用法提示（点麦克风开始说话 → 再点一次停止转写 → 结果回填输入框确认/修改后发送；首次使用会请求麦克风权限）。
- **测试**：页面断言（标签 ≥2 处 + 提示行）+ i18n 契约（种子 +1/po +4，mo 重编），45 passed。
- **总结**：requests.md 占号 R156；本条为回应；冲突记录：无。归档：窗口未超。

## 2026-10-11（R158：麦克风转写卡死修复）

### R158（「转写中…」永远不结束：els 注册表漏项 + 同步 TypeError 防御）

- **根因定位**（ES app-log-magicbook + docker logs + 代码比对）：停止分支 `statusNode.textContent = ''` 对未注册的 `els['sw-s-audio-status']`（undefined）赋值 → 同步 TypeError 在 fetch 之前炸掉 → 无 alert、按钮禁用、标签停在「转写中…」——且服务端零日志（请求根本没发出）。只影响口语面板（复述的 sw-r-metrics 已注册）。注册表漏项是 R155 建表时只列了麦克风按钮、R156 改 statusNode 引用时未同步注册表所致。
- **修复**：①注册表补 `'sw-s-audio-status'`；②停止分支同步段包 try/catch——任何异常都复原按钮 + 提示，永不卡「转写中…」；③新静态测试 `test_speaking_writing_static.py` 双锁：JS 引用的每个元素必已注册、注册表每个 id 必在模板（此类错误 pytest 页面断言抓不到）。
- **顺带排查结论**（另两条独立线）：①moon-well 直连实测 SiliconFlow 引擎链路 OK（key 200、热重绑 provider=siliconflow 生效），但 RestTemplate 文件 part 默认 octet-stream 会被 SiliconFlow 500 [no body]（audio/wav 同请求 200 实测）——已修（moon-well R160：文件 part 按扩展名给标准 audio/* MIME）；②**Nacos 里的 siliconflow api-key 现在返回 401 Token is invalid**（14:05 实测 200 → 14:2x 失效）——用户需在 SiliconFlow 控制台取当前 key 重新填入 Nacos。
- **测试**：静态完整性 2 例 + 代理 40 例 = 42 passed。
- **总结**：requests.md 占号 R158；本条为回应；冲突记录：无。归档：窗口未超。
