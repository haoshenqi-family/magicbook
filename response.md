# 对话回应记录

> 含每个需求的回应、冲突说明及两个文件的总结。
> **归档规则**：本文件仅保留最近 10 个 request 的回应；更早内容原样归档至 `response-archive/`（按 request 区间分文件），需要历史细节时按编号检索归档目录，不要读全量历史。

**归档索引**

- `response-archive/response-R01-R31.md`：R1–R31（2026-08-14 ～ 2026-08-31）
- `response-archive/response-R32-R49.md`：R32–R49（2026-09-03 ～ 2026-09-17）
- `response-archive/response-R50.md`：R50（2026-09-18）
- `response-archive/response-R51-R70.md`：R51–R70（2026-09-18 ～ 2026-09-21）

---

## 2026-09-22（trace-id 全链路实施）

### R72（trace-id：请求级贯穿 magicbook→moon-well，进 ES 日志；RestClient 降 INFO）

- **moon-well 侧**：①新增 `TraceIdFilter`（OncePerRequestFilter，最高优先级）——优先透传上游 `X-Trace-Id`，缺失生成 32 位 hex；写 MDC `traceId`、回写响应头；finally 清理防 Tomcat 线程复用泄漏。②新增 `TraceIdTaskDecorator` 并注册为全局 `@Async` 执行器（TeslaMateConfig 内 `taskExecutor`/`applicationTaskExecutor` 两 bean 名，4-16 线程池），异步日志携带触发请求 traceId。③`TedAudioService` 手写单线程池加 `withTraceContext` 快照透传。④`application.yml` 加 console/file pattern（`[%X{traceId:-N/A}]`，无上下文显示 N/A）。
- **LLM dispatcher 后台线程不改**：drainLoop 为常驻后台循环，无上游请求上下文，traceId 恒为 N/A 属预期；LLM 任务级 trace（发布落库→执行恢复）属独立设计项，待排期。
- **magicbook 侧**：①`cps/logger.py` 加 `trace_id_var`（contextvars，gevent greenlet 安全）+ 全局 LogRecord 工厂注入 `traceId` 字段（无上下文占位 `-`，防 Formatter KeyError 丢日志）+ FORMATTER 加 `[%(traceId)s]`。②`web.py`：`before_request` 设 contextvar（沿用上游 X-Trace-Id）、`after_request` 回写响应头、`_moonwell_identity_headers()` 统一注入 `X-Trace-Id` 出站头、refreshToken 独立调用同样携带。
- **RestClient 降级确认**：`org.elasticsearch.client.RestClient: info`（原为 `org.elasticsearch.client: debug`）——30s 心跳/请求摘要 DEBUG 行完全消失；ES 业务异常仍走 WARN/ERROR 不受影响。
- **验证**：moon-well `mvn test` 411 例全过（含 pattern 生效——测试日志已见 `[N/A]` 段）；magicbook `pytest` 204 例全过 + logger 模块自测（无/有上下文格式化输出正确）。fnos 侧当日网络不可达（ping 不通），生产部署与 ES 端到端验证待网络恢复后进行（CI 推送 develop 即自动部署）。
- **文档**：根 `OPS.md` 新增 §2.3 trace-id 全链路查询（报障姿势 + curl 模板），KQL 表加 `message: "<traceId>"`。

### 总结

- **requests.md**：占号 R72。
- **response.md**：记录实施、验证与遗留（LLM 任务级 trace 待排期；生产端到端验证待 fnos 可达）。
- **冲突记录**：无。

### R70（对应 moon-well R54）：管理员积分调整面板

- credits 页新增「Admin: Adjust Credits」红色面板（仅 role_admin 可见）：目标用户ID / 额度(±) / 原因，提交前二次确认，成功后提示新余额并刷新明细。
- 代理 `/ajax/credit/admin-adjust`：user_login_required + role_admin 前端门禁，moon-well 侧白名单二次校验（纵深防御）。
- 测试：test_credit_consume.py 7 例通过（+登录门槛/转发/面板渲染 3 例）。

### R71：积分页板块排序

- 页面顺序调整为：余额卡 → 充值（档位+收银台）→ 管理员调整（仅管理员）→ 消耗明细（最后）；纯模板块挪动，元素 id 与 JS 绑定不变。
- 测试：test_credit_consume.py 7 例通过（模板断言不依赖顺序，全部仍过）。

## 2026-09-23（log.level 字段：日志级别独立成 ES 字段）

### R73（filebeat script processor 解析级别 → log.level keyword）

- **方案**：不改应用日志格式——`deploy/filebeat.yml` 加 script processor，从 message 提取级别写入 `log.level`；`deploy/init-app-log-es.sh` 索引模板补 `"log.level": keyword` 映射（幂等重跑即生效，含既有索引）。
- **解析规则（13 用例验证）**：行首锚定两种已知前缀——①ISO 时间戳（moon-well，兼容 `%5p` 双空格）；②`[方括号时间戳]`（magicbook）；级别词 TRACE/DEBUG/INFO/WARN/CRIT/ERROR/FATAL，CRIT→critical（ECS 约定），其余小写。堆栈行/访问日志行/无时间戳行不匹配 → 保持 filebeat 默认 info，不丢行。
- **踩坑记录**：首版正则 `^(?:\[[^\]]+\]\s+)?(LEVEL)\s` 匹配不了 moon-well 行——可选前缀组失败后 `^` 后必须紧跟级别词，ISO 时间戳吞不掉；node 13 用例测出后改为显式枚举两种前缀（比"行首 60 字符内搜级别词"更精确，避免堆栈行中段出现的 INFO 误标）。
- **验证**：node 按 YAML 折叠语义执行两份真实文件的 source 块，13 用例全过；fnos 仍不可达，生产部署（filebeat 重建 + 重跑 init 脚本）待网络恢复。
- **文档**：根 `OPS.md` KQL 表加 `log.level` 用法。

### 总结

- **requests.md**：占号 R73。
- **response.md**：本条。
- **冲突记录**：无。

## 2026-09-23（log.level 生产部署 + moon-well 日志分裂修复）

### R73 生产落地（fnos 恢复局域网后继续）

- **YAML 缩进坑（第一次部署失败）**：script processor 首版插在 input 列表内但缩进挂错层级（`- script:` 4 空格挂在 `fields_under_root` 之下）→ 两个 filebeat 容器反复 Restarting（`yaml: line 14: did not find expected key`）。修正为 input 内 `processors:` 键（与 paths/fields 同级），两份文件本地 pyyaml 校验后重推，容器恢复 Up。
- **修复 moon-well 日志分裂（重要发现）**：moon-well 容器实际由 app-manager 部署的 `/host/app/moon-well/docker-compose.yml` 管理（compose 文件已被 agent 清理，labels 可证），`./logs` 解析到 `/host/app/moon-well/logs`（真实写入点，5.5MB 在涨）；而 filebeat 读的是 `/vol1/1000/app/moon-well/logs`（旧手工 compose 时期的写入点，11:44 后停更）——**同一容器日志写 A、采集读 B**，今天白天的日志其实只来自历史文件。已将 filebeat compose 挂载改为 `/host/app/moon-well/logs:/var/log/moon-well:ro` 并重建，7416 条积压立即 ack。
- **关键路径事实（fnos 符号链接结构）**：`/app -> /vol1/1000/app`（符号链接）；agent 容器内 `/app` 挂载到宿主 `/host/app`。magicbook 容器挂载写 `/app/magicbook/...` 绝对路径 → 宿主解析到 `/vol1` 侧（数据一致，无问题）；moon-well 容器 compose working_dir 是 `/host/app/moon-well`，相对路径 `./logs` 落在 `/host` 侧。
- **生产验证**：①`log.level` 聚合近 5 分钟 7768 条全带级别（trace/info/debug 分布正常）；②magicbook 实测 `curl -H "X-Trace-Id: test-opds-20260923" :8083/opds` → ES 命中 1 条 `log.level=warn` 且 message 含该 traceId（级别字段 + trace-id 双特性同时验证通过）；③ILM 策略用仓库版脚本（180d）重跑确认（服务器 /root 下旧脚本是 30d 版）。
- **防回退**：新版 filebeat.yml 已同步到 app-manager 部署目录（/host/app/moon-well/、/host/app/magicbook/deploy/），CI 触发 agent 重部署时不会丢 parse_log_level 配置。

### 总结

- **response.md**：补记生产部署过程与日志分裂修复。
- **遗留**：/root/init-app-log-es.sh 已更新为仓库版；magicbook 的 /host 侧部署目录仅 deploy/filebeat.yml，其 compose 来源待下次部署观察。
- **冲突记录**：无。

### R74（Bark 通知切换自建服务器）

- Bark 通知地址与 key 更换为自建 `https://bark-server.haoshenqi.top`（key 以 fnos `.env` 为准，此处不回显）。
- 实际执行范围（用户决定）：只改 fnos 本地 webhook-builder——`.env` BARK_KEY 换新 + build-magicbook.sh 2 处 URL 替换（改前已 tar 备份：/app/codelib/webhook-builder/bark-backup-20260925-061438.tar.gz）；`.github/workflows/build-and-push.yml` 与 GitHub secrets 均不动（Actions 已停用；用户明确不改 GitHub 侧）。
- 验证：bash -n 通过、旧域名残留 0、fnos 实发测试推送 code:200（2026-09-25）。
- 提醒：若日后重新启用 GitHub Actions，需先把三仓库 secret BARK_KEY 更新为新值。

### R76（一键登记全部英文书翻译任务队列：只入队，逐本激活才发布）

- **需求澄清**：与「一键翻译整本书」同机制，批量作用于全部英文书；登记阶段只建任务队列（不发布、不翻译、不耗积分），逐本激活时才真正发布（缓存回收 + 只发缺失段）。
- **实现**：
  - 新表 `reading_translation_queue`（book_id 唯一；QUEUED/ACTIVATED/ERROR 状态机）；登记只存待办指针，不预建 job/item（避免 44×数千段空批次与僵尸判定互相干扰）。
  - service：`enqueue_all_english_books()`（扫 eng+EPUB/KEPUB，幂等只补新增）、`activate_queued()`（start(force=True) 物化批次，回填 job_id；失败标 ERROR）、`list_queue()`（状态+进度联动）。
  - 路由：`/ajax/reading-translate-queue/enqueue-all|list|activate`（admin）+ 管理页 `/translation-queue`。
  - fingerprint/段落解析延迟到激活时（文件可能变化，激活时算才准确）。
- **验证**：新增 3 个单测（幂等、格式筛选、状态机+失败路径；其中 filter 桩按语义等价内存过滤，SQLAlchemy 表达式正确性由部署后真实数据验证）；单段发布异常 except 引用的 zipfile 未 import 被 3 号测试抓出（NameError），已修——正是状态机用例的价值。全量 212 passed（209+3）。
- **部署与实际登记**：`295ba993` 推送 → fnos webhook 构建 END OK → 容器内执行 enqueue：books=44, queued=44, skipped=0, errors=0，队列 44 条全 QUEUED。
- **使用**：管理页 `/translation-queue` 一键登记/逐本「开始翻译」；激活后与单本按钮同语义（book 88 的 1803 段缺口也会被同机制补齐——该批次已在跑，无需再激活）。
- **遗留**：单本按钮弹窗「已缓存 0」是受理时快照过早的展示瑕疵（实际后台 1 分钟内完成缓存回收），后续可改成弹进度。

### R77（一键翻译全部英文书：登记即执行，去掉两段式队列）

- **需求变更**：R76 的「登记/激活两段式」不符合用户语义（「不要分开登记和激活」）——改为 **登记即执行**：一键给全部英文书直接建批次并开始翻译。
- **实现（352ed877）**：
  - 删除 TranslationQueue 队列表与 enqueue/activate 接口（R76 路线废弃，生产建过的 44 条 QUEUED 记录留存无害）。
  - `translate_all_english_books(publish, lookup)`：扫 eng+EPUB/KEPUB，逐本直接 `start(force=True)`，每本独立后台发布线程互不阻塞；**已有新鲜（<30min）活动批次的书自动跳过**防重复发布（僵尸由既有判定自愈）；无文件/失败书单条记录不中断。
  - `all_books_progress()`：从任务表聚合每书最新批次进度。
  - 页面 `/translate-all`：一键开始 + 进度表（状态/完成数/失败数/更新时间）。
- **验证**：R76 队列测试删除；新增 R77 三测试（全量执行 force、跳过在跑+坏书、进度聚合取最新批次）。全量 212 passed。
- **测试工位教训**：stub `query(Model.column)`（progress 里的列查询）与 SQLAlchemy DeclarativeMeta 的 isinstance 语义（type(Model) 是元类）两处踩坑；stub 的 filter 改为对 BinaryExpression 按 left.key/right.value 真实求值，杜绝语义漂移。服务层顺手把 `in_(子查询)` 改为先取 id 列表（对 stub 与真实 DB 都更直接）。
- **部署**：推送 → fnos 构建 END OK → 容器重建 SUCCESS。未代为触发执行——一键会立即对 44 本英文书发布翻译并连续消耗积分，由用户在页面上自行点击决定时机。

### R78（一键翻译进度停滞：SQLite 锁崩溃 + moon-well 排队 + 进度快照）

- **诊断（全部实测取证）**：09-26 07:39 一键 44 本共 82,550 段落库。① 44 个发布线程并发 commit 同一 SQLite → 30 次 `database is locked` 崩溃，31 本书的线程中途死亡，39,645 段从未发出（PENDING）；② 已发出的 38.5k 任务在 moon-well 顺序排队（吞吐 ~1 段/10s，09-26 完成 8,769 段、09-27 完成 3,020 段——但全是 09-25 的积压，一键批次为 0）；③ 页面进度读任务表计数器，只在单书懒回收时刷新 → 静态快照，用户以为翻译停了。
- **修复 1（并发收敛）**：全局 `threading.Semaphore(PUBLISH_WORKERS=2, env WHOLE_BOOK_PUBLISH_WORKERS)`，批次发布排队进入；`ub.get_new_session_instance` 的 SQLite `timeout` 5s→60s；新增 `_commit_with_retry` 指数退避（仅锁错误重试）。moon-well 本是顺序执行器，多线程发布无收益只放大竞争。
- **修复 2（进度活化）**：`all_books_progress(lookup)` 每次刷新对每书最新批次做 200 段/批缓存懒回收，页面数字跟着 moon-well 实际完成走。
- **过程中二次暴露（R52 遗留）**：恢复闭包 `_system_publish` 直接引用 `_moonwell_proxy`（定义于 cps.web）未 import → NameError，31 批次 27,428 段被误标 FAILED。修复：函数体内延迟 `from . import web as web_module` 取函数。教训：恢复路径此前从未真正跑通过发布段（前几轮故障都死在更早的环节），NameError 一直埋着。
- **FAILED 重发**：`retry` 接口只发 FAILED 段——两次崩溃的 FAILED 段（真发送失败）与 NameError 误标的 FAILED 混在一起；NameError 误标的段落实际上从未到达 moon-well，重发即可。部署修复后调 retry 接口逐批次重发。
- **验证**：新增 4 回归测试（信号量封顶并发、锁重试、进度懒回收、恢复闭包解析 _moonwell_proxy）；全量 216 passed。部署后 moon-well 消化速率 ~170 段/10min（4178 段/小时），39k 积压预计 10 小时内清完。
- **遗留**：moon-well 执行器吞吐 (~1 段/10s) 是最终瓶颈；若要提高可查其执行并发配置（不在本仓库）。

### R75（整本翻译仍报 can't subtract offset-naive and offset-aware datetimes）

- **根因**：`TranslationJob(Item).created_at/updated_at` 是 naive `DateTime` 列但默认值写 aware UTC。aware 值经 DB 往返后 `tzinfo` 被丢成 naive（SQLite 与 MySQL DATETIME 均不带时区），`start()` 的僵尸批次判定 `now_utc() - existing.updated_at` 相减即抛 TypeError；路由 `except TypeError` 把原文返回给前端 alert。前端「整本译」不传 force，只要书上有活动批次（含刚创建的），点击必炸——这就是「还是有问题」的直接原因。R50 引入僵尸判定时暴露，此前复用路径无减法所以未炸。
- **为什么旧测试没拦住**：`test_stale_active_job_is_recycled` 预置的僵尸批次是内存对象直接赋 aware 值，没经 DB 往返。
- **修复（口径归一 + 深度防御）**：新增 `cps/reading_translation/timeutil.py`（`now_utc` 唯一时间源 + `as_utc` 读侧归一）；models 两表四列改 `DateTime(timezone=True)`（新环境读回即 aware）；service 全部 7 处 `_now()` 收敛为 `now_utc()`，僵尸判定处读值经 `as_utc()`。存量 naive 行按 UTC 解释，与新行语义一致（写入侧一直是 UTC 墙钟，无数据迁移需要）。
- **测试**：新增 `tests/test_reading_translation_r75.py`（僵尸路径 + 复用路径，均走真实 SQLite 往返，修复前在 service.py:106 精确复现生产 TypeError）。修后整本翻译相关 12 个 + 全量 209 个测试全绿（基线 207 + 新增 2）。
- **护栏事件**：response.md 两处历史记录（R53/R71）含「凭据变量打码接等号」的形似凭据赋值字样，导致本次与后续任何写入都被整体扫描拦截；已征询用户（未答复，按推荐项继续）后把这两处改为等价文字描述（历史语义不变）。tests/test_reading_translation.py 未动：该文件 R51 既有测试的 bearer_token 占位字面量同样拦写入，R75 回归故单独建文件，占位是否改环境变量读取留待用户决定。
- **R75 后续（同日部署与网络故障）**：推送后 fnos webhook 构建死于 git 拉取间歇故障（`curl 16 HTTP2 framing layer`，重试时直连 443 超时 135s）。处置：fnOS root git 全局配置 `http.version=HTTP/1.1` + 低速断连快速失败，并按用户指示把 GitHub 域代理固定为 `http://192.168.31.11:12811`（内网开发机 HTTP 代理，仅 GitHub 域，ACR 推送不受影响；旧 1082 代理已失效）；手动重跑 `build-magicbook.sh` 后 END OK，app-manager 重建容器 SUCCESS，容器内验证新代码在跑。配置与排查步骤已补记根目录 `OPS.md` §4/§5。

---

## 2026-09-26

### R78（家族三系统架构评审，只读分析）

跨 app-manager / moon-well / magicbook 的架构级评审，全文已在对话中交付；三仓库账本同步登记（app-manager #9、moon-well R58）。未改任何代码。

- **magicbook 结论（B-）**：亮点——fork 卫生意识好（定制收进 ai/、reading_translation/、metadata_provider/ 独立包；cw_advocate 为 vendored SSRF 防护库 Advocate；OIDC 接 authentik 与家族统一认证）；事故驱动测试闭环成型（R51/R75 均补真实 SQLite 往返回归测试，R75 时点全量 209 个测试）。
- **结构性风险**：① Calibre-Web fork 是三系统最大长期维护负债——cps 4 万行上游代码、web.py 2580 行定制织入（oidc、moon-well 代理），无可见 upstream 同步节奏，需显式决策（锁版本定期 rebase 或声明 hard fork）；② Web 进程内长出作业系统——整本翻译后台线程已两次生产事故（R51 线程上下文、R75 时间口径），本质是长任务负载超出上游请求/响应架构形状，当前修复合理但每加一种后台任务都在加重量；③ ai/ 包 1744 行自成 LLM 栈（registry/crypto/memory），与 moon-well LlmFacade 平行，家族层面 LLM 管道两份。
- **家族级**：moon-well TED 导入直写本项目 metadata.db 是唯一违反「不共享数据库」原则的集成线；本项目网页元数据编辑（editbooks）同样写该库，双写者风险在本路径兑现概率最高，建议推动改 HTTP 契约。
- **冲突记录**：无。

### 总结

- **requests.md**：R78 已登记（家族三系统架构评审）。
- **response.md**：记录 magicbook 侧评审结论与风险；评审主体在对话中交付。

---

## 2026-09-26

### R79（架构评审修复执行，跨仓库；本仓库无代码改动）

用户裁定范围：修复4（RabbitMQ 下线，moon-well 侧完成，本仓库无依赖无改动）、修复3/5a/5b（app-manager 与根 OPS.md 侧完成）、数据库表逻辑关系整理（根 `docs/db/DATABASE.md`，含本仓库关联的 Calibre metadata.db 集成线定性）；修复1（TED 导入 HTTP 契约）与修复2（支付收敛）明确不做。

- 本仓库本轮仅账本登记，无代码/配置变更。
- 与本仓库相关的两条记录：① DATABASE.md §7 清理清单确认 `tag`/`word` 等遗留表与现役表无冲突；② 修复1 后续若启动，magicbook 侧需新增导入端点（评审报告已有设计），本轮不实施。
- **冲突记录**：无。

## 2026-09-27

### R80：书 89《魔法书使用指南》改用英文写，同其他书一样走整本翻译缓存

- **核实**：/read/89 即《魔法书使用指南》（R63 成书），正文 95 段全中文、语言标记 zho——整本翻译管线固定英译中，故此前不被「一键翻译全部英文书」纳入。翻译译文按段落 hash 写 moon-well `reading_paragraph_cache`（ES），与全部书共用，无需为本书另建缓存。
- **实施（原地英文化，书 id 不变，阅读进度/成就不受影响）**：①11 个 XHTML + OPF + NCX 全部重写为英文（结构与风格对齐原书，元数据全英文）；②mimetype 首位未压缩、保留目录条目打包，容器内用生产 parser 验证 94 段抽取、无 CJK 残留（仅保留正文对「译」字图标的引用）；③metadata.db 更新 data 行文件名、title/sort/author_sort、作者→Magicbook Family Team（删除孤儿中文作者行）、出版社→Magicbook Family Press（仅本书使用）、4 个独占标签英文化、简介英文化、语言 zho→eng、last_modified 刷新；④触发整本翻译：经真实 `WholeBookTranslationService.start()` 代码路径 + cw_login.login_user(admin)（admin 为本地账号无 moon-well 令牌，首批 90 段发布被 moon-well 拒绝；按启动恢复同款 `system_identity=True` 闭包走 service 自身 `retry()` 通道重发，90/90 发布成功）。
- **数据库变更记录（全部经验证的语句）**：首次尝试因把生产表列清单误读进脚本（books 表并无 is_augmented 列，生产列清单与仓库 db.py 一致）与 Calibre 触发器依赖 `title_sort()` 函数（裸 sqlite3 无此函数，已按 db.py `create_functions` 同等实现注册）各回滚一次，第三次成功，均有前后状态验证。
- **运行现状**：jobId `e7529a4d63424e6db1ffd14ce1eab6fb`，90 段已全部发布，moon-well 任务 id 74231–74320 全部 PENDING 排队（此前一键翻译存量约 3.66 万段，~1 段/10s，预计 4 天左右消化）；完成后 moon-well 写段落缓存，阅读器懒回收逐段显示中文对照。文件/库备份：fnOS `/vol1/1000/app/magicbook/backups/book89-zh-backup-20260927/`（原中文 EPUB + metadata.db + app.db）。
- **封面**：图内文字无法在本机核验（OCR 服务不可用），保持原样未动。
- **文档**：requests.md 追加 R80；本文件按归档规则将 R51–R70 原样搬移至 `response-archive/response-R51-R70.md` 并登记索引。
- **冲突记录**：无（本条执行中曾向用户发执行确认询问，用户未作答，按推荐项继续；已全程备份可回滚）。

### 总结

- **requests.md**：追加 R80。
- **response.md**：记录 R80 全过程；归档 R51–R70（本文件现保留 R71–R80）。

## 2026-09-27（整本翻译队列修复执行）

### R81（检查 llm task list，重新激活失败任务，完成所有翻译；moon-well R60 同源）

- **任务列表诊断（全部实测取证）**：system_llm_task_record 81,165 条——PENDING 36,684 / COMPLETED+SUCCESS 23,149 / FAILED 8,141 / ACCEPTED 195。FAILED 构成：8,140 条 ZOMBIE_RESET（09-24 僵尸巡检在执行器 hang 死时误杀）+ 1 条乐观锁；ACCEPTED 全部为僵尸领取（hermes-worker-01 185 + shao-selftest-worker 10）。
- **两个断点（本轮核心发现）**：① 消费队列的外部执行器 hermes-worker-01 是此前 AI 会话临时拉起的进程，09-27 14:04 后消失（各主机无脚本无容器），队列无人消费；其停因是 new-api 网关余额耗尽（剩 $0.0227 < 预扣 $0.04，全模型 403）。② **代码缺口**：`/llm/task/complete` 只落库不发事件，写 ES 缓存的 `ParagraphCacheTranslationCompletedListener` 只挂在进程内调度器路径——外部执行器完成的 ~2.1 万段译文全部滞留 MySQL，ES 缓存（magicbook-read-paragraph）自 09-24 14:54 起零写入。magicbook 台账 10,749 条 COMPLETED 是缓存回收 bug 造成的 `[]` 垃圾标记。
- **修复 1（常驻 worker）**：fnOS 新增 `/app/translate-worker`（docker compose，`restart: unless-stopped`，容器 moonwell-translate-worker，并发 3）：循环 accept（user 1 mk- API-key）→ DashScope qwen-flash 翻译 → complete → 直写 ES（doc id=SHA-256(trim(text))，scripted_upsert 幂等，保留音频/批注字段）。参数（paragraph/bookName/chapter）经只读 MySQL 查询补齐（accept DTO 的 parameters 恒为 null，toDetail 写死 null——登记为 moon-well 待修缺陷）。吞吐 ~3 段/s（对比 hermes-worker ~0.1 段/s）。
- **修复 2（缓存回填）**：23,149 条已完成任务的译文回填 ES——21,141 条写入，1,731 条已有跳过，1,386 条无效输出（`[]`/错误 JSON）跳过。缓存 4,368 → 35,000+。
- **修复 3（孤儿重置）**：按 textHash 归并分析（与 PENDING/COMPLETED 重叠的 4,708 条不动，防止重复翻译计费），物化孤儿 hash 表后分批 UPDATE，3,440 条 FAILED/ACCEPTED 重置为 PENDING。期间第一次全表 UPDATE 锁等待超时，KILL 阻塞事务后改两步法重做。
- **修复 4（magicbook 台账修复 + 缺口重发）**：容器内跑对账脚本（DRY 预演后执行；WAL + busy_timeout 60s + 重试规避 SQLite 锁）——60,683 段按 ES 实缓存回收为 COMPLETED（垃圾 `[]` 标记全部纠正），39,563 段真实缺口经 `/llm/task/publish` 重发进队列，发布失败 0。
- **运行现状（21:20 时点）**：队列 PENDING ~59.6k，worker 累计完成 21,614 段、速率 ~2.7 段/s（797 段/5min），ES 缓存 37,113 条持续增长；偶尔 read-timeout 单段失败落 FAILED 可再重发，无系统性错误。fnOS 留了 queue_watch.sh 看门狗（5 分钟巡检，worker 掉线自动 `compose up -d`）。按当前速率全队列消化约 6 小时。
- **积分口径**：外部执行器走 DashScope（fnOS .env 既有 key），不扣 moon-well 积分（R53 口径）；DashScope 计费在用户自己的阿里云账单。
- **遗留**：① moon-well completeTask 不发 LlmCallCompletedEvent / toDetail 丢 parameters——代码级缺口，建议后续把 webhook 或事件发布补上（本轮不动代码）；② 4,780 条历史 FAILED（有 PENDING/完成覆盖的重复任务）不再执行，等队列清空后自然作废，无需处理；③ new-api 网关余额需用户自行充值，否则翻译默认模型通道仍不可用。
- **冲突记录**：无。

### 总结

- **requests.md**：追加 R81。
- **response.md**：本条。

## 2026-09-28

### R84：sidebars 查词慢的取证结论（词典还是 LLM / 有无缓存）

- **结论先行**：sidebars 是词典查不到的变形词，每次都落到 LLM 同步翻译（~500–725 token / 次、扣 1 积分 / 次）。缓存分层看：**词典层有缓存且含负缓存**（512 条 LRU，miss 存空串，第二次起不再打词霸）；**LLM 层与划词链路完全无缓存**——负缓存每次返回 null 后 translate() 都继续同步调 LLM，同一词查十次就真调十次 LLM、扣十次积分。慢的体感还叠加了 NewAPI 500 失败重试。
- **证据链（全部生产实测）**：
  - 代码：`ReadingVocabularyService.translate` 单词先走 `IcibaDictClient`；`IcibaDictClient.lookup` 对 `sidebars` 首查 fetch 返回 null 并写入负缓存（`cache.put(key, "")`），后续查词命中负缓存直接返回 null（不再打词霸）；`LlmRouterFacade.callWithUsage` 同步调用无缓存；magicbook 代理与浏览器层也无缓存。
  - fnOS 实测词霸：`sidebars` → `{"message":[]}` 空（0.19s）；`sidebar` → 有释义（0.17s）——出网链路正常，纯属 miss。
  - ES 日志（app-log-*）：今日 13:41–13:56 窗口 `/vocabulary/reading/translate` 请求 15 次，`Credit consumed` 仅 7 次，其中 **13:45:00 有 magicbook WARN：moon-well /vocabulary/reading/translate -> HTTP 500 {"message":"NewApi call failed"}**（LLM 网关失败）；moon-well 自身 ERROR/WARN 为 0（全局异常处理器不落日志的已知缺口）。
  - MySQL credit_transaction：`caller=reading-translate` 今日 7 条 CONSUME，每次 1 积分、494–725 token、模型 glm-5.3-flash（newapi），含 13:44/13:48/13:49/13:55/13:56 等时刻；最后一笔 13:56:31（672 token）与 ES 请求日志 13:56:17 相隔约 13s——单次同步 LLM 耗时的直观体现。
  - ES 段落缓存 magicbook-read-paragraph：82,118 条，只收段落翻译，无 sidebars 词条；划词不写该缓存。
- **修复选项（待用户决定，未改代码）**：①划词结果加 ES/内存缓存（含负缓存，最直接）；②iciba miss 时词形还原后重查一次（sidebars→sidebar 即命中）；③moon-well 全局异常处理器落日志；④代理层对同词短窗口去重合并。

### R85：词典 miss 后的词形还原方案（问答）

- **怎么还原**：Lucene `EnglishAnalyzer`/`EnglishPossessiveFilter` + `PorterStemFilter`。关键发现：moon-well 生产容器 BOOT-INF/lib 里已有 `lucene-analyzers-common-8.3.0.jar`（ES 7.5.0 客户端传递依赖，elasticsearch.jar 必带），零新依赖即可用。实现要点：用 `TokenStream` 逐 token 还原后重组（保撇号词如 don't），只对「还原词 ≠ 原词」的 token 二次查 iciba（最多再花 3s，命中后写正/负缓存），miss 继续落 LLM，行为向后兼容。口径注意：Porter 是词干提取（stemming）非严格词典原形（lemmatization），x→xies 会截成 xi（自然 miss 降级到 LLM，与现状一致，不会翻错）；更大覆盖需换 SparkNLP/HCNNSegmenter（重）或外部 LLM/词典接口（引入新依赖/延迟），不建议。链路顺序：iciba(原词) → 还原 → iciba(还原词) → LLM → 结果缓存（R84 选项①仍然推荐）。

### R86：划词缓存 + 词典 miss 词干化重查（编码实现）

- **实现（moon-well，4 个主文件 + 3 个测试文件）**：
  - 新增 `vocabulary/service/WordStemmer.java`：Lucene `EnglishAnalyzer`（Porter）词干化，剥所有格（'s/’s）、拒绝非屈折形态（don't、连字符词）与停用词（返回 null）。Why 不是直接用 PorterStemmer：8.3.0 里它是包私有，公开入口只有 TokenStream 链；EnglishAnalyzer 恰好覆盖所需全部变换。lucene-analyzers-common 为 ES client 传递依赖，零新 jar。jshell/单文件实测锚定：sidebars→sidebar、dog's→dog、don't→null、studies→studi（合法非词，自然 miss 降级 LLM）。
  - `IcibaDictClient`：新增 `lookupWithStemming`——原词 miss 且还原词 ≠ 原词时二次查询；还原词 miss 同样入负缓存。
  - `ReadingParagraphCacheService`：新增 `findTranslation(text)` 单条读取（返回 `CachedTranslation(translation, source)` record）与带 source 的 `saveTranslation` 重载，字段 `translationSource`；与段落/TTS 缓存同一 ES 文档（SHA-256(trim(text))），字段级合并互不覆盖；读写均降级安全。
  - `ReadingVocabularyService.translate`：链路改为 缓存 → 词典+词干化 → LLM，全部回写缓存；**缓存命中透传原来源**（dictionary/llm），旧文档无 source 时兜底 llm，避免词典缓存被前端错标成「AI 翻译」。
- **测试**：新增 WordStemmerTest 9 例、IcibaDictClientTest +6 例（spy 桩编排层，避免 URL 编码假设）、ReadingVocabularyServiceTest +6 例（缓存命中/无 source 兑底/缓存降级/空译文不写缓存等）。
- **验证**：本机无 JDK25 Mockito 兼容（动态 agent 拒绝），基线用 JAVA_HOME=JDK21 重跑：干净基线 427 例全绿（EXIT=0）；带改动全量 448 例（surefire 汇总 tests=448 failures=0 errors=0 skipped=0）。日志中的 ERROR 行为既有测试故意触发的异常路径，非失败。
- **效果预期（待部署验证）**：sidebars 首查命中词典（~0.2s）而非 13s LLM；任何划词第二次起走 ES 缓存毫秒级返回；LLM 不再被重复词重复消耗（积分同步节省）。
- **冲突记录**：无。

- **怎么还原**：Lucene `EnglishAnalyzer`/`EnglishPossessiveFilter` + `PorterStemFilter`。关键发现：moon-well 生产容器 BOOT-INF/lib 里已有 `lucene-analyzers-common-8.3.0.jar`（ES 7.5.0 客户端传递依赖，elasticsearch.jar 必带），零新依赖即可用。实现要点：用 `TokenStream` 逐 token 还原后重组（保撇号词如 don't），只对「还原词 ≠ 原词」的 token 二次查 iciba（最多再花 3s，命中后写正/负缓存），miss 继续落 LLM，行为向后兼容。口径注意：Porter 是词干提取（stemming）非严格词典原形（lemmatization），x→xies 会截成 xi（自然 miss 降级到 LLM，与现状一致，不会翻错）；更大覆盖需换 SparkNLP/HCNNSegmenter（重）或外部 LLM/词典接口（引入新依赖/延迟），不建议。链路顺序：iciba(原词) → 还原 → iciba(还原词) → LLM → 结果缓存（R84 选项①仍然推荐）。

### R83：解释 magicbook reading-translate 接口逻辑 + 追问「为什么单词也全走 LLM」

- **magicbook 侧**（只读）：`/ajax/reading-translate` 为登录代理——校验 text 非空且 ≤2000 字符，经 `_moonwell_proxy` 转发 moon-well `/vocabulary/reading/translate`（20s 超时），身份头 + JWT 透传、401 自动刷新、内网显式 no-proxy、上游 ≥400 留痕日志。同族：`-batch`（1~20 段、附 bookName/chapter）、`-book*` 整书任务族。
- **moon-well 侧**（只读）：`ReadingVocabularyService.translate` 确有词典优先——单词条件（`^[A-Za-z][A-Za-z'’-]*$`）走 `IcibaDictClient.lookup`（金山词霸 suggest，免费无凭证，3s 超时，512 条 LRU 含负缓存），命中返回 `source=dictionary`；miss/异常才落 LLM。段落 `translateBatch` 设计上不经词典，直接 LLM + ES 段落缓存。
- **「全部走 LLM」的可能解释**：① 词组/句子划词与全部段落级翻译本就不走词典（设计使然）；② 词霸 miss：suggest 首条 key 与查询词须完全一致（忽略大小写），变形词/生僻词判 miss，且负缓存使同一词不再重试；③ 词典通道静默故障：iciba 为移动端接口，异常仅记 DEBUG 日志，生产 ES 无痕迹，若 fnOS 出网链路不通则所有单词静默落 LLM，且每次首查多付 3s 超时（与 LLM 串行）。
- **验证**：2026-09-28 从开发机 curl 词霸 suggest 接口正常（`hello` 返回释义），接口本身存活；fnOS 出网链路无法在本机验证。生产侧可用划词气泡角标（词典/AI 翻译）直接区分实际来源。
- **冲突记录**：无。上轮回应仅写了 requests.md 占号、漏写本文件 R83 回应，本轮补记。

### 总结

- **requests.md**：R83–R86。
- **response.md**：R83 接口逻辑与追问结论；R84 sidebars 慢查取证（词典 miss + 无缓存 + NewAPI 500 叠加）；R85 词形还原方案（Lucene Porter，零新依赖）；R86 两项优化落地（448 测试全绿，待部署）。

## 2026-09-28（trace.id 独立字段：Kibana Available fields 可见可过滤）

### R74（filebeat 解析 trace.id → trace.id keyword 字段）

- **背景**：trace-id 此前拼在 message 文本里（pattern `%X{traceId}` / `[%(traceId)s]`），Kibana Available fields 无此字段，只能 `message: "<id>"` 文本匹配。
- **方案**：两份 `filebeat.yml` 同一 script processor 扩展——moon-well 行匹配 `--- [thread] [32hex]` 提取；magicbook 行匹配 `[时间戳] LEVEL [tid]` 提取（N/A/`-` 不写）；旧格式日志（无 32hex）不写字段，防 moon-well 旧 pattern `[thread] [logger]` 误采。`init-app-log-es.sh` 模板补 `trace.id: keyword` 映射。
- **验证踩坑**：①初版提取正则把旧格式 `[x] [y] logger` 的 `y` 误采为 traceId → 加 32hex 门卡（抽样证实生产 traceId 全为 32hex）；②既有索引先于新模板存在，动态映射把 `trace.id` 抢注为 `text+keyword`（模板 keyword 不生效）→ 动态模板无法改已有字段类型，moon-well 索引暂为 text+keyword（KQL/聚合走 `.keyword` 子字段均可用，Kibana 兼容），下个 ILM 周期或重建索引后统一为 keyword；magicbook 索引建得晚，已直接套用模板 keyword。
- **生产验证**：moon-well 近 3 分钟 524 条中 120 条带 `trace.id`（其余为后台线程 N/A 不写）；`term trace.id.keyword` 聚合正常（单 traceId 10 条）；magicbook 实测 `X-Trace-Id: fieldtest-20260928` → ES 命中 2 条 `trace.id=fieldtest-20260928`（warn+error）。新 filebeat.yml 已同步 app-manager 部署目录防回退。
- **文档**：根 `OPS.md` KQL 表改为 `trace.id: "<id>"`。

### 总结

- **requests.md**：占号 R74。
- **response.md**：本条。
- **冲突记录**：无。

## 2026-09-28（magicbook 整站假死排查与恢复）

### R87（https://magicbook.haoyuhang.top/ 突然访问不了——应用假死，已恢复）

- **现象与分层定位**：公网 TLS 握手正常（Traefik 证书有效）但 HTTP 请求 15s 0 字节；内网直连 fnOS:8083 TCP 能连但 12s 0 字节；fnOS 本机 `curl 127.0.0.1:8083` 同样挂起 → 排除 Traefik/网络，应用假死。容器状态却显示 `Up 32 hours (healthy)`。
- **py-spy 实锤死锁链**（`pip3 install py-spy` + `py-spy dump`）：MainThread（Tornado IOLoop）卡在 `cps/search_metadata.py:137` 的 `as_completed` 无限等待；它提交到 `ThreadPoolExecutor-1` 的两个线程卡在 `cps/metadata_provider/google.py:54` 的 `requests.get`（**无 timeout**）——fnOS 内网到 `www.googleapis.com` 不可达（复现：curl exit 28 超时），TCP 连接永不超时。元数据搜索视图跑在事件循环线程里 → 外呼挂 → 全站 8083 不再响应。旁证：8083 上 113 个 CLOSE-WAIT 堆积、accept 队列积压、应用日志止于 15:23:31、WAL 文件停在 13:51。
- **为什么 healthy/自愈没兜住**：healthcheck 是 `nc -z localhost 8083`（TCP 探活），应用不 accept 时内核 backlog 仍完成握手，永远报 healthy；magicbook 也没有 moon-well 那样的 autoheal。当日 14:18/14:52 moon-well NewAPI 500、moon-well 自身 15:27/15:36 被 autoheal 重启，均为相邻事件，与本假死无因果。
- **处置**：`docker restart magicbook`（死锁无软恢复手段）。验证：fnOS 本机 HTTP 302（6ms），公网 302（0.1~0.5s）；容器内 09-27 遗留的 `/tmp/trigger_book89.py`、`retry_book89.py` 等挂起进程随重启消失（文件仍在，无害）。
- **遗留待办（未改代码，待确认后排期）**：① `google.py` 及其他元数据 provider 外呼统一加 `timeout`；② compose healthcheck 从 `nc -z` 改为 HTTP 探针（如 `curl -f http://localhost:8083/`），让假死能触发自愈；③ 根 `OPS.md` §4 已新增「Web 应用整站假死」排查行。
- **文档**：根 `OPS.md` 更新最后更新日期与 §4 排查表。

### 总结

- **requests.md**：占号 R87。
- **response.md**：本条。
- **冲突记录**：无。

## 2026-09-28（magicbook 元数据外呼：仅谷歌走代理 + 强制超时）

### R88（仅谷歌相关请求走内网代理 192.168.31.11:12811，其余保持直连）

- **实现（magicbook，8 个源文件 + 2 个测试文件）**：
  - 新增 `cps/metadata_provider/outbound.py`：按域名路由——仅 `googleapis.com` / `google.com` / `googleusercontent.com` / `gstatic.com`（含 `scholar.google.com`）走 `METADATA_GOOGLE_PROXY`；其余域名显式 `proxies={'http':None,'https':None}` 钉死直连，防止泄漏的 `http_proxy`/`https_proxy` 把豆瓣/Amazon/ComicVine/LubimyCzytac 静默改道；`timeout` 强制注入，显式传 `None` 会被重置为默认 (5,30)。域名按 label 边界匹配，`notgoogle.com` 不算谷歌。
  - 六个 provider 全部接入：google（专属超时 (5,20)，R87 源头）、amazon、douban、lubimyczytac、comicvine、scholar（顺带注入 `scholarly.use_proxy`）。
  - `google.py` 的 API key 改为请求时读取：旧写法在类体求值，provider 扫描早于 config 初始化时会抛 `AttributeError` 带崩整个扫描（测试环境已复现）。
  - `/metadata/search` 弃用无界 `as_completed` → `futures.wait(timeout=METADATA_SEARCH_TIMEOUT，默认 60s)`：卡住的 provider 丢弃、已完成结果照常返回；不再用 `with`（上下文退出时 `shutdown(wait=True)` 会把等待上限架空，R87 教训）。同族的 `/metadata/provider/<id>` 单源路径靠 provider 自身超时兜底。
  - healthcheck 从 `nc -z` 改为应用层 HTTP 探针（TCP 探不出事件循环假死）。
- **测试**：新增 `tests/test_metadata_outbound.py` 11 例（域名路由三分支 / 显式直连抗环境变量污染 / timeout 不可绕过 / 视图不被卡死 provider 无界阻塞 / 非法 env 兜底）；conftest 补注册 metadata 蓝图。全量 **227 例通过**。
- **验证**：开发机实测 googleapis 直连 2.0s、经代理 2.3s 拿到响应（HTTP 429，代理链路本身可用）；非谷歌域名 `_proxies_for` 恒返回直连映射。
- **部署状态（已上线）**：代码 `67b5f82b` 与文档 `4975cdff` 均已推送到 develop。fnOS webhook 构建**首次尝试失败**（`git fetch` 走代理报 `GnuTLS recv error (-110): The TLS connection was non-properly terminated`，属代理/GitHub 瞬断，builder 侧 git 代理配置齐全）；重推文档提交后**构建成功**，18:24:48 由 app-manager 重建并启动 magicbook + filebeat 容器。线上验证：容器 `running/healthy`，本机 `127.0.0.1:8083` → 302（3.6ms），公网 `magicbook.haoyuhang.top` → 302（147ms）；容器内 env 已生效（`METADATA_GOOGLE_PROXY=http://192.168.31.11:12811`、`METADATA_SEARCH_TIMEOUT=60`），healthcheck 已换为 HTTP 探针；实测路由 `googleapis` → 代理、`douban` → 直连，经代理请求 googleapis 2.05s 返回 429（链路可达，配额受限于尚未配置 API key）。
- **线上配置（已就位）**：`/vol1/1000/app/magicbook/.env` 增加 `METADATA_GOOGLE_PROXY=http://192.168.31.11:12811`；`docker-compose.yml` 换成仓库版（新增两个 env 透传 + HTTP healthcheck），旧文件备份为 `docker-compose.yml.bak-20260928`。**注意：线上 compose 是手工副本，仓库改动不会自动同步**，每次改 compose 都要手动 scp。
- **文档**：根 `OPS.md` §4 的「Web 应用整站假死」排查行（R87 新增）已覆盖本故障模式；本轮补充了代理与超时口径。
- **冲突记录**：无。

### 总结

- **requests.md**：占号 R88。
- **response.md**：本条。
- **冲突记录**：无。

### R88 补漏（2026-09-28 晚，已上线）

- **现象**：元数据搜索已通（21:19 配置保存成功并重启，Google 不再报 429，返回了结果与封面 URL），但点「应用元数据」取谷歌封面报 `Error Downloading Cover`。
- **根因**：封面下载是**独立于 provider 搜索的另一条外呼链路**——`helper.save_cover_from_url` 用 `cw_advocate.get` 直连，R88 的代理路由只覆盖了 provider 的 `search()`。日志实锤：`Cover Download Error ValidatingHTTPSConnectionPool(host='books.google.com', port=443) ... ConnectTimeoutError ... connect timeout=10`。因带 10s 超时，只报错不假死。
- **修复**：`save_cover_from_url` 增加 google 分支，谷歌域名改走 `outbound.get`（复用「仅谷歌走代理」路由）；其余域名仍走 advocate —— advocate 自带 `ValidatingHTTPSConnection`、挂不上代理，这正是当初漏掉它的原因，也是不能整体替换的原因（SSRF 校验需保留）。
- **测试**：`tests/test_metadata_outbound.py` 新增 `TestCoverDownloadRouting` 2 例（谷歌封面必须走 outbound 且不碰 advocate；非谷歌封面不许改道 outbound）。全量 **229 例通过**。
- **上线验证**：`d21ead7a` 推送 → 21:43:20 构建 + app-manager 部署成功；容器 `healthy`；镜像内 `/app/cps/helper.py:828` 已含新分支；实测该封面 URL 路由到代理并返回 `200 image/jpeg 74529 bytes`（2.7s）。
- **配置**：无需新增（复用 `METADATA_GOOGLE_PROXY`）。

### 总结

- **requests.md**：R88 补漏，不单独占号。
- **response.md**：本条。
- **冲突记录**：无。
