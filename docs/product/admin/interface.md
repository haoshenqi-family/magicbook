# admin · L2 接口说明

> 管理面端点的功能定义、调用方法与上游映射。首发于 R130（队列监控）；此前 R126 的
> 四个手动执行端点一直未落 L2，本册一并收录。上游契约权威 = moon-well 代码（R110/R118）。
> R250 管理员运营站内信后台的本仓页面与代理也已登记；运营邮件事实与批次审计权威 = moon-well R230。

## 能力边界

管理面板的薄代理层：本仓不落库、不做字段改写，请求体原样透传（两侧 DTO 命名直接对齐）；页面 `/llm-tasks` 与 `/admin/mail` 均为 `@admin_required`。LLM 任务 JSON 端点走 `_llm_task_admin_gate()`，运营发信 JSON 端点走 `_admin_json_gate()`，非管理员均返回 JSON 403。真正的白名单二检在 moon-well：LLM 任务用 `ai.llm.task-manual-run.admin-user-ids`，运营发信用 `credit.admin-user-ids`。

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

### 管理员运营站内信（R250 → moon-well R230）

| magicbook 端点 | 上游 | 超时 | 说明 |
| --- | --- | --- | --- |
| `GET /admin/mail` | — | — | 管理员运营发信页面，Flask endpoint `web.admin_mail_page` |
| `GET /ajax/admin-mail/users` | `POST /mail/admin/users` | 10s | `keyword` 最长 80 字，`limit` 默认 100、上限 500 |
| `GET /ajax/admin-mail/audience-count` | `POST /mail/admin/audience/count` | 10s | 无 payload；返回全体用户人数整数 |
| `POST /ajax/admin-mail/send` | `POST /mail/admin/send` | 30s | 只透传 `audienceType/userIds/title/body/actionPath`；`ALL` 不带 userIds；去重后 >5000 本地 400 |
| `GET /ajax/admin-mail/campaigns` | `POST /mail/admin/campaigns/page` | 10s | `pageNo` 默认 1、上限 100000；`pageSize` 默认 20、上限 50 |
| `POST /ajax/admin-mail/recall` | `POST /mail/admin/recall` | 10s | 只接受正整数 `campaignId`；不接收 operator |

运营发信代理与 LLM 任务代理一样保持 `_moonwell_proxy` 三元组；本地参数非法是 400 的额外分支。用户侧渲染契约见 `docs/product/companion/interface.md`，实现边界见 `docs/product/companion/features/admin-mail.md`。

## 调用方契约

- 响应统一 `Result{success, result, message}`（moon-well 包装）；业务失败（非白名单、BLOCKED 等）的 `message` 原样透出到页面，不吞换泛用文案。
- 前端渲染口径：失败桶 `recovery ∈ {AUTO_REQUEUE, FORBIDDEN}` 只读（徽标、无重发按钮）；`etaHours` 不可信不展示。
- 跨仓字段漂移由 `tests/test_llm_task_admin_monitor_r130.py::TestCrossRepoContract` 钉住（前端读取字段 ⊆ moon-well DTO、分类/状态下拉 ⊆ 枚举）。

## L3 与历史设计

- R126：`docs/project/_legacy/feat/llm-task-run/design/admin-panel.md`
- R130：`docs/project/iterations/1.0/r130-llm-queue-monitor/`（HLD/LLD/AC）
