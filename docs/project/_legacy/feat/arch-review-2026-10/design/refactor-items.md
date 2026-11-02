# magicbook 重构项明细（B1–B8 + 未编号项 + 跨仓项本仓部分）

> 状态：任务清单（2026-10-15 建档，全部待启动；开工时按 `AGENTS.md` worktree 纪律逐项单独立项）
> 来源：家族根 [`architecture-review-2026-10-14.md`](../../../../../docs/architecture-review-2026-10-14.md) §2.2 / §3.2；编号 B1–B8 与原文一一对应。总表与波次见 [overview.md](overview.md)。

**通用验收底线（每项都适用，下文不再重复）**：开发态单测按两级闸门执行（新增/改动用例全绿 + 受影响模块相关测试文件）；发布态全量 `pytest tests/` 仅由用户显式指令触发；push `develop` 即上线，未经指令不得 push；拆分类任务（B1/B2/B4）交付后必须真机验收（worktree 干净检出 + 拷贝运行期文件整站验收，R144 先例）。

---

## B1 · 抽 `cps/moonwell/` 防腐层包（MoonWellClient）

> 状态：已完成（2026-10-15，分支 `refactor/r178-moonwell-client`，已 merge 本地 develop `9f7db964` 待验收；全量 549 passed 零失败；bridge 留守 B2，附带发现 get_comic 路由被游离三引号包死待用户确认，见 response R178）

- **严重度 / 波次 / 前置**：🔴 ｜ 波 2 ｜ 无
- **模式**：防腐层
- **现状问题**：防腐层本体住在 web.py——`_moonwell_proxy` / refresh / base_url / trace_id / system_token（`web.py:1480-1973`）全部在路由模块里，7 个模块反向 import 它（`opds.py:38`、`editbooks.py:418,531`、`kobo.py:52` 等）。且 `_moonwell_proxy` 返回形态不一致（失败二元组 / 成功三元组，`web.py:660` 注释自认），66 处调用靠「原样 return 不解包」的隐式契约——一旦解包即 ValueError→500 白页。
- **任务内容**：抽 `cps/moonwell/` 包，上述基建迁出为 `MoonWellClient`（统一返回形态，消灭二元组/三元组隐式契约）；收编 `oidc.py:154` 直连 exchange 与 `web.py:1952` refreshToken 旁路。
- **验收判据**：① 66 处代理调用改为显式契约（无「原样 return」隐式依赖）；② 7 个模块不再 import web；③ moon-well 代理链路回归（翻译/标记/详解/TTS/伴读冒烟）；④ 上游 merge 冲突面不升（diff 检查）。

## B2 · web.py 蓝图分域拆分

> 状态：**已完成**（2026-10-15，r181：94 条定制路由分四批迁出 cps/routes/{reading,credit,vocab,learning}.py（全部 <1000 行），web.py 3304→2299 行回归原版形状，endpoint 前后比对无丢失，全量 549 passed 零回归；getcomic 死字符串块同步清除路由激活；merge 本地 develop `3211f600` 待验收。上轮 r179 尝试的四类坑与方案记录见 response R179）

- **严重度 / 波次 / 前置**：🟠 ｜ 波 3 ｜ B1（防腐层先迁出，web.py 才能回归原版形状）
- **模式**：蓝图分域
- **现状问题**：web.py 3,452 行 / 139 路由，原版蓝图 + 全部定制代理路由 + 防腐层宿主三重身份；`web.py:1705` `_moonwell_book_finished_bridge`（107 行）业务编排（查库→检索→登记→置 FINISHED）写在路由层。
- **任务内容**：按域拆 `routes/reading|learning|credit|vocab.py`，web.py 回归原版形状；nce 的「子包 + 条件注册」（`main.py:96`）是现成样板；`_moonwell_book_finished_bridge` 业务编排下沉 service。
- **验收判据**：① 每文件 <1,000 行（波 3 判据）；② 路由行为零变化（139 路由清单比对）；③ 与上游的 merge 冲突面下降（以原版 diff 行数比对为证）。

## B3 · 声明式校验统一

- **严重度 / 波次 / 前置**：🟡 ｜ 未排（原波次表未覆盖） ｜ 建议 B1 后（schema 落位 `cps/moonwell/payload.py`）
- **模式**：声明式校验
- **现状问题**：三套校验体系并存（`web.py:639,811-861,1517-1532`）——`_b1_payload` 白名单、`_vt_positive_int`、annotation 逐条手写，约 300 行重复且不一致；另有 43 处 `get_json(silent=True)`、65 处手写 `jsonify({"success":False})`。
- **任务内容**：`_b1_payload` 白名单方案推广为 `cps/moonwell/payload.py` schema，替换逐条手写校验；`silent=True` 与手写错误响应在触及处顺手收敛。
- **验收判据**：① 新 payload schema 有契约测试（错误入参 → 结构化 4xx，不再静默 None）；② 触及路由的校验行为回归全绿。

## B4 · epub.js 按注释域拆 12 模块

> 状态：判据①达成（2026-10-15 批次 1–7，分支 `refactor/r183-epub-modules` @ worktree `../magicbook-arch-b5`，已 merge 本地 develop `72b97ad5` / `d25ac150` / `2b1437c7` / `cac5ed01` / `f1f01b8b` / `1ed7c73e` / `d2a00fff` 待验收；**epub.js 3,279→734 行（−77%）**，七个模块：core / word-detail / annotations / selection / immersive / ted-audio / tts。批次 7（朗读+连播 724 行）反向依赖只有章标题与阅读位置两个；顺带退役装配层侧的批次 1 薄委托（5 处调用改直连 `RC.*`）。**三道守卫**（模块全集静态锁 / 调用面 ⊆ 导出面 / 不得引用 epub.js 闭包内符号 + init 时序）合计逮到四处真缺陷，其中守卫自身的别名清单也曾漏了 RT/RTTS，已改为从 ALIASES 单一来源生成。全量 585→590 passed，七域各有无头 Chrome 探针。**剩余判据②③**（阅读器全功能真机回归、R172/R173 不回退）需线上整站验收；A/P 段（初始化、位置恢复、生词台账、书签、主题）可再拆 reader-location/reader-vocabulary，但 <1,000 判据已满足，是否继续由用户定夺。PingCode MAGICBOOK-2 `4X51sVcJ` In progress）

- **严重度 / 波次 / 前置**：🟠 ｜ 波 3 ｜ 无
- **模式**：门面拆模块
- **现状问题**：`cps/static/js/reading/epub.js` 3,279 行单 IIFE、141 函数、12+ 功能域混居，全仓最热文件（61 commits）——并行开发必然冲突。
- **任务内容**：按注释域拆 12 个模块，外露 `window.ReaderXxx` 命名空间（已有先例），epub.js 缩为装配层；拆完旧入口保留薄委托一个过渡期（家族总体原则 5）。
- **验收判据**：① 每文件 <1,000 行（波 3 判据）；② 阅读器全功能真机回归（段落译/整页译/整本译/朗读/连播/TED 原声/生词/伴读/批注）；③ R172/R173 已修缺陷不回退（TED 分流探测判据、bookListenToggle 链路）。

## B5 · 统一 API client【X1 本仓部分】

> 状态：开发中（2026-10-15，分支 `refactor/r177-unified-api-client`，已 merge 本地 develop `e750a739` 待验收；公共层落位 `cps/static/js/common/api.js`，全量 545 passed 零回归）

- **严重度 / 波次 / 前置**：🟠 ｜ **波 1（X1 三端合围）** ｜ 无
- **模式**：统一 API client
- **现状问题**：前端三套请求层——`learning-common.js:44-75` / `ai_chat.js:75` / `vocab-test.js:145-433`，CSRF 获取三份；解包与错误处理各自为政，行为漂移。
- **任务内容**：learning-common.js 的 httpJson / unwrapResult / csrfToken 提升为 `static/js/common/api.js`，ai_chat / vocab-test / credits 迁入；解包改为容错判定 + 失败在界面可见（静默降级是家族级反模式）。
- **验收判据**：① 三处调用方全部迁入公共层（CSRF 获取单点）；② unwrap 容错（非 Result 形态不再误判，与 moon-well M4 落地后的新形态兼容）；③ 失败可见（mock 接口故障时用户能看到错误提示而非「数据不存在」）；④ 与 moon-well M4、magiclens L1 联合验收（X1 判据：新增形制断言全绿）。

## B6 · JobServiceBase 模板方法（双胞胎去重）

> 状态：**已合入本地 develop**（2026-10-16，R186 `refactor/r186-job-service-base`；交付记录见
> [b6-job-service-base.md](b6-job-service-base.md)）。实测**不是双胞胎而是三胞胎**——`reading_word_detail/service.py`（R176）
> 是同形制的第三份拷贝，本批一并归一。判据①②达成（全量 603 passed + 13 例结构守卫 + 两处反向变异；交叉评审揪出三处「形状相似但判据被改」的问题，已落回原语义并各配用例），
> **判据③「整本翻译/整本朗读各跑一轮真机批次」待用户线上验收**。两条如实登记的边界：
> 进度字典与 item 状态机刻意不统一（会改前端契约）；花名册自愈只由朗读侧启用（给翻译/详解套上会
> 把「连点两次」从「再起一条」改成「静默跳过」，属行为变更）。

- **严重度 / 波次 / 前置**：🟠 ｜ 波 4 ｜ 无
- **模式**：模板方法
- **现状问题**：`reading_translation/service.py:82-519` ↔ `reading_tts/service.py:47-426` job/worker/progress/retry 结构逐一对称——同构双改风险（R169 整本朗读批次修复即双胞胎侧的事故形态）。
- **任务内容**：抽 `JobServiceBase`（start / progress / retry / cancel / worker 骨架），两个服务只留差异部分；R169 的自愈逻辑（停滞 + PENDING 重新 spawn）纳入骨架统一实现。
- **验收判据**：① 两服务既有测试全绿（含 R169 批次自愈用例）；② 重复骨架归一；③ 整本翻译与整本朗读各跑一轮真机批次回归。

## B7 · i18n 五步链生成化

> 状态：**已完成**（2026-10-15，r182：scripts/generate_i18n_seed.py + tests/i18n_js_files.json 生成物入库 + 契约测试适配；**手维护清单漏 3 文件的实证修复**；全量 549 passed；merge 本地 develop `8f4197c3` 待验收）

- **严重度 / 波次 / 前置**：🟡 ｜ 波 4 ｜ 无
- **模式**：生成化
- **现状问题**：`templates/i18n_seed.html:7` 手写 323 行种子字典 + `test_i18n_seed_contract.py:33` 手维护 JS_FILES 清单——五步链两处人肉环节，漏一步即静默英文回退。
- **任务内容**：改脚本扫描 `mbT()` 自动生成种子字典与 JS_FILES 清单（生成物替代手写清单，波 4 判据）。
- **验收判据**：① 生成物与现手写内容一致（迁移期比对）；② i18n 契约测试改跑生成清单全绿；③ 新增一个 `mbT()` 调用不再需要手改清单。

## B8 · MoonWellConfig 配置收口

- **严重度 / 波次 / 前置**：🟡 ｜ 未排（原波次表未覆盖） ｜ 无
- **模式**：配置收口
- **现状问题**：配置散落 `constants.py:142` / `web.py:1505` / `oidc.py:150`——无单一出口。
- **任务内容**：`MoonWellConfig` 集中封装；配 `.env.example` 契约测试（键集合一致，防漂移）。
- **验收判据**：① 三处散落配置收敛为一个出口；② `.env.example` 契约测试全绿。

---

## 未编号项（报告 §3.2 列明但未入 B1–B8 编号主体，如实登记）

- **代理返回形态不一致（🔴，B1 核心标的）**：`web.py:660` 注释自认的失败二元组/成功三元组问题——已并入 B1 任务内容与验收判据，不单独立项。
- **路由层业务编排（🟠）**：`_moonwell_book_finished_bridge` 107 行——已并入 B2 任务内容。
- **`silent=True` 与手写错误响应（🟡）**：43 处 `get_json(silent=True)`、65 处手写 `jsonify({"success":False})`——已并入 B3 任务内容，触及处收敛。

## 跨仓项本仓部分

### X2 · 镜像向量锁（三组镜像）

- **严重度 / 波次**：🟠 ｜ 波 4（与 moon-well、magiclens 同窗口）
- **现状问题**：与 magiclens 近逐行同构 ×3——TTS fallback（`epub.js:469-506` ↔ `content.js:413-454`）、详解六板块渲染（`epub.js:607-801` ↔ `content.js:548-633`）、SSE 帧解析（`ai_chat.js:387-430` ↔ `chat.js:280-314`）——三端镜像无机器锁，R16/R24 类漂移 bug 必复发。
- **任务内容**：与 magiclens L7 共建共享断言向量：JSON 用例同源（放各仓 tests），本仓侧三组镜像逻辑跑同一份向量断言。
- **验收判据**：向量用例两端同源一致，任一端漂移即测试红灯。

---

## 状态回填约定

每项开工 / 完成 / 验收时：① 回填本节各条目下方一行 `状态：待启动 → 开发中（日期，分支）→ 已上线（日期，commit）`；② 同步 [overview.md](overview.md) 总表「状态」列。
