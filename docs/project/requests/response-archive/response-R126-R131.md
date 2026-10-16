# response 归档：R126–R131

> 2026-10-09（R141 写入触发窗口轮转）从 `response.md` 原样搬移：R126（LLM 任务手动执行面板）、R127（跨项目文档评审）、R128（AGENTS.md 三级体系）、R129（L1/L2 骨架与归档补账）、R131（单测闸门分级）。只搬移原文，不总结、不改写、不改编号。

## 2026-10-07（R126 LLM 任务手动执行面板）

### R126（LLM 任务手动执行面板，对齐 moon-well R110 US3）

- **交付**：`cps/web.py` 5 视图 + `_llm_task_admin_gate()`；`cps/templates/llm_tasks.html`（provider/model/caller/并发/上限/重放 + 开始·刷新·停止 + 4s 轮询进度）；`layout.html` admin 下拉新增 `top_llm_tasks`；42 条英文 msgid 进 `zh_Hans_CN` po 并**重编译 .mo**（重编译前先验证「当前 po 重编译产物与仓库内 .mo 逐字节一致」，确保 diff 只含新增）；`tests/test_llm_task_run_r126.py` 28 条。全量 `pytest tests/` → **364 passed**。
- **薄代理边界**：请求体原样透传（不做 snake_case 映射层，否则两侧契约漂移无人发现），队列语义/夹取/退避/重放全在 moon-well；**不**把 `/llm/task/run*` 加进内网互信白名单——手跑真实消耗模型配额，必须带管理员本人 token 才能归因与拒绝。
- **交叉审查抓到 3 条必须修**（都已在真浏览器夹具里实测修复）：① `loadOptions()` 每次覆盖并发/上限输入，而 `maxTasksPerRun` 默认 5000 ⇒ 管理员填 100、切一次供应商就变 5000，点开始就是一批 5000 次真实调用（改为 `touched` 脏标记 + 默认 `min(100,上限)`）；② 切 provider 不清模型名 ⇒ A 网关的模型名提交到 B 网关，整批 FAILED 且配额已耗（change 里清空）；③ 无视 options 的 `enabled`/`admin` ⇒ 面板看着可用、点什么都失败（Start 初始禁用，options 成功且白名单命中才解禁；未配置供应商 `<option disabled>`）。
- **建议修一并处理**：JSON 端点从 `abort(403)`（HTML）改为 handler 内 JSON 403（对齐 `/ajax/credit/admin-adjust`），并加「门禁先于转发」断言；回显服务端实际夹取值（填 9 → 提示并发 4）；`renderProgress`/`watch` 异常接入 reject 分支；`currentRun` 在 run 结束时清零 + `optionsSeq` 丢弃过期回包（实测 10s 内 status 恰好 3 次，无叠加轮询）；404 专门提示「moon-well 需发新版」。
- **新增跨仓库契约测试**（2 条）：面板提交的键与 moon-well `LlmTaskRunReqDTO` 字段名互锁、前端读取字段必须存在于三个响应 DTO。首跑就因正则不容嵌套泛型误报 `modelCandidates`，修正后确认两侧字段名对齐。
- **浏览器夹具的一课**：第一版把打桩 `<script>` 插进了面板脚本的 `<script>` **内部**，浏览器当脚本文本处理、面板逻辑一行没跑，而 `providerOptions=[]` 看起来像「没数据」而不是「脚本没执行」——判据是桩里定义的 `window.__calls` 变成 undefined。插在开标签之前才对。夹具与临时用例已删（`docs/temp` 本就 gitignored）。
- **待线上验收**（AC A14–A18）：moon-well 发版 + Nacos 加 `ai.llm.task-manual-run` 块后，用小上限（`maxTasks=20`、并发 2）跑一批，确认进度、停止、与自动模式互斥的文案。白名单口径已用生产数据预核：`app_user` 中 `user_id=1` = `hsq`（余额 1,007,760），`admin-user-ids` 配 `[1]`；OIDC 换票是否把本管理员落到 id=1 仍需线上点一次确认。
- **台账**：`requests.md` 追加 R126（前一条 125 有并行会话重复编号，未回改）；`docs/feat/llm-task-run/design/admin-panel.md` + `ac/admin-panel-ac.md`；本文件。

### R127（跨项目 L1-L3 文档评审与产品评估，只改文档）

- **范围**：配合家族根 `docs/product-review-2026-10-07.md` 的产品评估，对本仓库文档做正确性核查修正。**零代码改动**。
- **REQUIREMENTS.md 全册勘误**：在线站点旧域名 hyh.→**magicbook.haoyuhang.top**；§6 加 R98 架构变更横幅（AI 伴读已后端化 moon-well，cps/ai 退役、provider 配置移交 ai.llm.configs，各条目标〔历史〕）；§7 关闭「deepseek V4 flash 模型名待澄清」待办（已不适用）；§8 补 2026-10-07 变更记录行。
- **状态行失实回填（4 份）**：whole-book-translation「尚未开发」→已实现并经 R47/R76/R78/R101 多轮生产迭代；sso-user-unification「待评审」→Authentik sub user_key + JWT 代理链已上线；ai-agent magicbook-side「待排期」→R98 已实现；ai-reading-companion 英文实现计划加「已被取代」横幅（防止误按旧架构施工）。
- **口径修正（2 份）**：oidc-login.md 加端口口径注（本文按裸机 8085，生产实况 fnOS Docker 8083）；docs/reading-vocabulary.md「2026-09-14 临时调整」标注为持续近月的现状 + 指向 moon-well HLD 判定口径 + 恢复路径。
- **体系结论**（供后续决策，本次未动）：本仓库无 L1/L2/L3 分层，AGENTS.md 前置阅读要求的 `docs/kb/project-describe/` 为空壳——建议沿用 moon-well 模式引入三级体系，优先建「阅读器/词汇测试/LLM 任务面板」三个模块的 L1/L2；详见家族评估文档 §5.3。
- **总结**：requests.md 本条 R127；response.md 现存 17 个 R 级标题，**超出 10 条保留窗口（R120 完成时未归档，既有欠账）**，本条未代执行搬移；冲突记录：无（R123/R124 并行撞号系历史已记录事项）。

### R128（AGENTS.md 文档规范升级：引入三级体系规则）

- **改动**：AGENTS.md 文档规范节升级为三级表——L1 `docs/readme/`、L2 `docs/<module>/hld/` 标注**骨架待建**（新建内容一律按表落位，勿再新增游离文档；建设方案列家族方案 P1-A 待批准）；L3 `docs/feat/` 已成型。新增三级联动纪律四条：交付三问、数值同源（以 fnOS 生产实况与 moon-well 现行契约为准）、状态行强制（L3 design 头部必须有状态行，附 R127 一次修出 4 份失实先例）、历史文档只标注不重写（附 ai-reading-companion 横幅先例）。
- **规范与实况脱节修复**：核心工作流第 3 步「必须优先阅读 docs/kb/project-describe/」加空壳注记（当前仅 .gitkeep，实际入口 = 根 README + docs/REQUIREMENTS.md）；kb 行注记「填实或删除」待决策。
- **总结**：requests.md 本条 R128；response.md 追加本条（窗口欠账同 R127 所记）；冲突记录：无。

### R129（执行文档统一方案：magicbook L1/L2 骨架 P1-A + 归档补账）

- **P1-A 骨架落地**（9 个新文件）：L1 = docs/readme/readme.md（索引+分级表）+ library/reading/vocabulary/companion/credit/admin 六份模块 README（只讲功能；比方案的 4 模块多出 library/admin——书库是产品主入口、管理面板已有独立页面，均从既有 feat/REQUIREMENTS 归纳，无虚构功能）；L2 = reading/hld/hld.md（/ajax/reading-* → moon-well 代理映射表，端点逐一对照 cps/web.py 现核）+ vocabulary/hld/hld.md（判定/测试/设置代理映射，契约权威指向 moon-well）。
- **AGENTS.md 同步**：三级表「骨架待建」注记摘除（L1 ✅ 6 模块 / L2 ✅ 首批 2 份）；核心工作流前置阅读改为 docs/readme/readme.md + docs/REQUIREMENTS.md；联动纪律第一条去掉「骨架建好后生效」。
- **P1-B**：内网设备表指针化至 ops + app-manager truth（六处副本收敛）；**P2-D**：归档规则修订为「写入即检查、超 10 立即搬移」。
- **归档补账**：R111–R119 段（含乱序并行的 R116 条目）原样搬移至 response-archive/response-R111-R119.md，response.md 顶部补建全量归档索引；加本条后窗口恰 10 条。
- **遗留**：kb/project-describe 空壳的「填实或删除」仍待决策（本次以 readme/readme.md 作为前置阅读入口绕开）。
- **总结**：requests.md 本条 R129；冲突记录：无（129 未被并行占用）。

## 2026-10-08（R131 单测闸门分级）

### R131（单测逻辑改两级：开发态部分单测，正式发布才全量）

- **AGENTS.md「编码实现 · 交付标准」**：原「代码完成后必须确保项目可正常启动且全量单元测试通过」改为两级——**开发态（默认）**只跑本次新增/改动用例所在的测试文件 + 受影响模块的相关测试文件（`.venv/bin/python -m pytest tests/test_reading_vocabulary.py`），不要求全量；**正式发布态**（用户显式提出「正式发布 / 上线」，或按「Git 分支管理」把 `develop` 合并 `master`）才跑全量 `pytest tests/`，以 0 失败为判据并把用例总数写入本文件。
- **实况注记（已写入文档）**：push `develop` 即触发 fnOS 构建自动上线（`../ops/runbook.md` §1），构建链不跑测试，全量单测历来只是人工闸门，故「正式发布」以用户显式指令为准；开发期跳过全量的跨模块回归风险由该闸门兜底。
- **§4 bug修复** 条款与新口径天然一致（「更新单元测试并验证通过」＝开发态部分单测），未改。
- **跨仓同步**：moon-well R119 / app-manager R36（Maven 侧命令与 `clean`、管道退出码两条判据）/ magiclens R30（无自动化测试，两级闸门落在手工验收清单）。
- **窗口**：本条回应后 response.md 含 10 个 request 的回应（R120/R122/R123/R124/R125×2/R126/R127/R128/R129/R131），未超 10，无需搬移。
- **总结**：requests.md 本条 R131；冲突记录：无（131 未被并行占用）。只改文档，未动代码与测试。

---

