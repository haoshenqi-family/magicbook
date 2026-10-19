# LLD — R130 LLM 队列监控面板

> 状态：已实现（2026-10-19 merge 回 develop 待验收；未 push 未上线——push 即触发 fnOS 构建链，由用户拍板）
> 上层设计：[hld.md](./hld.md)。前稿（行号漂移）：`_legacy/feat/llm-task-run/design/admin-monitor.md`。

## 1. 代理端点（magicbook 侧新增 6 路径）

沿用 R126 形制：`cps/web.py` `_LLM_TASK_PATHS` 追加映射，`cps/routes/vocab.py` 新增 6 个 `POST /ajax/llm-task/*` 处理器，body 原样透传（无字段映射，两侧 DTO 命名直接对齐），`_llm_task_admin_gate()` 双闸（magicbook `role_admin()` + moon-well 白名单）。

| magicbook 端点 | 转发目标（moon-well） | 超时 | 说明 |
| --- | --- | --- | --- |
| `POST /ajax/llm-task/admin-overview` | `/llm/task/admin/overview` | 10s | 无入参 |
| `POST /ajax/llm-task/admin-failures` | `/llm/task/admin/failures` | 15s | `{caller?, sinceHours?}` |
| `POST /ajax/llm-task/admin-page` | `/llm/task/admin/page` | 10s | keyword 联合过滤在服务端强制，前端先本地校验并提示 |
| `POST /ajax/llm-task/detail` | `/llm/task/detail` | 10s | `{taskId}`；管理员可看任意任务（归属校验放行） |
| `POST /ajax/llm-task/admin-recovery-plan` | `/llm/task/admin/recovery-plan` | 20s | confirm 恒不传（只读预案） |
| `POST /ajax/llm-task/admin-republish-failed` | `/llm/task/admin/republish-failed` | 30s | 仅在二次确认后带 `confirm:true` |

## 2. 关键响应结构（前端消费字段，权威 = moon-well DTO）

- `overview`：`callers[{caller,pending,accepted,running,completed,failed}]`、`pendingCount/acceptedCount/runningCount`、`oldestPendingCreatedAt`、`lastFinishedAt`、`ratePerHour`、`throughput[{hour,completed,failed}]`（近24h）、`stale{oldestAcceptedAt,minutesSinceLastFinish,acceptedOverThreshold}`、`reclaim{requeued,exhausted}`、`acceptedTimeoutHours/acceptedMaxRequeue`（阈值回显）。
- `failures`：`totalFailed`、`unknownRatio`、`buckets[{category,recovery,count,firstAt,lastAt,sampleTaskId,sampleMessage(80字),perHour[{hour,count}],matchedErrorCode}]`。
- `page`：`PageVO` 瘦行（taskId/requestId/userId/caller/mode/taskType/priority/status/completed/provider/model/acceptedBy/时间三戳/latencyMs/三 token 数/errorCode/errorMessage/paramsPreview/promptChars/outputChars），pageSize 夹 1–50。
- `recovery-plan|republish-failed` 共用：`mode(PLAN/EXECUTED/BLOCKED)`、`byCategory[{category,recovery,count,sampleTaskId}]`、`replayEligible/republishEligible`、`plannedLimit`、`blocked/blockReason`；EXECUTED 另有 `republished/skippedDuplicate/skippedForbiddenCategory/failed[{taskId,reason}]`。
- 失败分类 → 恢复方式（moon-well `LlmTaskFailureCategory` 全枚举）：`STALE_CLAIM(AUTO_REQUEUE)`、`STALE_EXHAUSTED(FORBIDDEN)`、`ZOMBIE_RUNNING(REPLAY)`、`NETWORK(REPLAY)`、`TIMEOUT(REPUBLISH)`、`RATE_LIMIT(REPUBLISH)`、`CONTENT_FILTER(FORBIDDEN)`、`AUTH(FORBIDDEN)`、`OUTPUT_INVALID(REPUBLISH)`、`UNKNOWN(MANUAL)`——前端按 `recovery` 字段渲染按钮，不自行枚举推断。

## 3. 页面结构（`cps/templates/llm_tasks.html` 增量）

```text
/llm-tasks（R126 手动执行区不动，下方追加）
├── #lr-mon-overview   总览：全局计数行 + caller 表 + 吞吐迷你柱状（纯 CSS）+ stale/reclaim 预警条；15s 轮询（visibilitychange 暂停）
├── #lr-mon-failures   失败分类：caller 下拉 + 时间窗(24h/72h/168h)；桶表（分类/恢复/数量/首末时间/样本消息截断）；未知占比警示
├── #lr-mon-tasks      任务查询：过滤栏(caller/status/errorCode/userId/taskType/keyword/时间区间) + 50/页分页表 + 行点击 → 详情 modal（params JSON 折叠、prompt/output 默认 2KB 截断可展开、token/延迟角标）
└── #lr-mon-recovery   恢复：选 caller(+errorCode/category 可选) + limit → 生成预案(PLAN) → 预案表（byCategory、eligible 数）→ 「确认重发 N 条」二次确认弹窗 → EXECUTED 结果（republished/skipped/failed 明细）
```

- 前端本地校验：keyword 未搭配 caller/status/errorCode/userId 时禁用查询按钮并提示（服务端同款约束）。
- `AUTO_REQUEUE`/`FORBIDDEN` 桶：只读展示「自动回收 / 禁止重发」徽标，无按钮。

## 4. 权限与安全

- 页面 `@user_login_required + @admin_required`（R126 同款）；6 个 JSON 端点走 `_llm_task_admin_gate()`（JSON 403，不落 HTML）。
- 详情 modal 展示 prompt/output 全文属管理员敏感面：不新增日志落盘（HttpLoggingFilter 已有截断规则，遵循现网口径）。

## 5. i18n

新增 msgid 全部走五步链（`mbT` 字面量 → `i18n_seed.html` → po 手工补 → pybabel 编译 → 契约测试 JS_FILES 清单），中英双语；测试钉 msgid↔po 一致（R126 范式）。

## 6. 测试计划（守卫 = 契约形制断言）

新文件 `tests/test_llm_task_admin_monitor_r130.py`，monkeypatch `web._moonwell_client.proxy`：

1. 6 端点转发 path/payload/timeout 断言（含 confirm 恒不带/仅确认后带）。
2. 非 admin → JSON 403（非 HTML）。
3. keyword 联合过滤：前端配置对象含该约束文案（防回归删除提示）。
4. 模板守卫：四区块 id 存在、相邻重复行检测、msgid↔po 一致 + zh 真实渲染。
5. 恢复按钮渲染规则（recovery∈{AUTO_REQUEUE,FORBIDDEN} 不出按钮）——模板级断言。

## 7. 上线顺序与回滚

- moon-well 已上线，无顺序依赖；magicbook 单仓 push develop → fnOS webhook 自动构建。
- 回滚 = revert 本仓 commit（纯增量，无 schema/契约变更）。

## 8. 文档四问（2026-10-19 已回填）

- L1（能力）：`docs/product/readme/admin.md` 已加「LLM 队列监控」条目。
- L2（契约）：**落位更正**——设计原写 vocabulary/interface.md（基于错误调查结论，该文件并无 llm-tasks 代理表）；admin 模块此前无 L2，按「随演进补齐」**新建 `docs/product/admin/interface.md`**，10 个端点全量收录（R126 四条 + R130 六条）。
- L3（实现）：admin 模块 L3 未建（仓规「随演进补齐」），本 LLD 即实现记录。
- LLD：本文件状态行（已改「已实现待验收」）。

## 9. 实现纪要（as-run，与设计的偏差与坑）

- **msgid 禁 `%`**：Jinja i18n 扩展对译文做 `%`-格式化，含 `%N` 的 msgid 渲染即 `ValueError: unsupported format character`；占位符改 `{N}/{C}`，JS `.replace('{N}', …)` 语义不变。
- **i18n 通道**：模板内联 `{{_('…')}}` + script 内 T 表（Jinja 渲染）——不走 i18n_seed/mbT 链（那是静态 JS 文件的通道）；po 手工补 60 条 + `pybabel compile`。
- **分页响应** = `PageVO{records, total}`；状态下拉取 `LlmTaskStatusEnum` 八值、恢复分类下拉取 `LlmTaskFailureCategory` 十值——均由跨仓契约测试钉住（漂移即红）。
- **详情全文展开**：长文存 JS 内存 `detailCache`，HTML 属性只放键名——避免把数千字符转义塞属性。
- **轮询暂停**：`setInterval` 内查 `document.hidden` 跳轮 + `visibilitychange` 切回立即刷一轮。
- **UI 改版（2026-10-19 验收反馈「元素堆叠太拥挤」）**：四区块纵向全宽堆叠改为 **Bootstrap 3 nav-tabs**（一次一个区块，layout 已载完整版 bootstrap.min.js 含 Tab 组件）；总览改「三个大数字 stat 块 + caller 表(7 栏)/吞吐柱+预警(5 栏) 双栏」；任务查询与恢复的 form-inline（8/4 个无标签控件挤一行）改 **label+控件栅格**（col-sm-6/col-md-3，两行四列）；「去恢复此类」跳转从滚动改为切 Tab。新增 msgid 仅 `Created from/Created to` 两条（其余全部复用），po+mo 已同步。所有区块 id / data- 属性 / JS 契约保持不变，测试零改动全绿。
