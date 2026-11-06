# LLD — R240 核心异步任务体系（仅设计）

> 状态：**设计**（2026-10-28；本轮不实现代码、不建表、不改部署）
> 上层设计：[hld.md](./hld.md) · 验收：[ac/acceptance.md](./ac/acceptance.md)
> 静态规范：[需求](../../../../product/async-task/requirements.md) ·
> [接口](../../../../product/async-task/interface.md) ·
> [运行时](../../../../product/async-task/features/runtime.md) ·
> [准入清单](../../../../product/async-task/features/task-authoring.md)

## 1. 实施目标

建立 `cps/async_task/` 作为 magicbook 唯一允许执行持久异步任务的运行时。首版继续与 Web 同进程，不拆 worker。

本文定义实施时的代码边界、DDL、算法、兼容与测试；不代表已实现。

## 2. 代码布局

建议首版结构：

```text
cps/async_task/
├── __init__.py          # init_runtime(app) / get_runtime()
├── api.py               # submit/get_job/request_cancel/retry_failed
├── models.py            # 四张核心表
├── state.py             # 状态枚举与合法迁移
├── handler.py           # AsyncJobHandler / ItemContext / Outcome
├── registry.py          # (job_type, job_version) 注册与启动校验
├── runtime.py           # runtime 生命周期、wake、drain
├── scheduler.py         # claim、配额、轮询、聚合
├── worker.py            # 固定大小 worker pool
├── lease.py             # 领取、续租、fenced commit
├── recovery.py          # 启动与周期恢复
├── observability.py     # 结构化日志与指标
└── handlers/            # 各业务 adapter；实施时按波次增加
    ├── translation.py
    ├── reading_tts.py
    └── word_detail.py
```

禁止：

- 业务模块直接 import `models.py` 改状态；
- handler 自建线程；
- runtime 直接依赖 Flask request context；
- `cps.web` 与 runtime 形成循环依赖。

## 3. DDL 草案

SQLite 类型仅表达职责，实施时以 SQLAlchemy model 为准。时间统一 UTC。

### 3.1 `async_job`

```text
id TEXT PK
job_type TEXT NOT NULL
job_version INTEGER NOT NULL
owner_user_id INTEGER NULL
idempotency_key TEXT NOT NULL
priority INTEGER NOT NULL DEFAULT 0
state TEXT NOT NULL
payload_json TEXT NOT NULL
payload_hash TEXT NOT NULL
total_count INTEGER NOT NULL DEFAULT 0
succeeded_count INTEGER NOT NULL DEFAULT 0
failed_count INTEGER NOT NULL DEFAULT 0
skipped_count INTEGER NOT NULL DEFAULT 0
running_count INTEGER NOT NULL DEFAULT 0
waiting_count INTEGER NOT NULL DEFAULT 0
cancel_requested_at DATETIME NULL
next_wake_at DATETIME NULL
last_error_code TEXT NULL
last_error_message TEXT NULL
created_at DATETIME NOT NULL
started_at DATETIME NULL
updated_at DATETIME NOT NULL
finished_at DATETIME NULL
version INTEGER NOT NULL DEFAULT 0

UNIQUE(job_type, idempotency_key)
INDEX(state, next_wake_at, priority, created_at)
INDEX(job_type, state)
```

### 3.2 `async_job_item`

```text
id TEXT PK
job_id TEXT NOT NULL FK async_job.id
item_key TEXT NOT NULL
sequence INTEGER NOT NULL
state TEXT NOT NULL
payload_json TEXT NOT NULL
checkpoint_json TEXT NULL
result_json TEXT NULL
external_ref TEXT NULL
attempt_count INTEGER NOT NULL DEFAULT 0
max_attempts INTEGER NOT NULL
next_attempt_at DATETIME NULL
owner_instance_id TEXT NULL
lease_token TEXT NULL
lease_expires_at DATETIME NULL
heartbeat_at DATETIME NULL
error_code TEXT NULL
error_message TEXT NULL
error_retryable INTEGER NULL
created_at DATETIME NOT NULL
started_at DATETIME NULL
updated_at DATETIME NOT NULL
finished_at DATETIME NULL
version INTEGER NOT NULL DEFAULT 0

UNIQUE(job_id, item_key)
INDEX(state, next_attempt_at, lease_expires_at)
INDEX(job_id, state)
INDEX(owner_instance_id, lease_expires_at)
```

### 3.3 `async_job_attempt`

```text
id TEXT PK
job_id TEXT NOT NULL
item_id TEXT NOT NULL
attempt_no INTEGER NOT NULL
instance_id TEXT NOT NULL
lease_token TEXT NOT NULL
outcome TEXT NULL
error_code TEXT NULL
error_message TEXT NULL
external_ref TEXT NULL
metadata_json TEXT NULL
started_at DATETIME NOT NULL
finished_at DATETIME NULL

UNIQUE(item_id, attempt_no)
INDEX(job_id, started_at)
```

### 3.4 `async_runtime_instance`

```text
instance_id TEXT PK
hostname TEXT NOT NULL
pid INTEGER NOT NULL
app_version TEXT NOT NULL
started_at DATETIME NOT NULL
heartbeat_at DATETIME NOT NULL
draining_at DATETIME NULL
stopped_at DATETIME NULL
```

### 3.5 迁移版本

新增 `async_runtime_meta(schema_version INTEGER)` 或项目既有 migration 机制中的等价版本记录。建表与迁移必须幂等；应用重复启动不得重复灌数据。

## 4. Claim 事务

SQLite 单进程下，scheduler 使用一个短暂写事务领取：

```text
BEGIN IMMEDIATE
  SELECT item candidate
    FROM async_job_item i JOIN async_job j
    WHERE i.state IN (...) AND due
      AND i.lease_token IS NULL OR i.lease_expires_at <= now
      AND j.cancel_requested_at IS NULL
      AND quota available
    ORDER BY j.priority DESC, i.next_attempt_at, i.created_at
    LIMIT 1

  UPDATE async_job_item
     SET state='RUNNING',
         owner_instance_id=:instance,
         lease_token=:new_token,
         lease_expires_at=:now+ttl,
         heartbeat_at=:now,
         attempt_count=attempt_count+1,
         version=version+1
   WHERE id=:id
     AND state=:old_state
     AND version=:old_version
     AND (lease_token IS NULL OR lease_expires_at <= :now)

  INSERT async_job_attempt(...)
  UPDATE async_job SET state='RUNNING', ... WHERE id=:job_id
COMMIT
```

实现优先使用 SQLite 单语句 `UPDATE ... WHERE id = (SELECT ...) RETURNING`（运行时 SQLite 版本支持时），否则使用 `BEGIN IMMEDIATE`。无论哪种，必须保证“读取候选”和“拿到租约”之间不存在可被另一线程利用的 TOCTOU。

未来 MySQL/PostgreSQL 实现可改为 `SELECT ... FOR UPDATE SKIP LOCKED`，但 API 和状态语义不变。

## 5. Lease heartbeat 与 fencing

### 5.1 续租 SQL 语义

```text
UPDATE async_job_item
   SET lease_expires_at=:now+ttl, heartbeat_at=:now, version=version+1
 WHERE id IN (:running_item_ids)
   AND owner_instance_id=:instance
   AND lease_token=:token
   AND state='RUNNING'
```

批量续租按 lease token 分组；某 item 影响行数为 0 即失去租约。

### 5.2 Fenced commit

所有终态写回条件：

```text
WHERE id=:item_id
  AND owner_instance_id=:instance
  AND lease_token=:token
  AND state='RUNNING'
```

如果影响 0 行：

- 本次结果丢弃；
- 记录 `async_lease_lost`；
- 不得创建第二次 job、不得把 job 置成功；
- handler 若支持取消，应观察本地失去租约信号并停止后续子步骤。

长 item 的中间 checkpoint 使用同一 fencing 条件，但保持状态为 `RUNNING`：

```text
UPDATE async_job_item
   SET checkpoint_json=:checkpoint,
       heartbeat_at=:now,
       lease_expires_at=:now+ttl,
       version=version+1
 WHERE id=:item_id
   AND owner_instance_id=:instance
   AND lease_token=:token
   AND state='RUNNING'
```

handler 只能通过 `ItemContext.save_checkpoint()` 调用该能力；影响 0 行时抛 `LeaseLost`，不得继续执行可能产生副作用的后续子步骤。checkpoint 的 schema 由 handler 声明并带版本，大小必须有上限，不保存凭据、完整 prompt 或整本书正文。

### 5.3 attempt_started 与最终 outcome

领取事务内插入 attempt 开始行；最终提交时更新同 `(item_id, attempt_no)` 的 `outcome/finished_at`。如果进程崩溃，attempt 行保留为空 outcome，周期 recovery 可标记为 `LEASE_EXPIRED` 或等价审计结果。

## 6. Handler 接口落地

```text
class AsyncJobHandler:
    job_type: str
    job_version: int
    default_max_attempts: int = 5
    default_lease_seconds: int = 45
    quota_key: str = "default"
    job_max_concurrency: int = 1

    def execute(self, ctx): ...
    def poll_external(self, ctx): ...
    def classify_error(self, exc): ...
```

`ItemContext` 除字段与取消检查外，必须提供 `save_checkpoint(checkpoint, progress=None)`；不允许 handler 为写 checkpoint 直接更新核心表。

handler 通过显式 registry 注册，不在 import 时偷偷注册。`init_async_runtime` 在 Flask app 初始化时：

1. 创建表/迁移；
2. 注册内置 handler；
3. 检查未注册的排队 job；
4. 注册 runtime instance；
5. 启动 scheduler、heartbeat、worker pool；
6. 执行一次 recovery。

业务 handler 的数据库写入必须使用 runtime 提供的 scoped session factory 或独立的 session factory；不得复用请求线程的 `ub.session`。

## 7. 状态聚合

job 状态由 item 聚合，不能由 handler 随意写：

- 存在 `RUNNING` → `RUNNING`；
- 无 running，存在 `PENDING` 或已到期 retry/waiting → `QUEUED` 或 `RUNNING`（按是否已开始）；
- 无 running，只有未来 retry/waiting → `RETRY_WAIT`；
- 全部 `SUCCEEDED/SKIPPED` → `SUCCEEDED`；
- 有成功/跳过且有 `FAILED` → `PARTIAL_FAILED`；
- 全部 `FAILED` → `FAILED`；
- 取消请求 → 待运行 item 取消，运行中结束后 `CANCELED`。

计数更新可用“状态变更后重算”保证正确性，初期数据量不必做复杂增量；重算与 item 状态更新在同一事务。

## 8. Retry、backoff 与错误分类

默认：

- 可重试网络/限流/上游 5xx：指数退避；
- 永久业务/参数/权限错误：立即 `FAILED`；
- 毒 item：达到 `max_attempts` 后 `FAILED`；
- 上游返回 `Retry-After`：取该值与本地退避的较大者，并设合理上限；
- 每次退避加 jitter；
- handler 可覆盖单次延迟，但不能取消 job 级最大尝试上限。

建议初始退避序列（秒）：`5, 15, 60, 300, 900`，最终由配置和 handler 决定。

## 9. 取消与人工重试

### 9.1 cancel

1. `request_cancel` 设置 job 的 `cancel_requested_at`；
2. `PENDING/RETRY_WAIT/WAITING_EXTERNAL` → `CANCELED`；
3. `RUNNING` item 不强制杀线程，只通知取消；
4. handler 在安全点返回 `SKIP`/`FAIL_PERMANENT` 或自然完成，fenced commit 后 job 收敛；
5. 已取消 job 的 retry 返回原状态并记日志，不复活。

上游不可撤回的 item 在取消响应中标记 `remote_may_continue=true`，由业务页面显示。

### 9.2 retry_failed

- 只选择当前 `FAILED` item；
- `attempt_count` 保留；
- handler 可声明 `reset_retry_budget=True`，人工重试后获得新的 `max_attempts` 预算；
- 重新置 `PENDING`，设置 `next_attempt_at=now`；
- 插入新的 attempt 行只在真正领取时发生；
- 若 job 是 `CANCELED`，拒绝。

## 10. 启动恢复与周期 recovery

### 10.1 启动

顺序必须在数据库初始化之后、Web 接收流量之前完成注册和 recovery 初始化，但 recovery 扫描可以在后台线程继续。

发现 `RUNNING` 且 lease 过期的 item：

- 记录旧 owner/token；
- attempt 审计标记 `LEASE_EXPIRED`；
- `attempt_count < max_attempts` → `RETRY_WAIT`，`next_attempt_at=now+backoff`；
- 预算耗尽 → `FAILED`；
- 重算 job。

发现 `QUEUED`、到期 `RETRY_WAIT`、到期 `WAITING_EXTERNAL`：交给 scheduler claim。

### 10.2 周期

- 每 5s poll 一次；
- 每 10s heartbeat；
- 每 30s 全量扫描一次过期租约和异常终态；
- 每次扫描必须有界、可重入；
- 多 scheduler 不保证同时只跑一个，但 CAS 保证领取正确。

## 11. 优雅停机与 Compose

### 11.1 代码接入点

- `cps.__init__.create_app()`：`async_runtime.init_app(app)`；
- `WebServer.stop()`：先调用 `async_runtime.shutdown(drain=...)`，再停 Web 服务；
- signal handler 保持单入口，重复 SIGTERM 要幂等；
- `cps.py` 的最终退出路径也要保证 runtime 已停止或租约可由新进程回收。

### 11.2 shutdown 状态机

```text
RUNNING
  └─ SIGTERM → DRAINING
       ├─ 停止 claim
       ├─ 继续 heartbeat
       ├─ 通知 handlers
       ├─ drain 超时
       └─ STOPPED
```

### 11.3 Compose

实施时在 `magicbook` service 增加：

```yaml
stop_grace_period: 40s
```

应用 drain 默认 25s，留 15s 给进程退出、数据库 flush 和 Docker 清理。必须用 SIGTERM 真机测试，不能只看 Dockerfile。

## 12. 身份与 moon-well 调用

当前 R238 预览/翻译恢复展示三种身份来源：

- 请求线程 user token；
- 内部 system identity；
- bearer token 闭包。

核心 runtime 的规则：

- 任务只保存 `owner_user_id` 和计费归属；
- handler 通过 runtime 的服务凭据提供器获取后台身份；
- 不得把用户 token 保存到数据库或日志；
- 若某个上游操作必须依赖用户临时授权，handler 必须返回可重试的 `AUTH_REQUIRED`，并让用户在界面重新授权后再触发；
- 批量任务的完成回写和计费归属必须能在无用户在线时继续。

这一条在实施前需要逐项核对 moon-well 现有服务身份/计费接口；本轮不修改 moon-well，只把它作为 D2–D5 的接入门禁。

## 13. 存量任务迁移

### 13.1 通用映射

| 现字段/概念 | 核心字段 |
| --- | --- |
| job table `status` | `async_job.state`，按映射表转换 |
| job/item `created_at/updated_at` | 同名保留 |
| item `text_hash/batch_seq/text` | `item_key` + `payload_json` |
| item `attempt_count` | `attempt_count` |
| item `error_message` | `error_code` + `error_message` |
| `updated_at` 30 分钟僵尸 | 不再使用；活动任务迁移为租约或 `RETRY_WAIT` |
| `_live_workers` | 不迁移；进程内状态没有持久价值 |
| `task_id` / 外部 ref | `external_ref` |

### 13.2 分链路

#### R238 预览

- 迁移最简单，快照可重建；
- `book_fingerprint` 作为 job 指纹；
- `EXTRACTING/CHECKING` 拆成 item 或 checkpoint；
- 页面读取核心 job 状态；旧 `reading_word_detail_preview` 只读清理。

#### 整本朗读

- job = 一本书一个批次；
- item = 去重段落；
- `item_key = text_hash`；
- execute 调 `/tts/speak`；
- 成功以缓存写入/HTTP 2xx 为准；
- 现有缓存自然幂等，但必须把 voice/style 纳入幂等条件，避免不同音色误命中。

#### 全文单词详解批次

- job = 一本书补缺；
- item = 200 词批；
- `item_key` 由排序后的词表 hash 生成；
- `publish` 成功后可用 `WAITING_EXTERNAL` 或直接 `SUCCEEDED`，取决于 moon-well 是否同步受理；
- 覆盖率回收是 job 级 reconcile，需在 LLD 另行定义。

#### 整本翻译

- job = 一本书翻译批次；
- item = 去重段落；
- `item_key = text_hash`；
- publish 成功写 `external_ref=taskId`，进 `WAITING_EXTERNAL`；
- 轮询 `find-translations` 后提交结果；
- 需要处理“已发布但上游无 taskId”和“缓存已存在”两种收敛。

#### Book-finished bridge

- 作为后续波次迁移；
- 若它依赖用户 token，必须先建立服务身份或明确“用户重新登录触发”；
- 若无法保证后台恢复，应改为可观察的持久 job，而不是 daemon。

### 13.3 切换规则

- 每一波先加只读影子读取/对账，再切写；
- 活动 job 若不能无损导入，必须在无活动批次时部署；
- 旧表保留至少一个观察窗口；
- 旧 job service 的 `_spawn_*` 与 recovery 入口在切换后禁止被调用；
- 前端保持原端点名，或提供兼容代理，不能要求用户换 URL。

## 14. 配置

建议环境变量：

```text
ASYNC_RUNTIME_ENABLED=1
ASYNC_WORKER_COUNT=4
ASYNC_LEASE_SECONDS=45
ASYNC_HEARTBEAT_SECONDS=10
ASYNC_POLL_SECONDS=5
ASYNC_SHUTDOWN_DRAIN_SECONDS=25
ASYNC_RETRY_MAX_DEFAULT=5
ASYNC_JOB_RETENTION_DAYS=90
ASYNC_ATTEMPT_RETENTION_DAYS=30
```

数值必须在启动时校验：heartbeat < lease、drain < Compose grace、所有并发 > 0。

## 15. 观测与运维

至少提供：

- `/ajax/admin/async-jobs`（可选，管理员只读）：按类型/状态统计、最老 job、失败样本；
- CLI/诊断函数：按 job/item/attempt 查询；
- 日志字段与 `runtime.md` §11 一致；
- 定时清理终态 job/attempt，依据保留期配置，不清理仍可重试或审计未完成的记录。

## 16. 测试计划

### 16.1 单元测试

- 状态迁移合法/非法；
- idempotency key 去重；
- backoff、jitter、Retry-After；
- quota 计算；
- 聚合法 job 状态；
- fencing SQL 0 行分支；
- 中间 checkpoint 成功提交、失租拒绝和恢复后从最近安全点继续；
- 取消与 retry 边界；
- 敏感字段拒绝写入日志/状态。

### 16.2 集成测试

- SQLite 两个线程同时 claim 同一 item；
- 两个 runtime instance（测试库）竞争；
- heartbeat 丢失 → 租约过期 → 重新领取；
- 旧 token 写回失败；
- worker 进程被模拟终止后启动 recovery；
- 长 handler 在 drain 超时下的收敛；
- external `WAITING_EXTERNAL` 轮询；
- 毒 item 与部分失败聚合；
- 业务端点响应与旧契约一致。

### 16.3 真机/故障注入

- 部署一次时在整本朗读中途发 SIGTERM，观察新进程继续；
- 执行中 kill -9，验证租约回收；
- 外部成功后模拟本地 commit 失败，验证幂等；
- 检查 Compose grace 与 runtime drain 的实测时间。

## 17. 分批实施任务拆分

| 任务 | 依赖 | 产物 |
| --- | --- | --- |
| D1-A 表与迁移 | 无 | models/migration/schema map |
| D1-B runtime 骨架 | D1-A | claim/lease/heartbeat/recovery |
| D1-C worker/registry | D1-B | 有界池、handler SPI |
| D1-D shutdown | D1-C | SIGTERM/drain/Compose |
| D1-E 核心测试夹具 | D1-B/C | 故障注入与多线程 claim |
| D2 R238 迁移 | D1 | 现有 preview 行为兼容 |
| D3 TTS 迁移 | D1 | 现有 TTS API 兼容 |
| D4 word-detail 迁移 | D1/D3 | 覆盖率与重试兼容 |
| D5 translation 迁移 | D1 | external waiting/回收兼容 |
| D6 旧实现收敛 | D2–D5 | 禁用旧 daemon/恢复 |

## 18. 本轮不实施

- 不提交代码；
- 不新增表；
- 不修改 `cps/async_task/`（目录尚不存在）；
- 不修改 `docker-compose.yml`；
- 不迁移现有 job；
- 不修改 moon-well；
- 不将 MB-231 状态推进到 Planned/In progress；待用户确认设计后再进入开发。
