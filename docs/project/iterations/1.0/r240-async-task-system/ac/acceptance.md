# AC — R240 核心异步任务体系

> 本轮只验收**设计与规范文档**。实现验收项保留给 D1 以后。
> 状态：设计待用户确认（2026-10-28）。
> 上层设计：[HLD](../hld.md) · [LLD](../lld.md)

## A. 本轮设计文档验收

### A1 统一权威入口

- [x] 从 `magicbook/AGENTS.md` 可以直接找到异步任务强制规范。
- [x] 规范明确“单进程 + 数据库租约 runtime，本轮不拆分 Web/Worker”。
- [x] 静态文档包含需求基线、内部接口、运行时 L3、任务作者准入清单。
- [x] HLD/LLD/AC 均能从迭代目录互相跳转。

### A2 架构完整性

- [x] 文档同时覆盖 job、item、attempt、instance 四类事实。
- [x] 文档明确数据库是唯一事实源，进程内集合不能判活。
- [x] 文档明确 CAS 租约、heartbeat、fencing、过期回收和启动恢复。
- [x] 文档明确 item 级 checkpoint 的受租约保护写入 API、最大工作损失和部分失败语义。
- [x] 文档明确至少一次执行 + 外部副作用幂等，不虚假承诺 exactly-once。
- [x] 文档明确取消、重试、错误分类、最大尝试次数和毒 item 处理。
- [x] 文档明确全局/类型/job/上游 quota 与有界 worker 池。
- [x] 文档明确 SIGTERM、drain、Compose grace 和不落原始凭据。

### A3 现有链路覆盖

- [x] 整本翻译、整本朗读、全文单词详解预览、全文单词详解批次都被纳入迁移分析。
- [x] book-finished bridge、legacy WorkerThread/APScheduler、请求级 fan-out 的边界被说明。
- [x] 每条现有链路有迁移波次或明确排除理由。

### A4 未来 Agent 门禁

- [x] `AGENTS.md` 明确禁止新增业务自管 daemon、进程内判活、`updated_at` 僵尸判据。
- [x] `task-authoring.md` 提供十一个设计门禁问题、禁止事项、测试矩阵和评审清单。
- [x] LLD 必须登记 job_type/version、item_key、幂等键、断点、重试、权限、quota、失败可见性和故障测试。
- [x] 例外必须获得用户明确批准并形成 ADR。

### A5 不越界

- [x] 本轮不新增运行时代码。
- [x] 本轮不创建数据库表或迁移脚本。
- [x] 本轮不修改 Compose 或部署脚本。
- [x] 本轮不修改 moon-well。
- [x] 现有业务 HTTP 契约不变，不声称任何行为已上线。

## B. D1 实现前置验收（未来）

- [ ] 核心表 DDL、索引、迁移和回滚已评审。
- [ ] 双线程/双实例 claim 同一 item 只有一个租约成功。
- [ ] heartbeat 丢失后租约可回收，旧 owner 写回影响 0 行。
- [ ] 启动恢复对 `RUNNING`、`QUEUED`、`RETRY_WAIT`、`WAITING_EXTERNAL` 均有测试。
- [ ] SIGTERM 真机测试证明停止 claim，drain 与 Compose grace 顺序正确。
- [ ] handler registry 能发现未注册 job 并告警/失败，不静默滞留。
- [ ] 核心 runtime 关闭时旧任务链路仍可回滚运行。

## C. D2–D5 业务迁移验收（未来）

- [ ] R238 预览切核心后，原 `/ajax/word-detail-preview` 状态和页面行为兼容。
- [ ] 整本朗读切核心后，`/ajax/reading-tts-book*` 端点、进度和重听计费语义不变。
- [ ] 全文单词详解批次切核心后，覆盖率和失败展示不变，毒批不阻塞整本。
- [ ] 整本翻译切核心后，publish 受理、`WAITING_EXTERNAL` 轮询、完成回收和重试可用。
- [ ] 所有迁移链路都有“外部成功后本地提交前崩溃”的验证或明确风险登记。
- [ ] 旧 daemon、进程内花名册和 30 分钟判活不再被新代码引用。

## D. 文档验证记录

本轮执行：

- 文档路径与链接静态检查；
- `git diff --check`；
- 确认无运行时代码、数据库、Compose、moon-well 变更。

- 结果：文档链接 0 broken（排除站点路由 `/me`、`/credits`）；`git diff --check` 通过；
  `git status` 仅含 `AGENTS.md` 与 `docs/` 变更。详见本轮 `response.md` R240。
