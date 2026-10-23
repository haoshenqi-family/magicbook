# AC — R214 书籍详情（三子项验收标准）

> 状态：**定稿（2026-10-23 用户复核通过）**，随开发逐条勾选；拍板⑦：AI 简介无「重新生成」按钮（B2/B4 的标注口径不变）
> 关联：[hld.md](../hld.md) · [lld.md](../lld.md) · 需求基线 [`product/library/requirements.md`](../../../../../product/library/requirements.md) §2 R214
> 回归视口：桌面 1440×900 · 移动 390×844（对应 QA 报告 §四 截图 `a2-book-detail.png` 重拍对比）
> 拍板口径六条见 HLD §7；本文件只写「怎么算过」，不重复方案。

## A · 基础信息与元数据修正（含阅读入口解禁）

- [ ] **A1** GIVEN 普通读者（非 admin）WHEN 打开任意书籍详情页 THEN **能看到「在线阅读」及格式下拉**；看不到「整本任务」「生成简介」等管理员元素（守卫测试钉住「在线阅读不在 `role_admin()` 条件内」，反向变异移回去必须报红）
- [ ] **A2** GIVEN 管理员 WHEN 打开详情页 THEN 「编辑元数据 / 取消」收进「管理员工具」分组，与读者操作区视觉分离
- [ ] **A3** GIVEN 书的 `pubdate` 与入藏 `timestamp` 相差 ≤1 天 WHEN 看详情 THEN 显示「导入于 YYYY-MM-DD」（tooltip 说明判定依据），**不显示伪造出版日**；相差 >1 天则照常显示「出版于 …」（单测覆盖两分支）
- [ ] **A4** GIVEN EPUB 的 OPF 声明 `dc:language` 为 `eng` + `chi` WHEN 导入 THEN 书目语言落两种，详情页语言行显示两种语言并带「双语」徽标（导入回归：改回只取第一条 → 报红）
- [ ] **A5** GIVEN 存量书目语言缺失/单边 WHEN 运行 `scripts/backfill_languages.py`（默认 dry-run）THEN 只输出「book_id | 现状 | OPF 声明」差异清单、不写库；`--apply` 才写，且执行前自动备份 `metadata.db`，**不动 EPUB 文件**
- [ ] **A6** GIVEN 书的难度来源 WHEN 看详情 THEN 按四级兜底显示难度标签：① 标签 `阶N` ② 书架名 `阶N` ③ 系列映射（如 `书虫·第N级`）④ 都没有显示「未分级」；与 R213 分级推荐同一解析器、同一本书两处结论一致
- [ ] **A7** GIVEN 书已在某书架 WHEN 看详情 THEN 已加入的书架显示为可移除 chip（含 ✕），与「加入书架」按钮**视觉可分**（对照 QA 截图原状逐项对比）

## B · 内容速览（简介 / 目录 / 试读）

- [ ] **B1** GIVEN 书目自带简介（comments 非空）WHEN 看详情 THEN 显示原文且**无任何标注**（不套 AI 框）
- [ ] **B2** GIVEN 无自带简介但已生成 AI 简介 WHEN 看详情 THEN 显示摘要正文 + 明确标注「由 AI 生成 · `<model>` · `<generatedAt>`」（守卫测试钉住标注存在，防被删）
- [ ] **B3** GIVEN 两者皆无 WHEN 看详情 THEN 显示「暂无简介」并指向目录与试读；**不自动生成、不伪造**
- [ ] **B4** GIVEN 管理员 WHEN 点「生成简介」THEN 产出 120–200 字中文简介并落 `book_insight`，对所有读者可见；生成入口仅管理员可见；非管理员触发返回 403（守卫）
- [ ] **B5** GIVEN AI 简介上游失败 WHEN 生成 THEN 简介区块内红字显示上游原始 message，**不静默降级成「暂无简介」**、不写 `ai_summary`（守卫）
- [ ] **B6** GIVEN 任意 EPUB WHEN 看详情 THEN 目录树渲染章节（nav.xhtml / toc.ncx，取不到退化按 spine 文件），显示每章段数，默认前 8 章 + 「展开全部」；点击章节展开该章首段摘录（不离开页面）
- [ ] **B7** GIVEN 任意 EPUB WHEN 看详情 THEN 首章试读显示 ≤1200 字、带淡出遮罩与「继续阅读」按钮，点击进入阅读器
- [ ] **B8** GIVEN 单本解析失败或 >8MB 大书 WHEN 打开详情 THEN 页面不 500：失败区块单独显示「解析失败：<原因>」（`last_error` 落库），大书只出目录与统计不出摘录，其余区块正常

## C · 整本任务统一入口 + 代价面板

- [ ] **C1** GIVEN 普通读者 WHEN 看详情 THEN **看不到「整本任务」按钮**（拍板①：仅管理员）；管理员可见「在线阅读」主按钮 + 「整本任务」次按钮（守卫）
- [ ] **C2** GIVEN 管理员 WHEN 点「整本任务」THEN 打开模态，三个 Tab（整本翻译 / 整本朗读 / 全文单词详解）各一张同构代价卡：量 → 不修改原文件 → 覆盖率 → 耗时 → 积分 → 开始按钮
- [ ] **C3** GIVEN 任一 Tab WHEN 看代价卡 THEN 固定行「**不修改原文件，结果存缓存**」（事实口径，HLD §2-⑦）
- [ ] **C4** GIVEN 翻译 Tab WHEN 查覆盖率 THEN 显示「已缓存 X / 共 Y 段」（来自 `find-translations`）；朗读 Tab 显示「按全 miss 上限估算，已缓存段落自动跳过不重复计费」（拍板③，无批量探针）；lookup 失败显示「缓存命中暂不可得」，**不显示 0**（守卫）
- [ ] **C5** GIVEN 有 ≥3 个同类历史批次（单位数 ≥30）WHEN 估耗时 THEN 显示「约 X 小时 Y 分 · 基于最近 N 个批次实测」；样本不足则回落常量并**明写「按常量估算」**
- [ ] **C6** GIVEN moon-well 费率端点可用 WHEN 看积分行 THEN 显示「约 N 积分（粗算，非账单）」+ 上限；端点不可用 THEN 显示「费率暂不可得」并给出字符/token 量，**不猜数字**（守卫：不允许出现估算积分与 `known:false` 并存）
- [ ] **C7** GIVEN 点「开始整本翻译」WHEN 提交前 THEN 必须二次确认，确认文案含预计耗时与积分；确认后调既有 start 端点，模态关闭、页面顶部出现进度条 `done/total` + 上次更新时间
- [ ] **C8** GIVEN 已有活跃批次 WHEN 加载详情页 THEN 「整本任务」按钮直接进进度态（不显示「开始」），轮询按既有口径（翻译 4s / 朗读 5s / 详解 30s），COMPLETED 后停止轮询
- [ ] **C9** GIVEN 三个既有 job 端点 WHEN 面板调用 THEN 一个都不改形制（起批/进度/重试/取消 全部复用）；新增文案进 i18n 种子，`test_i18n_seed_contract` 全绿

## 全局

- [ ] **G1** 1440×900 与 390×844 两档截图与 QA 报告 `a2-book-detail.png` 原截逐项对比：无裁切、无横向滚动、新区块排版不破
- [ ] **G2** 文档回填完成：需求基线 §2 R214 条目、L2 契约（`/ajax/credit/billing`、`book-intro`）、LLD 状态行、plan.md 状态列
- [ ] **G3** `tests/test_book_detail_r214.py` + `tests/test_epub_languages.py` 全绿；既有全部测试文件无回归（尤其 `test_no_duplicate_js_lines.py`、`test_i18n_seed_contract.py`）
- [ ] **G4** moon-well R207（费率 + book-intro）未就绪时：C 子项可先行 merge（积分行走「费率暂不可得」分支、AI 简介按钮置灰并说明），R207 到位后无需改接口形制
- [ ] **G5** 拍板遗留两项（HLD §7）在验收前给结论：① AI 简介是否保留「重新生成」按钮；② 语言补正 dry-run 清单出来后，书虫那批的执行范围
