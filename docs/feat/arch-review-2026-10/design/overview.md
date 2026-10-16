# magicbook 架构评审任务拆分（2026-10）

> 状态：任务清单（2026-10-15 建档，全部待启动；本轮仅登记任务，未做任何开发）
> 来源：家族根 [`architecture-review-2026-10-14.md`](../../../../../docs/architecture-review-2026-10-14.md) §2.2（B1–B8）、§3.2（严重度标记）、§2.5（X1/X2 本仓部分）、§2.7（波次）；跨仓协同总账见家族根 [`arch-review-2026-10-tasks-crossrepo.md`](../../../../../docs/arch-review-2026-10-tasks-crossrepo.md)
> 建档：2026-10-15（`requests.md` R174）。开工时逐任务按 `AGENTS.md` worktree 纪律单独立项（一任务一分支），本清单不整包启动。

## 一、本目录文档

| 文档 | 内容 |
| --- | --- |
| [overview.md](overview.md) | 本文件：任务总表、波次依赖、跨仓协同、执行纪律 |
| [refactor-items.md](refactor-items.md) | 编码类重构项 B1–B8 + §3.2 未编号项 + 跨仓项 X2 本仓部分（开工需 worktree） |
| [doc-fixes.md](doc-fixes.md) | 文档修正项 DF1–DF8（纯文档活，主检出可直接做，无需 worktree） |

## 二、任务总表

（「状态」列随开工 / 验收回填；编号与家族根评审报告一一对应，便于回溯原文。）

| ID | 任务 | 类型 | 严重度 | 波次 | 前置依赖 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| B5 | 统一 API client：httpJson/unwrapResult/csrfToken 提升为公共层（X1 本仓部分） | 编码 | 🟠 | **波 1（X1 三端合围）** | 无 | 开发中（r177，待验收） |
| B1 | 抽 `cps/moonwell/` 防腐层包（MoonWellClient 收编代理基建） | 编码 | 🔴 | 波 2 | 无 | 已完成（r178，待验收） |
| B2 | web.py 蓝图分域拆分（routes/reading\|learning\|credit\|vocab） | 编码 | 🟠 | 波 3 | B1（防腐层先迁出 web.py）；**前置已清（R180）** | **已完成**（r181：94 路由分四批迁出，endpoint 无丢失，全量 549 passed，merge 3211f600 待验收） |
| B4 | epub.js 按注释域拆 12 模块，缩为装配层 | 编码 | 🟠 | 波 3 | 无 | 进行中（r183 批次 1–6：六个 reader-* 模块，epub.js 3,279→**1,449**（−56%），全量 590 passed，新增「跨模块调用面 ⊆ 导出面」+「不得引用 epub.js 闭包内符号」两道守卫（拆解过程据此逮到三处真缺陷）；余 TTS 簇与装配层收尾，PingCode MAGICBOOK-2） |
| B6 | reading_translation / reading_tts 双胞胎抽 JobServiceBase | 编码 | 🟠 | 波 4 | 无 | 待启动 |
| B7 | i18n 五步链生成化（脚本扫描 `mbT()` 自动生成种子字典与 JS_FILES） | 编码 | 🟡 | 波 4 | 无 | **已完成**（r182：脚本 + 生成清单入库 + 契约测试适配，549 passed，merge 8f4197c3 待验收） |
| B3 | 声明式校验：`_b1_payload` 白名单推广为 payload schema | 编码 | 🟡 | 未排（原波次表未覆盖） | 建议 B1 后（schema 落位 cps/moonwell/） | 待启动 |
| B8 | MoonWellConfig 配置收口 + `.env.example` 契约测试 | 编码 | 🟡 | 未排（原波次表未覆盖） | 无 | 待启动 |
| X2 | 镜像向量锁本仓部分（TTS fallback / SSE 解析 / 详解六板块渲染） | 测试 | 🟠 | 波 4 | 与 moon-well / magiclens 同窗口 | 待启动 |
| DF1–DF8 | 文档修正（状态滞留 / 数值冲突 / 悬空索引 / 待决策 / 卫生） | 文档 | — | 数值类随波 0，其余未排 | 无 | 待启动 |

> 波次口径引自报告 §2.7：波 1（契约 X1：M4+B5+L1）→ 波 2（防腐/门面：B1）→ 波 3（巨石拆分：B2/B4）→ 波 4（生成与治理：B7/B6）。B3 / B8 未入原波次表，属本拆分文档如实标注的「未排」项，开工顺序由用户定夺。

## 三、跨仓协同项（本仓承担部分）

| 项 | 内容 | 协同仓 | 落地窗口 |
| --- | --- | --- | --- |
| X1 契约治理三端合围 | 本仓 **B5**（统一解包：api.js 公共层，解包容错 + 失败可见） | moon-well **M4**（包装兜底）、magiclens **L1**（rpc 门面） | 波 1 同一窗口（R44/R173 类事故从「三端各自防御」变「两端机制 + 一端可见」） |
| X2 镜像向量锁 | TTS fallback（`epub.js:469-506` ↔ magiclens `content.js:413-454`）、SSE 帧解析（`ai_chat.js:387-430` ↔ magiclens `chat.js:280-314`）、详解六板块渲染（`epub.js:607-801` ↔ magiclens `content.js:548-633`）三组镜像 | magiclens L7、moon-well（词形还原向量） | 波 4 |
| X3 词汇标度统一（显示侧） | band 唯一标度落地后，本仓展示层跟进（HardLevel 仅作显示皮肤） | moon-well 主责 | 未排，随 moon-well X3 |

## 四、执行纪律（引用本仓 `AGENTS.md`，不复制细则）

1. **worktree**：编码类任务开工即建 `../magicbook-<slug>`（从 `origin/develop` 最新点切出）；一次会话一个 worktree；merge 后保留待验收；`.venv` 复用主检出（`../magicbook/.venv/bin/python -m pytest`）。
2. **两级单测闸门**：开发态部分单测（新增/改动用例全绿 + 受影响模块）；发布态全量 `.venv/bin/python -m pytest tests/` 仅由用户显式指令触发——**push `develop` 即触发 fnOS 构建自动上线**，本清单任何任务未经用户指令不得 push。
3. **web.py / epub.py 拆分专项约束**：本仓是 Calibre-Web 定制副本，B1/B2 拆分必须以「上游 merge 冲突面下降」为第一判据（报告 §2.2 B2 的立项目标）；nce 的「子包 + 条件注册」（`main.py:96`）是现成样板。
4. **状态回填**：每任务完成即回填本文件总表「状态」列与 `refactor-items.md` 对应小节的状态行；L3 design 头部状态行按三级联动纪律回填。
