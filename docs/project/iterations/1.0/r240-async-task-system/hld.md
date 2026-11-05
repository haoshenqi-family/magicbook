# HLD — R240 核心异步任务体系

> 状态：**设计（待用户确认）**（2026-10-28）
> 关联：Ship [MB-231 / idea c9HjwIa2](https://haoshenqi.pingcode.com/ship/ideas/c9HjwIa2) · 迭代 `1.0` · 单仓 magicbook。
> 本轮范围：**仅设计、写文档；不实现代码、不建表、不改部署、不处理 moon-well。**

## 1. 用户诉求与结论

用户要求：

> 做 magicbook 的异步任务体系设计，并把它作为一个核心模块来处理，写文档声明，以后的 agent 做异步任务必须按照这个异步任务体系来设计实现。先只做设计，写文档。暂时按照不拆分来处理。

结论：

1. 建立 `async-task` 核心工程模块，统一任务台账、调度、租约、恢复、重试、取消、幂等和可观测性。
2. 当前不拆分 Web/Worker。单进程内运行有界执行器，数据库是唯一任务事实源。
3. 部署重启仍会发生，但任务最多重做当前安全点，并在租约过期后自动恢复；不允许永久卡在 `RUNNING`。
4. 新建 `docs/product/async-task/` 静态规范，并把强制准入规则写进 `AGENTS.md`；以后 Agent 不得新增自管 daemon 的业务异步任务。
5. 现有整本翻译、整本朗读、全文单词详解属于迁移债务，后续分波迁移，不在本轮改代码。

## 2. 当前事实

### 2.1 已有异步链路

| 链路 | 当前执行方式 | 恢复现状 |
| --- | --- | --- |
| 整本翻译 | 请求建 `job/item`，daemon 发布到 moon-well，查询进度时懒回收 | 启动钩子单独恢复有 `PENDING` 的活动批次 |
| 整本朗读 | 请求建 `job/item`，daemon 逐段调用 `/tts/speak` | 用户再次点击、retry 或轮询时按进程内花名册补线程 |
| 全文单词详解预览 | 持久化快照，daemon 解析 EPUB 并检查缓存 | 下一次页面请求补线程 |
| 全文单词详解批次 | 请求建批 item，daemon 分批发布 | 用户再次点击或 30 分钟僵尸判定 |

其他后台行为还包括 book-finished bridge、legacy `WorkerThread`、APScheduler 和请求级元数据 fan-out，成熟度与恢复要求不同，需按 LLD 的目标分类迁移或明确排除。

### 2.2 根因

- `JobServiceBase._live_workers` 是进程内集合，重启即清空，不能证明任务是否存在；
- 每个 job 自建 daemon 线程，缺少全局并发和统一停机；
- `updated_at` 30 分钟僵尸判定恢复慢，也无法区分“线程死亡”与“长任务仍在运行”；
- 翻译有启动恢复，TTS/详解没有统一恢复，行为分裂；
- `docker compose up -d` 会重启容器，daemon 线程没有 drain；
- 任务状态虽大多落库，但执行权、断点和幂等策略没有形成统一契约；
- R238 已明确：当前进程内锁只适用于单进程，多进程需要 DB lease。

## 3. 方案选型

| 方案 | 结论 | 理由 |
| --- | --- | --- |
| A. 单进程 + 数据库租约驱动 runtime | **采用** | 不增加部署单元；直接解决重启恢复、并发抢占与停机；与当前 SQLite、Flask/Tornado 形态兼容 |
| B. 立即拆分 `magicbook-web` / `magicbook-worker` | 暂不采用 | 拆分不自动带来可靠性；同 compose 全量重启仍然一起停；额外引入身份、部署、观测和版本兼容成本 |
| C. 引入 Celery/RQ + Redis/RabbitMQ | 暂不采用 | 新增基础设施；SQLite 任务事实仍要迁移；当前规模不需要 |
| D. 继续加强 daemon 线程与进程内锁 | 否决 | 进程重启即失效，无法解决根本问题 |
| E. 只增加 `stop_grace_period` | 不充分 | 只能缩短窗口，不能恢复 kill/崩溃/超时后的任务 |

### 3.1 为什么不拆分也可以

可靠性取决于五个机制，而不是进程数量：

1. 持久化 job/item 与 item 级 checkpoint；
2. 数据库 CAS 租约和 owner heartbeat；
3. 租约过期回收 + fencing；
4. 外部副作用幂等；
5. 优雅停机与启动恢复。

只要这些成立，单进程重启后可以继续执行。拆分 worker 的主要收益是“只发布 worker 时不影响 Web”或“Web 发布不杀长任务”，属于**发布隔离**，不是任务正确性的前提。

未来如果长任务确实成为发布瓶颈，再抽取同一 runtime + handler 为独立进程；届时 SQLite 必须换成支持可靠行级锁的数据库。

## 4. 目标架构

```text
业务模块
  └─ producer API：事务内创建 job + items
          │
          ▼
  async_job / async_job_item / async_job_attempt
          ▲
          │ DB CAS 租约 + heartbeat + fenced commit
  async-task runtime（与 Web 同进程）
    ├─ scheduler / recovery
    ├─ bounded worker pool
    ├─ handler registry
    └─ instance registry / observability
```

核心边界：

- Runtime 拥有调度、租约、状态机、重试、取消和恢复；
- Handler 拥有领域执行与业务结果；
- Producer 拥有业务权限、参数校验、job/item 拆分和幂等键；
- 业务 API 保持自己的页面和端点，不强迫用户感知“核心任务框架”。

## 5. 关键不变量

1. 数据库是任务唯一事实源；内存只做提示。
2. 同一 item 同一时刻至多一个有效租约 owner。
3. 所有执行结果写回必须带 owner + lease token。
4. 进程重启后不依赖旧线程状态恢复。
5. 外部副作用必须有稳定幂等键或可查询句柄。
6. 每个 handler 有最大尝试次数、并发 quota 和取消语义。
7. 失败必须落稳定错误码并对用户可见。
8. 不持久化用户原始凭据。
9. 应用 drain 必须短于容器 grace。
10. 单进程不得成为省略可靠性的理由。

## 6. 产品与工程文档分工

| 文档 | 回答 |
| --- | --- |
| [`async-task/requirements.md`](../../../../product/async-task/requirements.md) | 核心模块应该具备什么能力、边界与非目标 |
| [`async-task/interface.md`](../../../../product/async-task/interface.md) | producer / handler / status / 状态机契约 |
| [`async-task/features/runtime.md`](../../../../product/async-task/features/runtime.md) | 运行时、表结构、租约、恢复、停机、迁移顺序 |
| [`async-task/features/task-authoring.md`](../../../../product/async-task/features/task-authoring.md) | 未来 Agent 的设计、实现、测试与评审门禁 |
| 本 HLD / [LLD](./lld.md) / [AC](./ac/acceptance.md) | R240 这次为什么做、准备怎么实现、如何验收 |

## 7. 落地波次

| 波次 | 内容 | 出口 |
| --- | --- | --- |
| D0（本轮） | 静态规范 + HLD/LLD/AC + AGENTS 强制声明 | 用户确认设计 |
| D1 | 核心 runtime 骨架、表、registry、租约、恢复、停机测试 | 不接业务也能证明故障恢复 |
| D2 | R238 预览迁移 | 验证多阶段 checkpoint 与派生数据重建 |
| D3 | 整本朗读迁移 | 验证单 item 外部调用与自然缓存幂等 |
| D4 | 全文单词详解批次迁移 | 验证批 item、部分失败、覆盖率对账 |
| D5 | 整本翻译迁移 | 验证 `WAITING_EXTERNAL` 与完成回收 |
| D6 | 收敛 legacy daemon 与旧恢复入口 | 新任务只允许核心 runtime |

每一步保持现有业务 HTTP 契约，先做数据映射与对账，再切写路径。不得大爆炸切换全部链路。

## 8. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| 单次外部调用可能在 lease TTL 内未完成 | heartbeat 持续续租；handler 声明 lease 和 timeout |
| 外部成功、本地未提交造成重复调用 | 强制幂等键审计；上游需支持去重/查询；无法保证的链路显式登记风险 |
| SQLite 写锁冲突 | 短事务、`busy_timeout`、有限重试；核心调度串行 claim；多进程前迁 MySQL/PostgreSQL |
| 优雅停机被长 HTTP 拖死 | `SIGTERM` 停止 claim；drain 超时后退出；租约过期由新进程恢复 |
| 迁移期间新旧实现并存 | job_type/version 分开；切写前对账；旧记录只读或冻结 |
| 用户 token 过期导致恢复失败 | 后台改用服务身份 + owner 计费归属；不落原始 token |
| handler 吞异常或无限重试 | 统一 Outcome/错误分类、最大尝试次数与毒 item 测试 |
| 文档只写原则、Agent 仍绕过 | AGENTS.md 强制准入 + LLD 十一问门禁 + code review checklist |

## 9. 回滚与暂不实现边界

- 本轮只有文档，不涉及运行行为，可直接以文档 revert 回滚。
- D1 后续实现必须保持新表增量、旧表不删；runtime 开关关闭时旧链路可继续运行。
- 任一业务迁移失败时，只回退该 handler 的写路径，不删除核心 runtime 与审计数据。
- 不做：拆分进程、引入消息中间件、修改 moon-well、自动迁移现有活动 job、修改生产部署。

## 10. 文档四问

- **能力变了吗？** 本轮无用户可见能力变化；新增内部核心模块规范。
- **契约变了吗？** 现有业务 HTTP 契约不变；新增内部 producer/handler/status 目标契约。
- **实现/边界变了吗？** 新增 L3 运行时架构与强制准入清单，明确现有实现是迁移债务。
- **本次怎么实现？** 本轮只落 HLD/LLD/AC 与静态规范；编码状态仍为“设计”。

## 11. 待用户确认

1. 是否接受“单进程 + 数据库租约 runtime，本轮不拆 worker”的总方案。
2. 是否接受把 `AGENTS.md` 的异步任务准入设为强制门禁，例外需用户明确批准。
3. 是否按 D1→D6 的分波顺序实施；本轮不进入 D1。
