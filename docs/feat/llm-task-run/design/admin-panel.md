# LLM 任务手动执行面板（R126 · US3 admin-panel）

> L3 详细设计。需求原文见 `requests.md` R126；对端设计见
> `moon-well/docs/feat/llm/design/llm-task-manual-run.md`（R110 US1/US2/US3）。
> 本模块只做 magicbook 侧的管理员入口与转发，不含任何队列语义。

## 1. 目标与边界

给管理员一个「看完队列再决定这一批怎么跑」的入口：选 provider / model / 并发 / 本批上限，
手动消费 moon-well 的 `system_llm_task_record` 队列，能查进度、能停止。

边界（刻意不做）：

| 不做 | 原因 |
| --- | --- |
| 队列/状态机逻辑 | 全部在 moon-well（认领 CAS、限流退避、重放门禁都在服务端） |
| 请求体字段映射层 | 前端直接按 moon-well DTO 命名提交；多一层 snake_case 映射会让两侧契约漂移无人发现 |
| 并发/上限的前端强校验 | 权威夹取在 `LlmTaskManualRunProperties.resolveConcurrency/resolveMaxTasks`，前端只负责把上限显示出来 |
| 自动执行模式的开关 | `ai.llm.task-auto-execute.enabled` 与手跑互斥，moon-well 侧已直接拒绝，不在面板重复暴露 |

## 2. 接口清单

`cps/web.py` 新增 5 个视图 + 1 个 `_llm_task_admin_gate()` 辅助：页面路由用
`@user_login_required + @admin_required`；4 个 JSON 端点用 `@user_login_required` +
handler 内 `current_user.role_admin()` 返回 **JSON 403**（`abort(403)` 给的是 HTML，
前端 fetch 只能显示「HTTP 403」，管理员看不到可处置信息；成例见 `/ajax/credit/admin-adjust`）：

| magicbook 路由 | 方法 | 转发到 moon-well | 超时 | 请求体 |
| --- | --- | --- | --- | --- |
| `/llm-tasks` | GET | —（渲染模板） | — | — |
| `/ajax/llm-task/options` | POST | `/llm/task/run/options` | 15s | `{}` |
| `/ajax/llm-task/run` | POST | `/llm/task/run` | 15s | 表单原样透传 |
| `/ajax/llm-task/status` | POST | `/llm/task/run/status` | 10s | `{runId}` |
| `/ajax/llm-task/stop` | POST | `/llm/task/run/stop` | 15s | `{runId}` |

Why 走 `_moonwell_proxy` 而不是加进 `resource.ignoring.internalUri` 的内网互信通道：手跑会真实
消耗模型配额并把成千上万行改成 RUNNING，必须带管理员本人的 `moonwell_access_token`，
moon-well 才能按 `ai.llm.task-manual-run.admin-user-ids` 白名单归因与拒绝。

字段契约（与 `LlmTaskRunReqDTO` 逐字对齐）：
`provider` `model` `concurrency` `maxTasks` `caller` `taskType` `replayFailed`；
响应信封 `{success, message, code, result, timestamp}`，前端 `unwrap` 只认 `success`/`result`/`message`。

## 3. 页面结构（`cps/templates/llm_tasks.html`）

- 顶部一行队列概览：待处理 / 可重放失败 / 服务端上限 / 正在执行的 runId（来自 options）
- 开始按钮**初始禁用**，只在 options 成功返回且 `enabled && admin` 后解禁；未配置供应商在
  下拉里标注且 `<option disabled>`；切 provider 会清空模型名（跨网关模型名不通用），且
  并发/上限只覆盖「管理员没改过」的输入框（`touched` 脏标记）——否则填的 100 会被
  `maxTasksPerRun=5000` 静默冲掉；
- 表单：provider 下拉、model 输入框（datalist 取该 provider 的两档配置，允许手填任意名）、
  caller 下拉（含「全队列」空值）、并发数、本批上限、重放失败勾选
- 按钮：开始执行（confirm 二次确认）/ 刷新 / 停止（仅 run 活跃时可用）
- 进度表：已认领 / 成功 / 失败或超时 / 仍在执行 / 队列剩余 / 状态；活跃期 4s 轮询一次

Why 数字来自服务端而不是前端计数：runId 写在 `accepted_by` 上，进度是 moon-well 按任务表
`group by status` 出来的，进程重启或页面刷新后仍然可信。

Why 模型候选不取供应商 `/models`：2026-10-07 实测智谱 Coding 端点清单只有 11 项且不含实际可调通的
免费档模型，照清单做下拉会挡掉可用模型（详见 moon-well 设计 §2）。

## 4. i18n

42 条英文 msgid 进 `zh_Hans_CN/LC_MESSAGES/messages.po` 并**重新编译 `messages.mo`**
（成例对齐 R124 单词详解）。模板 `<script>` 内的字符串一律由 Jinja 渲染——本项目 JS 侧没有
`_()` 实现，裸写会 ReferenceError；`tests/test_llm_task_run_r126.py` 同时锁住两件事：
po 词条齐全 + 真实渲染成 zh 后页面/下拉框出现中文（防「加了 po 忘了编译 .mo」）。

## 5. 上线前置条件（顺序敏感）

1. moon-well 发版（US1+US2 的代码），否则 4 个 `/llm/task/run*` 全 404，面板加载 options 报错。
2. Nacos `moon-well-ai.yaml` 加 `ai.llm.task-manual-run` 块，其中 `admin-user-ids` 必须包含
   **magicbook 管理员在 moon-well 侧映射到的 userId**（OIDC 换票得到的账户，不一定是 1）。
   对不齐的症状：点了「开始执行」返回「无权限手动执行 LLM 任务」。
3. 数据库索引：`docs/feat/llm/sql/` 无本仓脚本，索引在 moon-well 侧（`idx_accepted_by`）；
   依赖 `ddl-auto=update` 或手工执行 moon-well 仓库那条 SQL。
4. magicbook 侧无新增环境变量、无新增 `.env` 键（复用既有 `MOON_WELL_READING_URL`）。

## 6. 测试

`tests/test_llm_task_run_r126.py` 28 条（含跨仓库 DTO 契约 2 条、Start 按钮门禁 1 条）：4 条转发路径、请求体逐字节透传、空 body 不崩、
非管理员 5 个入口全 403、上游 403 的 `message` 不被吞、admin 页面锚点齐全、
nav 入口仅 admin 可见且 id 全页唯一、zh 真实渲染（nav + 页面 + script 内文案）、
模板相邻重复行守卫、msgid↔po 一致性、模板 url_for 指向的视图函数存在。

全量：`pytest tests/` → **364 passed**。交互类缺陷另经浏览器夹具实测（见
`ac/admin-panel-ac.md` §2b/§2c）。
