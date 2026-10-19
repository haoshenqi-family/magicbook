# admin · L2 接口说明

> 管理面端点的功能定义、调用方法与上游映射。首发于 R130（队列监控）；此前 R126 的
> 四个手动执行端点一直未落 L2，本册一并收录。上游契约权威 = moon-well 代码（R110/R118）。

## 能力边界

管理面板的薄代理层：本仓不落库、不做字段改写，请求体原样透传（两侧 DTO 命名直接对齐）；页面 `/llm-tasks`（`@admin_required`），全部 JSON 端点走 `_llm_task_admin_gate()`（JSON 403）。真正的白名单二检在 moon-well（Nacos `ai.llm.task-manual-run.admin-user-ids`，与手动执行同一名单）。

## 端点映射

### 手动执行（R126 → moon-well R110）

| magicbook 端点 | 上游 | 超时 |
| --- | --- | --- |
| `POST /ajax/llm-task/options` | `/llm/task/run/options` | 15s |
| `POST /ajax/llm-task/run` | `/llm/task/run` | 15s |
| `POST /ajax/llm-task/status` | `/llm/task/run/status` | 10s |
| `POST /ajax/llm-task/stop` | `/llm/task/run/stop` | 15s |

### 队列监控（R130 → moon-well R118）

| magicbook 端点 | 上游 | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/llm-task/admin-overview` | `/llm/task/admin/overview` | 10s | 无入参；15s 轮询、页面不可见时暂停 |
| `POST /ajax/llm-task/admin-failures` | `/llm/task/admin/failures` | 15s | `{caller?, sinceHours?}`（默认 24h、上限 168h） |
| `POST /ajax/llm-task/admin-page` | `/llm/task/admin/page` | 10s | keyword 必须搭配 caller/status/errorCode/userId 之一（上游强制防 LOB 全表扫，前端提前拦） |
| `POST /ajax/llm-task/detail` | `/llm/task/detail` | 10s | `{taskId}`；上游归属校验对管理员放行 |
| `POST /ajax/llm-task/admin-recovery-plan` | `/llm/task/admin/recovery-plan` | 20s | confirm 恒由前端不发（只读预案零写库） |
| `POST /ajax/llm-task/admin-republish-failed` | `/llm/task/admin/republish-failed` | 30s | 唯一写路径；前端二次确认后才带 `confirm:true`，代理原样透传不剥离 |

## 调用方契约

- 响应统一 `Result{success, result, message}`（moon-well 包装）；业务失败（非白名单、BLOCKED 等）的 `message` 原样透出到页面，不吞换泛用文案。
- 前端渲染口径：失败桶 `recovery ∈ {AUTO_REQUEUE, FORBIDDEN}` 只读（徽标、无重发按钮）；`etaHours` 不可信不展示。
- 跨仓字段漂移由 `tests/test_llm_task_admin_monitor_r130.py::TestCrossRepoContract` 钉住（前端读取字段 ⊆ moon-well DTO、分类/状态下拉 ⊆ 枚举）。

## L3 与历史设计

- R126：`docs/project/_legacy/feat/llm-task-run/design/admin-panel.md`
- R130：`docs/project/iterations/1.0/r130-llm-queue-monitor/`（HLD/LLD/AC）
