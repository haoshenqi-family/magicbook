# AC — R213 首页信息架构（三子项验收标准）

> 状态：**A 除侧边栏分组外已上线 / B 已验收 / C 已开发待验收**（2026-10-24 更新；原为 2026-10-23 草案）
> 关联：[hld.md](../hld.md) · [lld.md](../lld.md) · 需求基线 [`product/library/requirements.md`](../../../../../product/library/requirements.md)
> 回归视口：桌面 1440×900 · 移动 390×844（对应 QA 报告 §三 / §八 截图重拍对比）
>
> **勾选口径**：本文件只对「本轮交付的那一段」勾选并留判据落点。A 段除 A1 外已随 MB-16 上线
> （2026-10-23 `05587241`）、B 段已随 MB-17 验收通过，但它们的勾选归属**各自结项轮次**（记录在
> [`../../plan.md`](../../plan.md) MB-16 / MB-17 行），本文件不代勾——代勾等于替别人宣布验收结论。

## A · 导航与外壳

> A 段证据位置：交付 `05587241`（chips 文字 / 格式徽标 / 搜索合并 / 移动底栏 / 裁切修复）+
> `3c2c6a6d`（高级搜索「阅读状态」四态化）；守卫 `tests/test_home_nav_shell.py`、
> `tests/test_adv_search_read_status.py`。

- [ ] **A1** GIVEN 任意登录用户 WHEN 看侧边栏 THEN 10 个书架按「书架/分级/媒体/系统」四组显示，每组带计数，**没有任何书架丢失**（总数与改造前一致）
  - **本迭代不实施**：用户 2026-10-24 拍板「A 的侧边栏分组这个迭代不改，下个迭代再说」。设计保留在 [lld.md](../lld.md) §5（不删不实现），`Shelf.kind` 判定留待下迭代开工时拍板（HLD §7.1）。本条**不勾，不是缺口**
- [ ] **A2** GIVEN 视口 1440×900 WHEN 打开任意页 THEN 「创建书架」按钮完整可见、可点击，无被裁切
- [ ] **A3** GIVEN 窄屏 390×844 WHEN 看筛选区 THEN 11 个 chips 收进「筛选」抽屉且每项有文字；桌面端 11 个 chip 均带文字标签
- [ ] **A4** GIVEN 书库列表 WHEN 看任意卡片 THEN 能区分 EPUB / PDF / TED 音频 / 视频（音频与视频卡显示时长；已缓存原声有标识）
- [ ] **A5** GIVEN 顶栏 WHEN 使用搜索 THEN 只有一个搜索入口；高级筛选从该入口展开，无并排重复的第二个「搜索」按钮
- [ ] **A6** GIVEN 移动端 390×844 WHEN 在任意一级页 THEN 底部常驻「书架 / 学习 / 我的」，正文不被遮挡、无横向滚动
- [ ] **A7** GIVEN 高级搜索页 WHEN 看「阅读状态」THEN 只有「不限 / 未读 / 在读 / 已读」四项，附一行中文说明；选「未读」能筛出**从没打开过**的书；旧链接带 `read_status=True/False` 打开不报错且语义不变

## B · 继续阅读

> B 段证据位置：交付 `0dccef16` / `420a6c48`（已上线），MB-17 用户 2026-10-23 真机确认「继续阅读可以了」；
> 守卫 `tests/test_reading_progress.py`、`tests/test_reading_progress_wiring.py`。
>
> ⚠ **B6 待核（2026-10-24 发现）**：仓库内查无 `reading_progress_enabled` 这个开关——`grep` 在 `cps/`、
> `tests/` 里都没有命中，`_Settings`（`cps/config_sql.py`）也没有对应列。也就是说「关闭即回退到 epub.js
> 本地位置」这条**根本没做过 kill switch**，进度上报是常开的。B6 因此**不勾**，且本次不擅自补开关（属 MB-17
> 范围，不是 R213-C）：留给 MB-17 结项时确认是「补开关」还是「把判据改成『上报失败不阻塞阅读』」。
> 注：B2–B5 的守卫（唯一约束 / csrf / percent 夹取 / 书被删跳过）在 `test_reading_progress.py` 里确有对应用例
> （`test_report_creates_and_upserts`、`test_invalid_payload_rejected`、`test_percent_clamped`、
> `test_recent_reading_skips_finished_and_missing`），但这不改变它们归属 MB-17 结项轮次勾选的口径。
- [ ] **B1** GIVEN 用户读到 37/125 页退出 WHEN 次日从任意设备登录 THEN 首页「继续阅读」第一张卡显示该书与 `37/125`，一步点击回到原位（≤3 步满足需求验收②）
- [ ] **B2** GIVEN 同一用户同一本书 WHEN 上报两次进度 THEN `reading_progress` 只有一行（唯一约束生效），`last_read_at` 取最新
- [ ] **B3** GIVEN 进度上报缺少/错误 `csrf_token` WHEN 提交 THEN 返回 4xx 且库中无新增行（守卫）
- [ ] **B4** GIVEN `percent` 传 150 或 -5 WHEN 上报 THEN 落库被夹到 0–100（守卫）
- [ ] **B5** GIVEN 书已被删除 WHEN 加载首页 THEN 继续阅读不显示该书，页面不报 500（守卫）
- [ ] **B6** GIVEN 关闭 `reading_progress_enabled` WHEN 阅读 THEN 行为回到改造前（epub.js 本地位置），无任何库写入

## C · 今日计划 + 分级推荐

> 状态：**已开发待验收**（2026-10-24）。证据：`feat/r213-home-ia`（基线 `origin/develop` `a3515312`），
> 全量 `pytest tests/` **873 passed / 0 failed**；新增 `tests/test_home_route.py` 27 例。
> **本段勾选含义＝「开发完成且判据落点有自动化守卫」**；仍需真机跑的行内标「真机待 G1」，不冒充已验收。

- [x] **C1** GIVEN 登录用户 WHEN 打开 `/home` THEN 首屏依次可见「继续阅读 / 今日计划 / 分级推荐 / 随机发现」四块（空数据块隐藏，不出现空白骨架残留）
  - 落点：`cps/templates/home.html` 四段各带 `{% if %}`；判据 `test_home_hides_empty_sections`、`test_home_renders_cards_through_shared_macro`
- [x] **C2** GIVEN moon-well 正常 WHEN 看今日计划卡 THEN 显示「待复习 n 词 · 写作 m 篇」，数值与 `/learning` 页一致（同源，不允许两处口径不同）
  - 落点：`cps/static/js/home.js` 取 **`reviewTotal`**（不是 `reviews.length`——会被 `reviewCap` 截断，见 lld §4.3 第一行修正）
  - 同源已由源码级核实：`LearningPlanService.today().reviewTotal` 与 `ReviewService.stats().dueNow` 同为 `countDueBetween(userId, MIN.withYear(1), now)`，数值恒等
  - **真机待 G1**：两页数字对拍属验收动作，无跨仓自动化测试
- [x] **C3** GIVEN moon-well 不可用 WHEN 打开 `/home` THEN 仅今日计划卡降级为「暂不可用 + 去学习页」，其余三块正常（不整页白屏）
  - 落点：`home.js` 两个请求各自 `catch`，两块都失败才换 `data-text-unavailable` 文案；服务端零依赖（今日计划不走 SSR）
  - 守卫：`home-plan-degraded` 类 + 文案 data 属性钉住；`test_home_js_passes_text_through_data_attributes`、`test_home_template_compiles`
  - **真机待 G1**：需在 moon-well 停服态下实看
- [x] **C4** GIVEN 用户有名为「阶1」「分级阶2」… 的书架 WHEN 看分级推荐 THEN 每阶给出未读书目（不含已读完的书），同阶多书架合并、按阶号**数字**升序（`阶10` 必须排在 `阶2` 之后），解析不出阶号的书归「未分级」尾组而非消失
  - 落点：`cps/routes/home.py` 的 `level_of_shelf` / `group_book_ids_by_level` / `level_recommendations`
  - 守卫：`test_level_of_shelf`（10 组参数，含 `阶10`≠`阶1`）、`test_group_merges_same_level_and_keeps_unleveled`、`test_level_picks_numeric_order_and_finished_excluded`、`test_level_picks_skips_missing_books`、`test_level_picks_empty_when_no_level_shelf`
- [x] **C5** GIVEN 匿名访问 THEN `/home` 跳登录页，不泄露任何数据（守卫）
  - 落点：`@user_login_required`；守卫 `test_home_requires_login`
- [x] **C6** GIVEN 登录成功 WHEN 落点 THEN 直接进入 `/home`（`config_home_landing` 默认 `true`）；置 `false` 后重登回原 `/` 发现页（可回退）
  - 落点：`cps/landing.py::landing_endpoint()` 单点，四处消费（登录页 `next` 默认 / 本地登录成功 / OIDC `oidc_next` / 已登录再访问登录页）
  - 守卫：`test_landing_defaults_to_home`、`test_landing_falls_back_when_disabled`、`test_login_page_next_defaults_to_home`、`test_login_page_next_defaults_to_index_when_disabled`、`test_login_post_lands_on_home`
  - 迁移：`ub.migrate_home_landing_config()` 给既有库补列（缺列＝每次读配置 `OperationalError`＝整站 500，故迁移属功能的一部分）；守卫 `test_migration_is_idempotent`

## 全局

- [ ] **G1** 1440×900 与 390×844 两档截图与 QA 报告原截逐项对比，无裁切、无横向滚动
  - **待用户真机执行**（验收动作，不属单测）。C2 的两页数字对拍、C3 的停服降级态一并在这一档看
- [x] **G2** 文档四问回填完成：L1（library / reading）、L2（新增端点）、L3（home-ia / reading-progress）、LLD 状态行
  - 本轮 R213-C 实际回填：L1 `docs/product/readme/library.md`「能做什么」首条 + 深入阅读链；L2 无新增对外契约端点（`/home` 是页面路由、`/ajax/learning/*` 为既有代理端点，`config_home_landing` 属站点配置非 API 契约），故不新建 L2 条目并在 lld §4.3 记录该判断；L3 新建 `docs/product/library/features/home-ia.md`（六节）；LLD 状态行 + §4.3 实现结果 + §4.4 验收对应
- [x] **G3** 单测 + 集成 + 守卫测试全绿；`pytest` 既有用例无回归
  - 2026-10-24 全量 `pytest tests/` = **873 passed / 0 failed**（含 R214-C 全部用例）
  - 注：`test_home_nav_shell.py::test_cover_format_badges_present` 与 `test_onboarding_tour.py::test_browse_step_anchors_exist_in_templates` 两条断言随卡片宏迁移**有意改判据落点**（断言从 `index.html` 源码移到 `partials/_book_card.html`，并各加一条「`index.html` 必须 import 该宏」的更强约束）——是结构变更的结果，不是放宽
