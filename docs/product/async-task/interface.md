# async-task · L2 内部接口与状态契约

> 状态：**目标态，R240 设计已落，尚未实现**（2026-10-28）。
> 读者：业务模块 producer、异步 handler 作者、任务状态查询页面作者。
> 运行时实现边界见 [`features/runtime.md`](./features/runtime.md)；新任务准入见
> [`features/task-authoring.md`](./features/task-authoring.md)。

## 1. 能力边界

核心模块提供四类能力：

1. **submit**：业务模块在一个数据库事务内创建 job 与 item；
2. **execute**：核心运行时按租约领取 item，调用已注册 handler；
3. **recover**：回收过期租约、重排可重试 item、修复 job 汇总状态；
4. **observe/control**：查询进度、请求取消、重试失败 item。

业务模块仍拥有领域 API、页面和业务结果结构；核心模块只拥有任务生命周期、调度、租约与一致性。

## 2. 状态机

### 2.1 job 状态

| 状态 | 含义 | 是否终态 |
| --- | --- | --- |
| `PREPARING` | producer 正在生成 item；尚不可执行 | 否 |
| `QUEUED` | item 已齐备，等待 worker | 否 |
| `RUNNING` | 至少一个 item 正被租约执行 | 否 |
| `RETRY_WAIT` | 当前没有运行中 item，但仍有 item 等待退避重试或外部轮询 | 否 |
| `SUCCEEDED` | 全部有效 item 成功或按规则跳过 | 是 |
| `PARTIAL_FAILED` | 有成功结果，也有永久失败 item | 是 |
| `FAILED` | 没有任何成功结果，且任务无法继续 | 是 |
| `CANCELED` | 用户/系统明确取消 | 是 |

`PREPARING` 为未来动态生成 item 预留；首版要求 producer 在同一事务内提交完整 item 集合，直接从 `QUEUED` 开始。handler 不得依赖一个尚未定义“追加/封口”协议的 `PREPARING` job。

### 2.2 item 状态

| 状态 | 含义 | 是否可领取 |
| --- | --- | --- |
| `PENDING` | 首次执行或人工重新排队 | 是 |
| `RUNNING` | 已被某个 worker 租约持有 | 否，租约过期后回收 |
| `WAITING_EXTERNAL` | 已交给外部系统，等待轮询/对账 | `next_attempt_at` 到期后可领取 |
| `RETRY_WAIT` | 可重试失败，等待退避 | `next_attempt_at` 到期后可领取 |
| `SUCCEEDED` | 业务结果已提交 | 否 |
| `FAILED` | 永久失败或达到最大尝试次数 | 否 |
| `SKIPPED` | 因去重、已缓存或业务规则无需执行 | 否 |
| `CANCELED` | 已取消 | 否 |

状态字符串一旦上线不得随意改名；需要扩展时只追加新值，并通过 schema/version 兼容旧值。

## 3. Producer API

目标代码入口：`cps.async_task.api`（实施阶段创建）。

### 3.1 提交任务

```text
submit(
  job_type: str,
  job_version: int,
  idempotency_key: str,
  payload: dict,
  items: list[ItemInput],
  owner_user_id: int | None,
  priority: int = 0,
) -> JobRef
```

约束：

- `job_type` 必须在启动时注册过 handler。
- `idempotency_key` 在 `(job_type, idempotency_key)` 维度唯一；重复提交返回原 job，不新建。
- `idempotency_key` 表示一次逻辑提交的去重身份，不是业务内容身份。同 key 且 payload hash 相同返回原 job；同 key 但 payload 不同必须冲突报错。用户明确发起新一次运行时，由 producer 生成新的提交 key；同一 HTTP 请求的网络重试必须复用原 key。
- job 与首批 item 必须在同一事务提交；事务回滚时不得留下内存任务。
- `items[].item_key` 在 job 内唯一，必须是稳定内容键，不能使用随机数或当前时间。
- payload 中禁止出现用户 token、API Key、完整 prompt、书籍正文等敏感内容。
- 提交成功后只允许调用 `wake()` 做低延迟提示；不调用 `wake()` 也必须由轮询兜底执行。

### 3.2 查询、取消、重试

```text
get_job(job_id, owner_user_id: int | None) -> JobStatus
request_cancel(job_id, actor: Actor) -> JobStatus
retry_failed(job_id, actor: Actor, item_ids: list[str] | None = None) -> JobStatus
```

- `get_job` 必须在业务层做 owner/admin 权限校验；核心接口不信任调用方传入的任意 owner。
- `request_cancel` 幂等；已终态 job 返回当前状态。
- `retry_failed` 只处理 `FAILED` item；不得改变 `CANCELED` job。
- 手工重试是否重置 `attempt_count` 必须由 handler 显式声明；默认保留历史尝试审计，只重置当前重试预算。

## 4. Handler SPI

目标接口：`cps.async_task.handler.AsyncJobHandler`。

```text
job_type: str
job_version: int
default_max_attempts: int
default_lease_seconds: int
quota_key: str

execute(ctx: ItemContext) -> Outcome
poll_external(ctx: ItemContext) -> Outcome
classify_error(exc: Exception) -> ErrorClass
```

### 4.1 ItemContext

至少包含：

- `job_id`、`item_id`、`item_key`、`attempt_no`；
- `job_type`、`job_version`；
- `owner_user_id`；
- 反序列化后的 job/item payload 与当前 checkpoint；
- 租约令牌只用于运行时内部 fencing，不暴露给上游；
- `cancellation_requested()` 与安全点检查能力；
- `save_checkpoint(checkpoint, progress=None)`：在当前租约仍有效时原子提交中间断点；失败必须抛出 `LeaseLost`，handler 随即停止后续子步骤；
- 受控的服务身份/凭据引用解析入口，不直接提供用户原始 token。

`save_checkpoint()` 只更新当前 item 的 `checkpoint_json`、受控进度与心跳元数据，不改变 item 终态，也不能绕过 producer/handler 权限边界。checkpoint 必须有大小上限，不保存凭据、完整 prompt 或整本书正文。

### 4.2 Outcome

| 结果 | 运行时动作 |
| --- | --- |
| `SUCCESS(result, external_ref=None)` | item → `SUCCEEDED`，提交结果与进度 |
| `SKIP(reason)` | item → `SKIPPED`，记录原因 |
| `RETRY(delay, error_code, message, retryable=True)` | item → `RETRY_WAIT`，设置 `next_attempt_at` |
| `WAIT_EXTERNAL(external_ref, next_poll_at, result=None)` | item → `WAITING_EXTERNAL`，到期调用 `poll_external` |
| `FAIL_PERMANENT(error_code, message)` | item → `FAILED` |

handler 不得直接修改 job 汇总字段、租约字段或其他 item 的运行时状态。领域副作用与 item 结果提交应尽量在同一业务事务内完成；无法合并时，必须按幂等要求处理。

### 4.3 错误分类

稳定错误分类至少包括：

- `INVALID_INPUT`：永久失败；
- `AUTH` / `FORBIDDEN`：默认永久失败，除非凭据可自动刷新；
- `RATE_LIMIT`：可重试，优先尊重上游 `Retry-After`；
- `TIMEOUT` / `NETWORK`：可重试，但必须依赖幂等键；
- `UPSTREAM_UNAVAILABLE`：可重试；
- `UPSTREAM_BUSINESS_ERROR`：由 handler 明确映射可重试或永久；
- `LOCAL_TRANSIENT`：数据库锁、磁盘短时故障等可重试；
- `POISON`：同一输入重复导致确定性异常，达到上限后永久失败。

禁止把所有异常一律吞掉并写日志；也禁止对所有异常无限重试。

## 5. JobStatus 返回契约

核心状态 DTO 至少包含：

```json
{
  "jobId": "…",
  "jobType": "…",
  "jobVersion": 1,
  "state": "RUNNING",
  "progress": {
    "total": 100,
    "succeeded": 40,
    "failed": 2,
    "skipped": 3,
    "running": 1,
    "waiting": 54
  },
  "cancelRequested": false,
  "nextWakeAt": "2026-10-28T12:00:00Z",
  "failure": null,
  "createdAt": "…",
  "startedAt": "…",
  "finishedAt": null
}
```

业务端点可以在 `result`/`domain` 中追加自己的领域快照，但不得改变核心状态字段语义。

## 6. 运行时保证

核心运行时承诺：

1. 同一租约内的 item 不会被两个有效 owner 同时执行；
2. 失去租约的 worker 无法提交成功结果；
3. 进程重启后，数据库中的可执行 item 会被恢复扫描发现；
4. handler 成功提交的中间 checkpoint 受 owner + lease token fencing 保护；
5. 每个终态 item 至少有一条 attempt 审计；
6. 取消后不再领取新 item；
7. 队列等待不依赖进程内存存活；
8. 超时或崩溃后的恢复时间有明确上界。

核心运行时不承诺：

1. 外部副作用天然 exactly-once；这由稳定幂等键和上游能力共同保证；
2. 上游不支持取消时能撤回已受理任务；
3. 任意 handler 代码崩溃后仍能保留其进程内临时变量；
4. 多进程部署下 SQLite 的高并发写吞吐。

## 7. 对外 HTTP 契约

核心模块不强制提供通用业务 HTTP API。各业务模块继续维护自己的端点，例如整本翻译的 start/status/cancel/retry。

如新增通用管理接口，只允许暴露：

- 脱敏后的 job/item/attempt 状态；
- 取消和重试操作；
- 聚合队列指标。

不得在没有权限校验的情况下暴露其他用户的 job，也不得返回 payload 中的敏感字段。

## 8. 版本与兼容

- `job_type` 表达业务类型，`job_version` 表达 payload 与 handler 语义版本。
- 旧版本 job 必须由旧 handler 或显式 migration 继续处理；不能静默交给不兼容的新 handler。
- 新增可选字段时先写默认值；删除或改义字段必须先完成数据迁移和旧 job 清退。
- handler 版本升级不得改变已完成 item 的业务解释。
