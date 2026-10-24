# 首页信息架构 `/home`（L3 实现说明）

> 建立：2026-10-24（R213-C / MB-18）。读者是**要改这个首页的人**——这里只讲实现与边界，
> 「首页长什么样、能做什么」见 L1 [`product/readme/library.md`](../../readme/library.md)；
> 「这一次怎么做的、被否的方案」见 LLD
> [`project/iterations/1.0/r213-home-ia/lld.md`](../../../project/iterations/1.0/r213-home-ia/lld.md)。

## 1. 组成与落点

| 块 | 取数 | 失败时 |
| --- | --- | --- |
| 继续阅读 | 服务端 `web.recent_reading()`（R213-B 的 `reading_progress` 表） | 空列表 → 整块不渲染 |
| 今日计划 | 前端 `home.js` 并行拉 `/ajax/learning/plan/today` + `/ajax/learning/writing/history` | 单块失败只让该数字显示 `–`，两块都失败整卡降级为「今日学习页」提示 |
| 按难度阶推荐 | 服务端 `routes/home.py::level_recommendations()`（规则化，无算法） | 空列表 → 整块不渲染 |
| 随机发现 | 服务端 `random_discover_books()`（`generate_linked_query` + `common_filters`） | 空列表 → 整块不渲染 |

- 路由：`GET /home`，`@user_login_required`（匿名跳登录）。
- 落点开关：`settings.config_home_landing`（Boolean，默认 `True`）。判据集中在
  `cps/landing.py::landing_endpoint()`，被四处消费：登录页 `next` 默认值、本地登录成功、
  OIDC `oidc_next` 默认值、已登录再访问登录/注册页。**只有这一个判据**，改口径只改这里。
- 模板：`cps/templates/home.html`；卡片宏 `cps/templates/partials/_book_card.html`
  （与 `index.html` 共用，见 §4）。

## 2. 「今日计划」两个数字的口径（别改错）

| 数字 | 来源 | 为什么是它 |
| --- | --- | --- |
| 待复习词数 | `plan/today` 的 **`reviewTotal`** | 与 `/learning` 页 `srs/stats.dueNow` 是**同一个** `countDueBetween(MIN, now)` 查询。**不要用 `reviews.length`**：`reviews` 被 `dailyMinutes` 推出的上限截断，会把「到期 40」显示成「到期 20」 |
| 写作待办篇数 | `writing/history` 里 `createdAt` 落在今日、且 `lastDraftNo == null` 的条数 | `null` = 出题后一稿未写（moon-well `WritingVO.HistoryItem` 既有字段）；不新增后端字段 |

- `createdAt` 是 Java `LocalDateTime.toString()`（`2026-10-24T15:30:00`，**无时区**），
  `home.js` 按浏览器本地时间解析——「今天」是用户视角的今天。
- 文案不走 `mbT()`：全部由模板 `_()` 注入 `data-*`，JS 只填数字。这样多语言只有一个入口，
  也不会往 i18n 种子里留「词条漏登记 → 静默回退英文」的面。

## 3. 按难度阶推荐：归阶规则

- 解析式：`^(?:分级)?阶\s*(\d+)`，如 `阶1` / `阶 2` / `分级阶3` / `阶3 桥梁书`。
  **刻意不锚定结尾**（真实书架名常带副标题）；**刻意窄**（`第一阶段` 不算阶 1）。
- 归阶：同阶多个书架的书**合并去重**（按 book id）；解析不出阶号的书进「未分级」尾组，
  **不隐藏**。
- 排序：按阶号**数字**升序（`阶2` 在 `阶10` 前）。
- 取书：每阶排除已读完（`ReadBook.read_status == FINISHED`），随机抽 `HOME_LEVEL_PICKS`（6）本，
  再逐本 `get_filtered_book`（书被删/无权看即跳过）。**不把整阶的 ORM 对象全查出来**。
- 性能：书架 1 查 + 关联 1 查 + 已读 1 查，然后至多 `阶数 × 6` 次主键查询；禁止「每阶一次查询」。

## 4. 卡片只有一份实现

`partials/_book_card.html::book_card()` 被 `index.html`（随机区 / 列表区）与 `home.html`
（继续阅读 / 分级推荐 / 随机发现）共用。差异全部走参数：`read_flag` / `show_badges` /
`card_id` / `modal` / `music_icon` / `series_plain` / `href`（+ `caller()` 追加区）。

**改卡片样式就改宏**——曾经随机区加了格式徽标、列表区一直没加，就是复制两份的直接后果
（由 `tests/test_home_nav_shell.py` 与 `tests/test_home_route.py` 的模板守卫钉住）。

## 5. 边界与坑

| 场景 | 行为 |
| --- | --- |
| 老库没有 `config_home_landing` 列 | `ub.migrate_home_landing_config()` 启动时 `ALTER TABLE settings ADD COLUMN ... DEFAULT 1`；缺列时任何配置读取都会 500，所以**迁移必须存在**，不能只靠默认值 |
| moon-well 慢 / 重启 | 首页照常打开，只有今日计划卡等它；今日计划**不参与服务端渲染** |
| 匿名访问 `/home` | 302 到 `/login`，不返回任何书目 |
| 用户没读过任何书 | 继续阅读整块不渲染，首屏从今日计划开始 |
| 书架里没有「阶N」命名 | 只有「未分级」尾组，或整块不渲染（一本书都没有时） |
| 有书在读但格式是 CBR/CBZ | 仍在继续阅读里（进度回传未接 CBR，卡片只显示书名与封面，点开进详情页链路） |

## 6. 测试

```bash
pytest tests/test_home_route.py -q          # 落点开关 / 空态 / 归阶规则 / 卡片渲染 / 迁移幂等
pytest tests/test_home_nav_shell.py -q      # 卡片徽标与外壳的接线守卫（断言已指向共享宏）
```

守卫要点：`/home` 登录门禁、空块不渲染、`阶10` 不排在 `阶2` 前、已读完不进推荐、
落点开关关闭后回退 `/`、迁移可重复执行、模板不自带第二份卡片实现。
