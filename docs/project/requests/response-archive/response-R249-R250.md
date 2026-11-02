## 2026-10-29（R249：整本朗读 worker 复用请求会话，批次停在进行中）

### R249（用户：「book 145 的整本朗读不是已经完成了吗？为什么显示未完成，我点击还可以继续」；追加：「搜索 es 缓存 确定一下」）

- **结论先行**：用户的直觉对了一半。ES/MinIO 里的整本音频缓存此前已经基本齐全，但批次台账确实没有完成；`RUNNING 207/1348` 不是缓存被清空，而是后台 worker 在请求线程关闭数据库事务后崩溃，剩余 1141 段一直没有被台账收口。
- **ES/缓存核验（修复前）**：按 book 145 当前批次的 1348 个 `text_hash` 查 `magicbook-read-paragraph`，命中 1347 个文档且全部带 `audioObject`；对应 1347 个 `reading-tts/<hash>.mp3` 在 MinIO 中全部存在、均非空，只有第 1117 段缺失。1347 条音频的 `bookName` 全是 `Matilda`，生成日期为 2026-10-09/10，所以用户看到过整本朗读效果，但 2026-10-29 新批次尚未收口。
- **根因**：生产 `init_db()` 把普通 `Session` 实例赋给 `ub.session`，整本朗读 daemon 与 HTTP 请求线程共用它。请求线程提交/关闭事务后，worker 于 11:41:59 下一轮 autoflush 抛 `sqlalchemy.exc.ResourceClosedError: This transaction is closed`；线程被花名册注销，但 job 仍为 `RUNNING`，且还有 PENDING 段，因此接口返回 `canResume=true`，页面显示「继续」。
- **为什么 207 次请求无异常**：`app-log-moon-well` 同时间窗内 `source=book-tts-batch` 的 `/tts/speak` 正好 207 次且无 ERROR，均命中旧缓存；台账只有逐段请求成功后才标 `DONE`，所以缓存已存在的 1140 段仍显示 `PENDING`。缓存齐备不等于批次完成，二者不能混为同一状态。
- **修复**：`WholeBookTtsService._synth_worker()` 改用 `_thread_db_session()` 的独立 engine + 线程作用域会话，逐段 `_commit_with_retry()`；每轮 `expire_all()` 让请求线程写入的 `CANCELLED` 可见；`_refresh_counts()` 显式接收 worker session；请求侧 `progress()` 提交后 `refresh(job)`，避免返回旧 `RUNNING` 快照。start/status/retry/cancel 契约、轮询、缓存与计费口径不变。
- **测试**：新增 `test_synth_worker_never_uses_request_session`，把 `ub.session` 换成任何访问都会报错的哨兵，worker 仍用独立会话跑到 `COMPLETED`。相关回归 **268 passed / 0 failed**，`git diff --check` 通过。
- **上线与生产验收**：实现 `39759318` 已快进推送 `origin/develop`；fnOS 构建并部署成功，容器 `running/healthy`，镜像 label `house.build-sha=39759318a53cd35f8d877c0afffd6783e861ba0d`。生产点击「继续」后从 207 段续跑至 `COMPLETED`，最终 `done=1348 / failed=0 / pending=0`，日志记录 `finished (done=1348 failed=0)`，部署后无新的 `worker crashed` 或 `ResourceClosedError`。
- **缓存补齐**：续跑后 ES `magicbook-read-paragraph` 为 1348/1348 段音频引用，MinIO 对应 1348 个对象全部存在且非空。`/book/145` 页面显示「整本朗读 · 已完成」「100%」「1,348 / 1,348」，「继续」按钮消失；刷新后出现「整本朗读已缓存」标识。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 明确后台任务不随页面请求中断；契约 → 无变化；实现/边界 → L3 `docs/product/library/features/whole-book-progress.md` 增加 worker 独立会话与「台账/缓存双口径」；本次实现 → R214 LLD §21、AC C12、需求基线、迭代 `plan.md` 与 requests.md R249。
- **窗口与驻留**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R237 整节原样搬至 `response-archive/response-R237.md` 并登记索引，窗口恢复 10。worktree `../magicbook-r249-tts-worker-session`（分支 `fix/r249-tts-worker-session`）按闸门保留待用户验收，验收通过后再清理。
- **总结**：requests.md 条目 249 已从占位回填；本条为回应。冲突记录：无撞号。迁移债务：本修复只隔离 R240 迁移前的存量 daemon 会话，整本朗读后续仍须迁入统一 async-task runtime 的租约、心跳与 fencing。

## 2026-10-29（R250：管理员运营站内信——自由撰写、单发/群发、发送历史与整批撤回）

### R250（用户：「我需要开发这个功能」；拍板：正文 500 字、仅管理员、单次最多 5000 人、支持撤回、全体包含管理员本人）

- **结论先行**：功能已上线，当前为**已上线待验收**；本轮沿用 `../magicbook-r250-admin-mail` worktree，不新建树。magicbook 提供管理员后台与薄代理，moon-well R230 持有运营邮件事实、批次审计与整批撤回。
- **页面与权限**：新增 `/admin/mail`，从 `/admin` 管理页进入，页面仅 `role_admin()` 可访问。五个代理 `users / audience-count / send / campaigns / recall` 都先校验 `role_admin()`；moon-well 再用 `credit.admin-user-ids` 做第二层白名单，非管理员本地 403 且不触达上游。
- **发送能力**：支持指定一人/多人或全体；全体包含管理员本人；指定用户去重后 1–5000 人，5001 在前端与服务端均拒绝。标题 trim 后 1–80 字，正文纯文本 1–500 字；跳转仅 `/credits`、`/buddy`、`/achievements`、`/learning`、`/mail`，无按钮时服务端返回 `actionPath=null`。
- **精确人数与确认**：全体模式通过独立 `audience-count` 代理读取真实人数，不加载全量名单估算；人数未知时禁止预览/发送，5000 可预览、5001 被阻止。编辑标题/正文只使预览失效，不丢失已取得的人数；发送确认显示精确人数，并说明可整批撤回、但收件人可能已看到，不误称发送不可撤销。
- **历史与撤回**：历史按发送时间倒序分页，显示范围、标题、目标/成功人数、操作人、正文与撤回状态；未撤回批次可整批撤回。撤回二次确认明确不可恢复；成功后刷新历史与 `MBMail` 未读数，失败显示上游 message，不乐观删行。moon-well 只删本批 `ADMIN_ANNOUNCEMENT`，审计永久保留，重复撤回幂等。
- **用户侧渲染**：运营邮件复用现有 `/mail`、抽屉 Mail、设置入口与伙伴信封；`mail.js` 用文本节点渲染 `title` 与 `customMessage`，不使用 `innerHTML`。原三类系统邮件的投递、已读/解决语义不变；服务端读取运营路径时也再次校验白名单。
- **文档四问**：能力 → `docs/product/readme/companion.md`；契约 → `docs/product/companion/interface.md`；实现/边界 → 新建 `docs/product/companion/features/admin-mail.md` 并同步 `mail-inbox.md`；本次实现 → `docs/project/iterations/1.0/r250-admin-mail/`（HLD/LLD/AC，状态已上线待验收），迭代 `plan.md` 已补行。R243 的“不做运营群发”边界标注为已被 R250 取代。
- **验证**：合并最新基线后定向回归 **160 passed / 2 warnings**；正式发布态全量 **1182 passed / 0 failed / 4 warnings**。`node --check` 与 `git diff --check` 通过；5000/5001 边界拆成两个独立 Node 进程，避免异步状态互相污染。
- **状态与驻留**：worktree `../magicbook-r250-admin-mail`（分支 `feat/r250-admin-mail`，占号 `64b0b1a9`）保留待验收。实现提交 `be4aebbd`，台账冲突合并 `5562db69`，最新基线合并 `e9c5d8fe`，发布合并 `77eacb85` 已推 `origin/develop`（`25d4af9f..77eacb85`）；fnOS `build END OK`、app-manager `deploy SUCCESS`、容器 `running/healthy`、`house.build-sha=77eacb85ad1849884819fba433a4dc840aba46c9`，生产 `/login` 200，匿名 `/admin/mail` 302 到登录页。
- **窗口与总结**：合并 R252/R253 基线后窗口达 11 节，按「写入即检查」把最早 R244 整节原样搬至 `response-archive/response-R244.md` 并登记索引，窗口恢复 10。requests.md 条目 250 已回填；冲突记录：无撞号，moon-well R230 为跨仓同源编号。
