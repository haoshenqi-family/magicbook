# 验收标准与验证报告 · LLM 任务手动执行面板（R126 · admin-panel）

验证环境：开发机 macOS，`magicbook/.venv`（Python 3.14），`pytest tests/`。
标注说明：✅=本机已验证并附证据；⏳=本机不可验，需线上确认（原因见文末）。

## 1. AC 清单

| # | 验收点 | 结果 | 证据 |
| --- | --- | --- | --- |
| A1 | 面板仅管理员可访问（页面 + 4 个 ajax 入口） | ✅ | `test_plain_user_cannot_*` 4 条：非管理员一律 403；admin 页面 200 |
| A2 | 四个 ajax 端点转发到正确的 moon-well 路径 | ✅ | `test_forwards_to_expected_upstream_path` 参数化 4 条 |
| A3 | 请求体字段名逐字节透传（不做 snake_case 映射） | ✅ | `test_run_payload_is_passed_through_unchanged`：7 字段全等 |
| A4 | 空 body / 非 JSON body 不导致 500 | ✅ | `test_missing_body_becomes_empty_object_not_crash` |
| A5 | 上游拒绝（403 + Result.message）不被吞成泛用文案 | ✅ | `test_upstream_rejection_body_and_status_pass_through` |
| A6 | 表单控件齐全可定位（provider/model/concurrency/maxTasks/caller/replay/start/stop/进度表） | ✅ | `test_admin_page_renders_the_controls`（9 个锚点） |
| A7 | 导航入口仅 admin 渲染，且 id 全页唯一（防合并残留） | ✅ | `TestNavigationEntry` 3 条 |
| A8 | 中文用户看到的是中文（nav + 页面 + script 内文案） | ✅ | `TestChineseRenderingIsLiveNotJustPo` 2 条 + 手工渲染核对（见 §2） |
| A9 | 新增 msgid 在 zh po 中均有非空译文 | ✅ | `test_every_msgid_has_chinese_translation`（36 条扫描） |
| A10 | script 内不存在未被 Jinja 渲染的裸 `_( )` 调用 | ✅ | `test_no_javascript_runtime_gettext_call` |
| A11 | 模板 script 无相邻同文代码行（R113 型合并残留） | ✅ | `test_no_adjacent_duplicate_code_lines` |
| A12 | 渲染后的 JS 语法合法 | ✅ | 渲染页面 script 落 `docs/temp` 后 `node --check` → JS_SYNTAX_OK（临时验证，夹具已清） |
| A13 | 并发/上限的权威夹取在服务端，前端只展示上限 | ✅（ moon-well 侧）| `LlmTaskManualRunServiceTest#concurrencyAndMaxTasksAreClamped` |
| A14 | 队列数字来自 moon-well 任务表（刷新页面/进程重启后仍可信） | ⏳ | 需线上：面板轮询 `/run/status` 观察 claimed/succeeded 随任务表变化 |
| A15 | 真实跑一批任务：选 zhipu + glm-4-flash-250414 + 并发 2 + 上限 20，进度与终态正确 | ⏳ | 需线上（moon-well 未发版，4 个端点当前 404） |
| A16 | 停止：已认领未开始的退回 PENDING，调用中的自然跑完 | ⏳ | 需线上；单测侧 `#stopReleasesUnstartedRowsAndReportsProgress` 已覆盖逻辑 |
| A17 | 与自动执行模式互斥（enabled=true 时面板收到明确拒绝文案） | ⏳ | moon-well `#runRejectedWhileAutoExecuteModeIsOn` 已覆盖；面板侧需线上看文案 |
| A18 | moon-well 管理员白名单与 magicbook 管理员映射到同一 userId | ◐ | 生产 `app_user` 实测：`user_id=1` = `hsq`（`credit_account` 余额 1,007,760），其余 5 个为 lzy/hz/hz-1/llmtask 测试号/`magicbook-system`(6)。⇒ `admin-user-ids` 配 `[1]` 是对的；OIDC 换票是否真把 magicbook 管理员落到 id=1 仍需线上点一次确认 |

## 2. 本机验证记录

- **全量测试**：`pytest tests/` → **357 passed**（本次新增 21 条）。
- **zh 渲染核对**（临时用例，跑完即删）：把 admin 的 locale 置 `zh_Hans_CN` 渲染两页
  - 下拉框：`任务执行=True`、`Task Runner 残留=False`、`整本翻译=True`（既有词条未受影响）
  - `/llm-tasks`：HTTP 200；抽样 9 个中文文案全部命中；唯一"英文残留"是 JS 对象键名
    `maxConcurrency`（非用户可见文案），据此判定 `.mo` 重编译确实生效。
- **i18n 编译链**：`messages.po` 追加 35 条；重编译前已验证「当前 po 重编译产物与仓库内
  .mo 逐字节一致」，因此 .mo 的 diff 只包含本次新增，不会顺手改动他国语言条目。

## 2b. 交叉审查（AGENTS.md 要求）与修复

评审提出 3 条必须修 + 6 条建议修，处置如下（全部有对应回归断言或浏览器实测）：

| 编号 | 问题 | 处置 |
| --- | --- | --- |
| M1 | `loadOptions()` 每次把并发/上限覆盖成服务端值，而 `maxTasksPerRun=5000` ⇒ 管理员填 100、切一次供应商就变 5000，点开始即一批 5000 次真实调用 | ✅ 已修：`touched` 脏标记，只填未改动项；默认值改为 `min(100, 上限)`。浏览器实测：填 7 → 切供应商 → 仍是 7 |
| M2 | 切换 provider 只重建 datalist，输入框里的旧模型名跟着提交到另一个网关 ⇒ 整批 FAILED 且已耗配额 | ✅ 已修：change 事件里清空 `#lr-model`。实测：填 glm-5.3 → 切 magpie → 变空 |
| M3 | 无视 options 的 `enabled`/`admin`，面板看着可用、点什么都失败 | ✅ 已修：`applyCapability` 禁用开始按钮并给可读文案；未配置供应商标注「(未配置)」且 `<option disabled>`。实测 notadmin：按钮灰 + 点击后上游零调用 |
| S1 | 服务端夹取后的实际并发/上限被丢弃 | ✅ 已修：用 `/run` 回显值提示。实测填 9 并发 → 提示 `Max concurrency: 4` |
| S2 | 输入框不在 `<form>` 内，浏览器 `max` 校验永不触发 | ✅ 已修：补 `#lr-maxtasks` 的 max + 两个 hint 行显示服务端上限 |
| S3 | `@admin_required` 的 403 是 HTML，前端只能显示 `HTTP 403` | ✅ 已修：4 个 JSON 入口改 handler 内 `role_admin()` + JSON 403（对齐 `/ajax/credit/admin-adjust`），并加「门禁先于转发」断言 |
| S4 | `renderProgress`/`watch` 抛错无人接，poller 仍每 4s 报错 | ✅ 已修：每条 promise 链尾带 reject 分支；`fail()` 统一标记 handled |
| S5 | `currentRun` 永不清零 → Stop 可能打到别人的批次；连续 loadOptions 乱序回包会用旧 activeRunId 重启轮询 | ✅ 已修：run 结束（`running=false`）即清 `currentRun` 并停表；`optionsSeq` 丢弃过期回包。实测 10s 内 status 恰好 3 次（t0/4s/8s），无叠加 |
| 备注 | 跨仓库字段契约无测试 | ✅ 新增 `TestCrossRepoContract` 2 条：面板提交的键与 `LlmTaskRunReqDTO` 字段名互锁、前端读取的字段必须存在于三个响应 DTO（同工作区外自动跳过） |
| 备注 | moon-well 未发版时 404 只显示「请求失败」 | ✅ 已修：非 JSON 的 404 专门提示「需要发新版本」；另 Start 按钮初始禁用，options 成功后才解禁 |

## 2c. 浏览器实测（交互类缺陷只能靠真 DOM 判定）

`docs/temp/` 夹具 = 用 test client 渲染真实模板 + 注入 moon-well 打桩（fetch/confirm），
静态服务 `127.0.0.1:8099`，browser-use `evaluate_script` 驱动。覆盖 M1/M2/M3/S1/S5/404 六项，
结果已写入上表。夹具与临时用例用完即删（`docs/temp` 本就 gitignored）。

踩到的一条夹具自身教训（值得记）：第一版把打桩 `<script>` 插进了面板脚本 `<script>` **内部**，
浏览器把整段当成脚本文本，面板逻辑一行都没执行，而 `providerOptions=[]`、`queue=""`
看起来「像页面没数据」而非「脚本没跑」——判断依据是桩里定义的 `window.__calls` 变 undefined。
插在开标签之前才是对的。

## 3. 本机不可验的部分与原因

- moon-well 的 `/llm/task/run*` 尚未发版到生产，4 个代理端点在本地既无上游也无法打桩出
  真实语义（进度、限流退避、重放门禁都是服务端行为）。
- 更硬的边界：`session["moonwell_access_token"]` 只在 OIDC 回调里产生，本机没有合法的
  moon-well 签名令牌，任何依赖真实转发的流程都会 401（项目已知边界）。

⇒ A14–A18 需要：**moon-well 发版 + Nacos 加 `ai.llm.task-manual-run` 块 + magicbook 发版**
之后，由管理员在线上跑一批小上限（建议 `maxTasks=20`、并发 2）确认；届时一并核对
`admin-user-ids` 是否命中该管理员在 moon-well 侧的 userId。
