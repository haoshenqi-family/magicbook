# async-task 运行时架构（L3）

> 状态：**目标态，R240 设计已落，尚未实现**（2026-10-28）。
> 读者：实现、迁移、运维和评审异步任务核心模块的人。
> 需求：[`../requirements.md`](../requirements.md)；接口：[`../interface.md`](../interface.md)；
> 新任务准入：[`task-authoring.md`](./task-authoring.md)。

## 1. 结论

magicbook 继续采用**单 Web 进程 + 进程内核心运行时**，不在本轮拆分 worker。

可靠性不来自“线程一直在跑”，而来自：

1. 数据库保存 job/item/attempt 与断点；
2. 数据库 CAS 租约决定谁有权执行；
3. 心跳与租约过期决定失联任务何时回收；
4. fencing token 阻止旧 worker 覆盖新 worker；
5. 稳定幂等键阻止恢复重试造成重复副作用；
6. 优雅停机缩小部署窗口，启动恢复兜住剩余情况。

拆分 Web/Worker 只能改善发布隔离和资源隔离；如果缺少上述机制，拆开后 worker 重启依然会让任务失败。若 Web 与 Worker 仍由同一条 `docker compose up -d` 一起重启，拆分本身也不会改善部署抖动。

## 2. 当前实现与目标差距

| 当前实现 | 问题 | 目标 |
| --- | --- | --- |
| `JobServiceBase` 用 `_live_workers` 进程内集合判活 | 重启即丢，不能作为持久事实 | 数据库租约与 instance heartbeat |
| 每 job 创建 daemon 线程 | 并发无全局上限，停机不可控 | 有界 worker 池 + 调度器 |
| `updated_at` 30 分钟判僵尸 | 恢复慢，且无法证明线程是否存在 | `lease_expires_at` + 心跳 |
| 翻译有启动恢复，TTS/详解依赖点击或轮询 | 恢复行为分裂 | 统一 recovery scanner |
| 各 service 自建 item 状态机和计费语义 | 新任务反复复制坑 | 核心状态机 + handler adapter |
| `SIGTERM` 只停 Web/调度器 | worker 不 drain、不释放租约 | draining 状态、安全点、grace period |
| 用户 token 由请求线程闭包传入后台 | 重启后无法自动恢复 | 服务身份 + owner 计费归属，不落原始 token |

现有 `docs/project/iterations/1.0/r238-word-detail-preview/lld.md` 已明确“多进程部署需另加 DB 租约”；R240 将 DB 租约提升为单进程也必须具备的能力。

## 3. 组件

目标代码边界：`cps/async_task/`。

```text
业务 producer
  └─ submit(job + items) ───────────────┐
                                       ▼
                               async_job / async_job_item
                                       ▲
              ┌────────────────────────┴────────────────────────┐
              │                    Runtime                         │
              │  Scheduler  →  bounded worker pool  →  handlers   │
              │      │                 │                  │        │
              │      ├─ claim/CAS      ├─ heartbeat        └─ domain│
              │      ├─ recovery       └─ fenced commit             │
              │      └─ aggregation                                 │
              └────────────────────────────────────────────────────┘
```

### 3.1 Scheduler/control thread

负责：

- 启动恢复扫描；
- 按配额领取到期 item；
- 计算 job 汇总状态；
- 回收过期租约；
- 维护实例 heartbeat 和 draining 状态；
- 处理 application wake-up 与固定周期 poll。

它不执行业务 handler，不做长 HTTP 调用。

### 3.2 Bounded worker pool

- 固定大小线程池，不为每个 job 创建线程；
- 线程只执行一个已领取 item；
- item 完成后回到池中等待下一个；
- 内存队列最多保存提示，不保存唯一待执行事实；
- 队列丢失、进程崩溃或线程异常都由数据库恢复。

### 3.3 Handler registry

- 启动时校验 `(job_type, job_version)` 唯一；
- 未注册 handler 的 job 进入 `FAILED` 或告警，不得永久静默滞留；
- handler 不依赖 Flask request context；
- 每个 handler 声明最大尝试次数、租约时长、并发 quota 和错误分类。

### 3.4 Lease heartbeat

- 每次领取生成随机 `lease_token`；
- heartbeat 只延长仍属于当前 owner/token 的 item；
- 续租失败即视为失去租约，handler 应在下一个安全点停止；
- 心跳线程属于核心控制面；业务代码仍不得自建 daemon。

## 4. 数据模型

目标表如下。实际字段名在实施 LLD 定稿后固化；当前仅定义职责与约束。

### 4.1 `async_job`

| 字段组 | 作用 |
| --- | --- |
| `id`, `job_type`, `job_version` | 任务身份与 handler 路由 |
| `owner_user_id`, `priority` | 权限、计费归属与调度优先级 |
| `idempotency_key` | 提交去重，唯一键 `(job_type, idempotency_key)` |
| `state` | job 状态机 |
| `payload_json`, `payload_hash` | 领域参数与完整性校验 |
| `total/succeeded/failed/skipped/running/waiting` | 聚合进度 |
| `cancel_requested_at`, `next_wake_at` | 取消与调度提示 |
| `created_at/started_at/updated_at/finished_at` | 生命周期时间 |
| `version` | 乐观并发版本 |

### 4.2 `async_job_item`

| 字段组 | 作用 |
| --- | --- |
| `id`, `job_id`, `item_key`, `sequence` | item 身份；唯一键 `(job_id, item_key)` |
| `state` | item 状态机 |
| `payload_json`, `checkpoint_json`, `result_json` | 输入、断点与输出 |
| `external_ref` | 外部任务 id、缓存键或上游查询句柄 |
| `attempt_count`, `max_attempts`, `next_attempt_at` | 重试预算与退避 |
| `owner_instance_id`, `lease_token`, `lease_expires_at`, `heartbeat_at` | 租约与 fencing |
| `error_code`, `error_message`, `error_retryable` | 稳定失败信息 |
| `created_at/started_at/updated_at/finished_at`, `version` | 生命周期与 CAS |

### 4.3 `async_job_attempt`

每次领取追加一行：

- `job_id`、`item_id`、`attempt_no`；
- `instance_id`、`lease_token`；
- `started_at`、`finished_at`；
- `outcome`、`error_code`、`error_message`；
- `external_ref`、`metadata_json`。

唯一键 `(item_id, attempt_no)`。该表用于审计、费用排查和恢复分析；默认保留期短于终态 job，具体天数由配置控制。

### 4.4 `async_runtime_instance`

- `instance_id`、`hostname`、`pid`、`app_version`；
- `started_at`、`heartbeat_at`、`draining_at`、`stopped_at`。

实例记录用于展示与诊断，不作为任务所有权本身；item 租约才是执行权。

### 4.5 索引

至少需要：

- job：`(state, next_wake_at, priority, created_at)`；
- item：`(state, next_attempt_at, lease_expires_at)`；
- item：`(job_id, state)`；
- job：唯一 `(job_type, idempotency_key)`；
- item：唯一 `(job_id, item_key)`；
- attempt：唯一 `(item_id, attempt_no)`。

## 5. 提交与执行时序

### 5.1 提交

```text
业务请求
  ├─ 校验权限与参数
  ├─ 计算稳定 idempotency_key
  ├─ BEGIN
  │    ├─ INSERT async_job
  │    └─ INSERT async_job_item(s)
  │  COMMIT
  ├─ runtime.wake()       # 仅降低延迟
  └─ 返回 job 状态快照
```

提交操作不直接启动线程。提交后进程立即崩溃，启动恢复仍能发现 `QUEUED` job。

producer 的 `idempotency_key` 只负责“同一次逻辑提交”的去重，`item_key` 与外部操作 key 才负责内容级幂等。二者不能混用：前者避免重复创建 job，后者避免恢复重试产生重复业务副作用。

### 5.2 领取

候选 item 必须同时满足：

- `state IN (PENDING, RETRY_WAIT, WAITING_EXTERNAL)`；
- `next_attempt_at <= now`；
- `lease_token IS NULL OR lease_expires_at <= now`；
- 所属 job 未取消；
- 当前 worker、任务类型、job 和上游 quota 都有空位。

SQLite 单写者场景使用短 `BEGIN IMMEDIATE` 事务完成“选一行 + CAS 更新 + 提交”，避免先查后写 TOCTOU。领取时：

- `attempt_count += 1`；
- 写入新的 `owner_instance_id`、随机 `lease_token`、`lease_expires_at`；
- item → `RUNNING`；
- job → `RUNNING`；
- 追加 attempt 开始记录。

同一 job 的默认并发为 1；需要并行时由 handler 显式声明 `job_max_concurrency`。

### 5.3 执行与提交

```text
handler.execute(ctx)
  ├─ SUCCESS / SKIP / RETRY / WAIT_EXTERNAL / FAIL_PERMANENT
  ▼
BEGIN
  UPDATE async_job_item
     SET state=?, result=?, checkpoint=?, next_attempt_at=?, version=version+1, ...
   WHERE id=? AND owner_instance_id=? AND lease_token=? AND state='RUNNING'
  UPDATE async_job_attempt
  UPDATE async_job aggregates
COMMIT
```

item 更新必须检查影响行数。若为 0，说明租约已丢失或被 fencing；worker 必须丢弃本次结果并记录 `lease_lost`，不得继续覆盖。

长 item 在内部安全点通过 `ItemContext.save_checkpoint()` 提交中间断点：

```text
UPDATE async_job_item
   SET checkpoint_json=?, heartbeat_at=?, lease_expires_at=?, version=version+1, ...
 WHERE id=? AND owner_instance_id=? AND lease_token=? AND state='RUNNING'
```

该更新与最终提交使用同一套 fencing 条件，但保持 item 为 `RUNNING`。影响 0 行时抛出 `LeaseLost`，handler 必须在下一个安全点停止；新 worker 从最近已提交 checkpoint 继续。checkpoint 提交成功不承诺外部副作用 exactly-once，仍需依赖稳定幂等键。

### 5.4 外部等待

翻译发布、异步 LLM 等任务返回外部 id 后进入 `WAITING_EXTERNAL`，记录 `external_ref` 和 `next_poll_at`。到期由 `poll_external` 查询上游：

- 完成 → `SUCCEEDED`；
- 仍运行 → 继续 `WAITING_EXTERNAL` 并推进下次轮询；
- 上游永久失败 → `FAILED`；
- 暂时不可达 → `RETRY_WAIT`。

外部轮询本身也必须受租约保护，避免多个 worker 同时查询和同时写最终状态。

## 6. 恢复、重试与 backoff

### 6.1 启动恢复

应用完成数据库初始化、handler 注册后启动 runtime：

1. 注册新的 `instance_id`；
2. 扫描 `RUNNING` 且租约已过期的 item；
3. 将过期 item 从 `RUNNING` 恢复为 `RETRY_WAIT` 或直接可领取的 `PENDING`；
4. 重算受影响 job 的汇总状态；
5. 扫描 `QUEUED`、已到期 `RETRY_WAIT` 和 `WAITING_EXTERNAL`；
6. 触发首次 claim。

恢复扫描不能依赖某个业务 service 的私有 `recover_active_jobs()`。

### 6.2 周期恢复

即使启动时没有积压，运行期间也可能有线程挂死、租约丢失或进程内异常。scheduler 必须周期扫描过期租约。

### 6.3 backoff

- 指数退避 + 随机 jitter；
- 上游 `Retry-After` 优先；
- 默认上限由 handler 声明；
- 达到 `max_attempts` 后转 `FAILED`，并在 job 上体现；
- 永久错误不参与退避；
- 取消请求优先于重试。

### 6.4 最大尝试次数与人工重试

- 每次领取先增加 attempt，异常崩溃也计入尝试；
- 人工重试可创建新的重试预算，但保留 attempt 审计；
- 不允许同一 item 的 `(item_id, attempt_no)` 重复。

## 7. 幂等与 fencing

### 7.1 稳定幂等键

推荐格式：

```text
magicbook:{job_type}:{job_id}:{item_key}:v{operation_version}
```

`item_key` 应来自业务内容或稳定序号，例如：

- 翻译：`text_hash`；
- 朗读：`text_hash + voice/style`；
- 单词详解：规范化词或词批内容 hash；
- 预览：`book_id + book_format + book_fingerprint + stage`。

### 7.2 副作用清单

每个 handler LLD 必须逐项列出：

- 数据库写入；
- 对象存储写入；
- moon-well/LLM/TTS 请求；
- 积分扣费；
- 消息或通知；
- 其他不可逆动作。

每项都要回答“崩溃后重试会发生什么”。

### 7.3 两种失租风险

1. **失租前请求失败**：新 worker 重试，通常安全。
2. **失租前外部成功、本地未提交**：新 worker 会再次请求；只能依赖上游幂等键、内容寻址缓存、查询已有任务或“先查后建”避免重复副作用。

核心运行时无法仅靠数据库解决第 2 种风险，因此上游契约审计是任务准入硬门禁。

## 8. 取消

取消请求在一个事务内：

1. 写 `cancel_requested_at`；
2. 将 `PENDING`、`RETRY_WAIT`、`WAITING_EXTERNAL` item 置为 `CANCELED`；
3. job 在运行中 item 结束后收敛到 `CANCELED`。

运行中 handler：

- 在安全点检查取消；
- 若上游调用不可中断，允许该次调用完成，但不能继续领取下一 item；
- 不能把已取消 job 通过 retry 静默复活。

## 9. 优雅停机

建议的初始参数：

| 参数 | 初始值 | 说明 |
| --- | --- | --- |
| `ASYNC_HEARTBEAT_SECONDS` | 10s | 续租频率 |
| `ASYNC_LEASE_SECONDS` | 45s | 默认租约 |
| `ASYNC_POLL_SECONDS` | 5s | DB 轮询兜底 |
| `ASYNC_SHUTDOWN_DRAIN_SECONDS` | 25s | 应用 drain |
| Compose `stop_grace_period` | 40s | 必须大于 drain |

这些值可按上游最长安全点调整；单个上游 HTTP 超时可以在 200s 左右，但心跳必须持续，容器退出时不能等待整段 HTTP 完成。

停机流程：

```text
SIGTERM
  ├─ runtime → DRAINING，停止 claim
  ├─ scheduler 停止派发新 item
  ├─ heartbeat 继续维持正在执行的租约
  ├─ handler 在安全点响应取消
  ├─ 已完成 item 正常 fenced commit
  ├─ 到期仍未完成的 item 保留租约，由新进程过期回收
  └─ 标记 instance stopped 后退出
```

可以主动释放尚未开始执行的租约；正在外部调用中的 item 不应被旧进程无审计地改成成功。交由租约过期回收 + 上游幂等更安全。

部署脚本仍应保留“代码指纹未变不重启”的优化，但不能把它当作任务可靠性的前提。

## 10. 并发与背压

默认策略：

- 全局 worker：4；
- `llm_publish`：2；
- `tts_provider`：1；
- `epub_cpu`：1；
- `io_poll`：2；
- 单 job：1；
- 单用户：同一高成本 quota 下不超过 2 个运行中 job。

调度顺序以 `priority DESC, next_attempt_at ASC, created_at ASC` 为主，并通过按 owner/job 轮转避免单个大 job 长期霸占。数值最终由实施配置固化，但任何 handler 都必须有上限且能解释。

## 11. 可观测性

每次状态变更写结构化日志：

```text
event=async_claim job_id=… item_id=… attempt=2 instance_id=… lease=…
event=async_success job_id=… item_id=… external_ref=…
event=async_retry job_id=… item_id=… next_attempt_at=… error_code=RATE_LIMIT
event=async_lease_expired job_id=… item_id=… old_owner=…
event=async_job_finished job_id=… state=PARTIAL_FAILED …
```

日志禁止记录原始 token、完整 prompt、全书正文。错误 message 需截断和脱敏。

至少观察：

- 每种 job 的排队数、运行数、重试数、失败数；
- 最老待执行年龄；
- 最近一次成功/失败时间；
- 租约过期回收次数；
- worker 利用率；
- 外部调用耗时、重试率、限流率；
- 终态 job 的部分失败比例。

## 12. 数据库与多进程边界

当前事实层是 `<config>/app.db` 的 SQLite。单进程 + 有界线程下，短写事务、`busy_timeout`、WAL/重试可以工作，但 SQLite 仍只有一个写者。

因此：

- 本轮单进程方案不因“没有跨进程锁”而不安全；执行权由数据库 CAS 租约表达；
- 真正的多 Web/Worker 进程启动前，必须评估并迁移到 MySQL 或 PostgreSQL；
- 不得只用 Redis 分布式锁替代持久任务事实；
- 不得把 SQLite 表复制到多节点共享盘后直接多进程写。

未来拆分时，runtime、handler、schema 与状态 DTO 不变，只替换运行位置和数据库能力；这保留架构退路，但不把拆分列为当前交付。

## 13. 迁移顺序

1. **只加核心骨架**：表、API、registry、scheduler、worker pool、recovery、shutdown；不接业务。
2. **R238 预览试点**：快照是派生数据，最易重建，用来验证租约、恢复和多阶段 checkpoint。
3. **整本朗读迁移**：单 item 费用明确，现有 moon-well 缓存提供自然幂等。
4. **全文单词详解批次迁移**：验证批 item、部分失败与覆盖率对账。
5. **整本翻译迁移**：验证外部任务发布、`WAITING_EXTERNAL` 和完成回收。
6. **收敛旧实现**：删除业务自建 daemon、私有花名册与重复恢复入口，保留兼容读取和必要旧表。

每个业务切换必须保持原 HTTP 接口与前端行为不变；先完成数据映射和双读/对账，再切写路径。活动 job 的迁移必须在无运行中批次或明确停机窗口执行。

## 14. 测试锚点

实施阶段至少覆盖：

- 同一 item 并发 claim 只有一个成功；
- 心跳续租后不会被回收；
- 停止心跳后租约过期并被新 worker 领取；
- 旧 owner 持过期 token 写回影响 0 行；
- 进程在每个阶段被 kill 后能恢复；
- 外部副作用重复调用受幂等键保护；
- 毒 item 达到上限后失败，不阻塞其他 item；
- 取消后不再 claim，运行中 item 收敛到取消；
- drain 窗口内停止 claim，超时后新进程可恢复；
- 队列满、worker 异常、数据库短时锁冲突均有明确行为；
- 状态聚合和用户可见进度不倒退、不假完成。

## 15. 后续实现 LLD 必填

实施 R240 时，LLD 必须明确：

- 实际 DDL、迁移版本和回滚；
- SQLite claim 的具体事务与 SQL；
- handler registry 初始化顺序；
- Flask app 启动/停止钩子的确切位置；
- 服务身份与现有 moon-well 调用的兼容方案；
- 每个存量 job 的字段映射、活动数据迁移和验收；
- Compose `stop_grace_period` 与进程 drain 的实测；
- 注入故障与重启恢复的测试证据。
