# HLD — R130 LLM 队列监控面板（四区块）

> 状态：设计（草案 v1，2026-10-18，待用户第二轮讨论）
> 关联：Ship [MAGICBOOK-143 / idea i7iJ3gwo](https://haoshenqi.pingcode.com/ship/ideas/i7iJ3gwo) · PJM 工作项 MAGICBOOK-4 · 同源 moon-well R118（后端已交付上线）· 扩展本仓 R126 `/llm-tasks` 面板。
> 前稿：`docs/project/_legacy/feat/llm-task-run/design/admin-monitor.md`（R130 US4 设计稿，行号已漂移，本文为其修订版）。

## 1. 目标与范围

给管理员在 magicbook `/llm-tasks` 页补齐**队列可视化与恢复能力**四区块：

1. **队列总览**：pending/accepted/running/completed/failed 计数（按 caller 分组 + 全局）、最老 pending 年龄、近 24h 吞吐、stale 预警（ACCEPTED 超时自动回收回显）。
2. **失败原因分类**：按 `LlmTaskFailureCategory` 十类分桶（含恢复方式 recovery 与 unknown 占比），支持 caller + 时间窗过滤。
3. **任务查询与详情**：按 caller/status/errorCode/userId/taskType/keyword/时间区间分页查询（50/页），行点开看详情（params/prompt/output 全文、token 与延迟）。
4. **一键恢复**：先 dry-run 生成恢复预案（PLAN），二次确认后执行重发失败（republish-failed，`confirm=true` 才写库）。

**不在范围**：R126 已有的手动执行（run/options/status/stop）不动；不新建数据库表（moon-well 侧已就绪）。

## 2. 现状与依赖

- 后端**全部就绪**（moon-well R118，已上线）：`/llm/task/admin/overview|failures|page|recovery-plan|republish-failed` 五端点 + `/llm/task/detail`（管理员放行），DTO 见 LLD §2。管理员白名单 = Nacos `ai.llm.task-manual-run.admin-user-ids`（`LlmTaskAdminGuard`，与 R110 手动执行同一名单）。
- 前端基线：R126 `/llm-tasks`（`cps/routes/vocab.py:95-146` 页面 + 4 个 run 代理；`cps/web.py` `_LLM_TASK_PATHS`/`_llm_task_admin_gate`/`_moonwell_proxy`）。本需求**纯增量**。

## 3. 方案选型

**采用：magicbook 薄代理 + 前端四区块**（与 R126 同构：代理原样透传 body，两侧 DTO 字段名直接对齐）。

否决方案：

| 否决 | 理由 |
| --- | --- |
| 前端直连 moon-well | 管理员 JWT 与内网地址暴露到浏览器；CORS/混合内容；违背「/ajax/* 用户代理统一鉴权归因」形制 |
| 在 moon-well 侧建管理 UI | moon-well 无前端载体；magicbook 是既定用户入口，R126 面板已在此 |

## 4. 模块/仓间分工

- **moon-well**：零改动（R118 已交付；其 L2 `docs/product/system/interface.md` 未收录 admin 端点——已登记为其文档欠账，不在本条修）。
- **magicbook**：代理 6 端点（LLD §1）+ `/llm-tasks` 页四区块 + i18n + 测试。

## 5. 契约要点（权威源 = moon-well 代码 DTO）

- 全部 POST + `Result` 包装；二进制无；鉴权 = 用户 JWT（管理员白名单二检）。
- `failures`：`{caller?, sinceHours?≤168 默认24}` → buckets（category/recovery/count/first/last/sampleTaskId/sampleMessage 截80字/perHour）。
- `page`：`keyword` **必须**与 caller/status/errorCode/userId 之一同用（服务端强制，防 LOB 全表扫）——前端要把这条约束显式化。
- 恢复枚举内嵌 category：`AUTO_REQUEUE`/`FORBIDDEN` 桶**不渲染重发按钮**；`REPLAY`/`REPUBLISH` 可重发；`MANUAL` 只提示。
- `republish-failed` 不可逆消耗模型配额：dry-run（confirm 缺省）→ 展示预案 → 用户点确认（二次确认弹窗带条数与 caller）→ `confirm:true`。
- `overview.etaHours` 当前不可信恒 null → 前端不展示或显示「—」。

## 6. 风险与回滚

| 风险 | 缓解 |
| --- | --- |
| 重发误操作烧配额 | dry-run 默认；二次确认文案含 plannedLimit/totalFailed；FROBIDDEN 类不可发 |
| 轮询打爆上游 | 总览 15s 一档、失败面板手动刷新；页面不可见时暂停（document.visibilitychange） |
| 回滚 | 前端/代理纯增量，revert 单 commit 即回滚；无数据结构变更 |

## 7. 开放问题（第二轮讨论）

1. 失败分类十桶的中文文案口径（建议沿用 moon-well 枚举名直译 + 恢复方式注记）。
2. 总览是否并入 R126 顶部（一屏四区块）还是 Tab 分页（建议：单页纵向四区块，管理页不强求一屏）。
3. 任务详情 modal 的 prompt/output 全文是否需要折叠/截断开关（默认 2KB 截断 + 展开）。
