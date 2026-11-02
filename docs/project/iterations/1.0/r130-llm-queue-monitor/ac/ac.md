# AC — R130 LLM 队列监控面板

> 逐条可勾选；验证环境 = 测试库 + 管理员账号（白名单 `ai.llm.task-manual-run.admin-user-ids`）。

## A1 总览

- [ ] GIVEN 管理员打开 /llm-tasks WHEN 队列有任务 THEN 总览区显示全局 pending/accepted/running/completed/failed 与 caller 分组表，数值与 `POST /llm/task/admin/overview` 直查一致
- [ ] GIVEN 页面停留 WHEN 15s 到点 THEN 自动刷新一次；WHEN 切到其他标签页 THEN 轮询暂停、切回恢复
- [ ] GIVEN `oldestPendingCreatedAt` 超过阈值 WHEN 渲染 THEN stale 预警条可见（含 acceptedTimeoutHours 回显）

## A2 失败分类

- [ ] GIVEN 存在失败任务 WHEN 选 caller + 24h THEN 十类分桶表渲染，`unknownRatio` 显示；样本消息截 80 字
- [ ] GIVEN bucket.recovery ∈ {AUTO_REQUEUE, FORBIDDEN} WHEN 渲染 THEN 该行无重发按钮、有只读徽标

## A3 任务查询与详情

- [ ] GIVEN 只填 keyword 不填 caller/status/errorCode/userId WHEN 点查询 THEN 按钮禁用/提示约束（且不发请求）
- [ ] GIVEN 合法过滤 WHEN 查询 THEN 50/页分页正常，行字段（caller/status/errorCode/latencyMs/tokens）齐全
- [ ] GIVEN 点击行 WHEN 详情返回 THEN modal 展示 params/prompt/output（默认 2KB 截断可展开）；非本用户任务管理员可见

## A4 恢复

- [ ] GIVEN 生成预案 WHEN confirm 未带 THEN 返回 mode=PLAN 且零写库（重发前后 `failed` 计数不变）
- [ ] GIVEN 预案展示 WHEN 点「确认重发 N 条」THEN 二次确认弹窗（caller/N/plannedLimit）→ 确认后 mode=EXECUTED，republished+skipped+failed 明细可见
- [ ] GIVEN 非管理员 WHEN 访问任一新端点 THEN JSON 403（非 HTML）

## A5 守卫与文档

- [ ] `tests/test_llm_task_admin_monitor_r130.py` 全绿（转发形制/403/模板/i18n 守卫）
- [ ] L1/L2/LLD 状态行已按四问回填；msgid 五步链走完（zh 渲染验证）
