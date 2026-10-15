# LLM 队列监控面板（R130 · US4 admin-monitor）

> L3 详细设计 | 状态：**设计待确认**（未写代码）
> 需求原文：`requests.md` R130（跨项目：对端 moon-well R118）
> 对端设计：`moon-well/docs/feat/llm/design/llm-task-monitor.md`（6 个 `/llm/task/admin/**` 端点 + 恢复语义）
> 同族文档：本 feat 的 [admin-panel.md](./admin-panel.md)（R126 · 手动执行面板）——本页是它的**扩展**，不是第二块面板

## 1. 目标与边界

给管理员一块「看得懂队列」的入口：现在排到哪了、为什么失败、还要跑多久、这批失败的能不能救。
R126 已经给了「跑」，缺的全在「看」——R109 放量 top 10k 详解任务当天，队列被一次 DNS 抖动在
9 分半内烧穿 7,596 条，而 magicbook 面板上只显示「待处理 0」，管理员无从分辨「跑完了」和「全挂了」。

边界（沿用 R126 §1，一字不改）：

| 不做 | 原因 |
| --- | --- |
| 队列/状态机/失败分类语义 | 权威全在 moon-well。前端一旦自己判「能不能重发」，就长出第二套恢复口径，而 R110 的重放门禁是建立在 `started_at`/终态之上的（moon-well R110 §5 缺陷 A 踩过） |
| 请求体字段映射层 | 直接按 moon-well DTO 命名透传，多一层 snake_case 会让两侧契约漂移无人发现 |
| 新页面 / 新 blueprint / 新 proxy | 复用 `_moonwell_proxy`（`cps/web.py:1209`）+ `_llm_task_admin_gate()`（`web.py:795-804`），并入 `cps/templates/llm_tasks.html` |
| 内网互信通道 | 恢复动作会新增上千条 PENDING 并真实消耗配额，必须带管理员本人 token 供 moon-well 白名单归因 |

## 2. 接口清单（转发）

`cps/web.py` 新增 6 个视图 + 1 张路径表（其中 detail 转发到 moon-well 既有的 /llm/task/detail）；全部 `@user_login_required` + handler 内
`current_user.role_admin()` 返回 **JSON 403**（不用 `@admin_required`，它 `abort(403)` 给的是 HTML）：

| magicbook 路由 | 转发到 moon-well | 超时 | 请求体 |
| --- | --- | --- | --- |
| `/ajax/llm-task-admin/overview` | `/llm/task/admin/overview` | 10s | `{}` |
| `/ajax/llm-task-admin/failures` | `/llm/task/admin/failures` | 15s | `{caller?, sinceHours?, bucketSize?}` 原样透传 |
| `/ajax/llm-task-admin/page` | `/llm/task/admin/page` | 10s | 筛选表单原样透传 |
| `/ajax/llm-task-admin/detail` | `/llm/task/detail`（moon-well US3 决定复用既有端点，只放开归属校验） | 10s | `{taskId}` |
| `/ajax/llm-task-admin/recovery-plan` | `/llm/task/admin/recovery-plan` | 20s | `{caller?, errorCode?, limit?}` |
| `/ajax/llm-task-admin/republish-failed` | `/llm/task/admin/republish-failed` | 30s | 预案入参 + `confirm:true` |

`_LLM_TASK_ADMIN_PATHS`（与 `_LLM_TASK_PATHS` `web.py:780-785` 并列成表，不散落字符串）。
`/llm-tasks` 页面路由不变（仍 `@user_login_required + @admin_required`），`layout.html` 导航项不变——同页扩展，不新增入口。

**为什么 republish 的超时给到 30s**：它是唯一会写库的端点，上限 `maxTasksPerRun=5000`、逐条
`publishTask` 各自事务。实测 R109 驱动 500 条/窗 4.6s，2,000 条量级会逼近 20s；这里不能沿用 15s
默认值，否则管理员看到「service unavailable」而服务端其实还在继续发（`_moonwell_proxy` 的
`RequestException` 分支正是这个形态，`web.py:1280-1282`）——**前端超时不等于任务停止**，这条要在 UI 上说明。

## 3. 页面结构（`cps/templates/llm_tasks.html` 内新增三块，现有执行区块保持不动）

顺序：总览 → 失败分布 → 任务查询 → **手动执行（R126 原区块）**。理由：管理员进这页的第一问题是
「现在什么样」，执行是看完之后的决定，把表单顶在头上等于逼他盲跑。

### 3.1 队列总览 `#lr-mon-overview`

- 卡片行：`pending / accepted / running / completed / failed`（按 caller 展开成小表格，
  caller 多于 4 个时折叠为「其它 N 个 caller」）
- 关键判据行：**最老 PENDING 时长**、**最近一次完成时间**、**最近一次领取时间**、近 3h 速率、ETA
- `staleRows.acceptedOverThreshold > 0` → 黄条「有 N 条被领取后超过 {阈值} 未回写（worker 疑似崩溃），
  下次巡检会自动回队重排」；同排显示 `reclaimed = {acceptedRequeuedLast24h, acceptedExhaustedLast24h, lastSweepAt}`，
  语义是「救回 N 条 / 放弃 M 条」，**不与失败数混排**（回收是运维动作，不是错误）
- 阈值与上限由 moon-well 在 overview 里回显（`acceptedTimeoutHours` / `acceptedMaxRequeue`，
  源头是 `ai.llm.task-auto-execute.accepted-timeout-after` 与 `accepted-timeout-max-requeue`，
  Nacos 可热改）；面板**只读展示、不提供配置入口**，也不许自己写死 24h/3 次
- **不提供「立即回收」按钮**：巡检 10 分钟一轮，服务端手动触发只会造出第二套终结路径，风险大于收益
- `STALE_EXHAUSTED`（`ACCEPTED_TIMEOUT_EXHAUSTED`，重排队次数用尽）单独一行红色提示
  「同一任务已被放弃 K 次，需人工查 worker」，恢复方式栏显示 FORBIDDEN 而非任何按钮
- `etaHours` 为 `null` 时显示「暂无稳定速率」，**不显示 0**（显示 0 会被读成「马上就完了」）
- 轮询：**15s** 一次（不是 R126 进度区的 4s）；页面不可见时暂停。总览是聚合查询，
  按 4s 打会对 moon-well 造成每秒数百次的无效 group by

### 3.2 失败分布 `#lr-mon-failures`

- 表：分类 / 条数 / 起止时间 / 建议恢复方式 / 样例 taskId / 近 24h 每桶计数
- 分类行左侧色标：`REPLAY`（可原地重放）· `REPUBLISH`（需重新发布）· `FORBIDDEN`（禁自动恢复，先修根因）
- 「建议恢复方式」直接渲染 moon-well 返回值，**前端零判断**
- 行内按钮「按此分类看任务」→ 把 `category` 填进 3.3 的筛选条件并重查
- 顶部一行说明「UNKNOWN 占比」：占比高提示签名表需补，不隐藏

### 3.3 任务查询 `#lr-mon-tasks`

- 筛选：caller / status / errorCode / userId / keyword + 「查询」按钮；分页 50 条
- 列表列：taskId、caller、status、model/provider、耗时、tokens、errorCode、`errorMessage` 截断、`createdAt`、操作
- 行点击 → Bootstrap modal（成例 `cps/templates/admin.html:247-264`）调 `/detail`，展示 `promptText` /
  `responseText` / `errorMessage` 全文 + `requestParamsJson` 格式化
- **不做 server-side 分页插件**（不用 `static/js/table.js` 的 bootstrap-table 旧范式），自制页码即可

### 3.4 恢复入口 `#lr-mon-recovery`

- 按钮「生成恢复预案」→ `/recovery-plan`（**dry-run，不写库**），渲染三分类条数 + 建议路径 + 样例
- 预案表下方才有「执行重新发布」按钮：需二次 `confirm()`，且 UI 上把「将新增 N 条 PENDING ≈ 约 M tokens」
  写在按钮文案里（数字来自 moon-well 返回，前端不做乘法估算）
- moon-well 返回护栏拒绝（NETWORK 故障 10 分钟窗口内）时，**原样显示 message**，不吞、不改写——
  那条提示正是让管理员先去修网络再点按钮的唯一信号
- `STALE_CLAIM`/`ACCEPTED_TIMEOUT` 类**既不显示「重新发布」也不显示「重放」按钮**：巡检已把它回队重排
  （`accepted_by` 清空、`requeue_count+1`），管理员要做的只是查清 worker 为什么死
- `started_at IS NULL` 的其它失败仍指引勾选 R126 已有的「Replay failed tasks」——同一词最多只有一条待执行行

### 3.5 复用而非新造

模板内既有 `ajax(url,payload)`（`llm_tasks.html:131-151`，判 404/success/unwrap `result`）、
`note()` 提示、`lr-csrf` + `X-CSRFToken` 头、`optionsSeq` 过期回包丢弃（:107,249）全部沿用；
新脚本继续写在模板内联 IIFE 里，**不建 `static/js/llm_admin.js`**（R126 先例，也避免多一个需缓存刷新的静态文件）。

## 4. i18n

新增约 60 条英文 msgid 进 `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po` 并**重新编译 `messages.mo`**
（成例 R124/R126）。模板 `<script>` 内字符串一律由 Jinja `_()` 渲染——本项目 JS 侧没有 `_()` 实现，裸写 ReferenceError。

## 5. 上线前置条件（顺序敏感）

1. **moon-well 先发版**（R118 的 6 个端点 + Guard + options 门禁），否则总览区加载即报 404，
   R126 的 options 也会因收紧后 403 而让面板空白——两件事同一轮上线，不能只发前端。
2. 确认 magicbook 管理员在 moon-well 侧映射到的 userId ∈ `ai.llm.task-manual-run.admin-user-ids`
   （OIDC 换票得到的账户，不一定是 1，见 `admin-panel.md` §5.2）。options 门禁收紧后，这一条从
   「跑不了」升级成「面板打不开」，症状变化要写进 AC。
3. 无新增环境变量：继续复用 `MOON_WELL_READING_URL`（`cps/constants.py:142`）。
4. 无数据库变更（表在 moon-well 侧）。

## 6. 测试（`tests/test_llm_task_admin_monitor_r130.py`）

沿用 `tests/test_llm_task_run_r126.py` 的断言范式（monkeypatch 替 `_moonwell_proxy`）：

1. 6 条转发路径的 `path/payload/timeout` 逐条断言（timeout 不能漂回默认值，§2 的理由）
2. 请求体逐字节透传；空 body 不崩
3. 非管理员访问 6 个 JSON 入口全部 JSON 403（不是 HTML 403）
4. 上游 403/护栏拒绝时 `message` 不被吞（前端必须把「先修网络」原文显示出来）
5. 模板锚点齐全（`#lr-mon-overview/failures/tasks/recovery`）、nav id 全页唯一
6. 相邻重复行守卫（R113 事故教训：并行会话静默上线的重复行）
7. msgid↔po 一致性 + zh 真实渲染（nav/区块标题/script 内文案都出现中文，防「加了 po 忘编译 .mo」）
8. 轮询节奏：总览 15s、执行进度仍 4s（防有人顺手统一成 4s）
8b. stale/reclaimed 文案随 moon-well 返回值渲染，前端不写死「24h」「3 次」也不自算阈值（防两侧口径漂移）
8c. 恢复方式列对 `AUTO_REQUEUE`/`STALE_EXHAUSTED` 两类**不渲染任何可点按钮**（回收由巡检负责，
    超限由人负责）——断言方式：这两类的行 HTML 里不出现 `data-action="republish"`
9. 区块顺序：总览在手动执行表单之前（防 UI 回退成「盲跑」形态）
10. `tests/` 全量绿（R126 交付基线 364 passed）

交互类缺陷另用浏览器夹具实测（`docs/temp/`，不入库）。

## 7. 并发写风险（本轮开工前必读）

`git status --porcelain cps/ tests/` 当前为空 → 代码面安全；但 `requests.md`、`response.md`、
未跟踪的 `docs/readme/`、`docs/feat/**` 正被 R129 文档会话改动。**占号 130 即刻锁定**，
若真撞号不改既有记录、续编空号并在 `response.md` 冲突记录里说明（AGENTS.md 编号纪律）。

## 8. 文档落位

- L3：本文件 + `ac/admin-monitor-ac.md`（验收时回填逐条结果与截图）
- L1：`docs/readme/admin.md` 在「LLM 任务手动执行」条目后追加一句「队列监控」能力描述（只讲能做什么）
- L2：admin 模块尚无 `docs/admin/hld/hld.md`，按 AGENTS.md 规则先落 L3 并在本文件标注「**待升 L2**」
