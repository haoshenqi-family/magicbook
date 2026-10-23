# AC — R213 首页信息架构（三子项验收标准）

> 状态：草案（2026-10-23），随 HLD/LLD 定稿后逐条勾选
> 关联：[hld.md](../hld.md) · [lld.md](../lld.md) · 需求基线 [`product/library/requirements.md`](../../../../product/library/requirements.md)
> 回归视口：桌面 1440×900 · 移动 390×844（对应 QA 报告 §三 / §八 截图重拍对比）

## A · 导航与外壳

- [ ] **A1** GIVEN 任意登录用户 WHEN 看侧边栏 THEN 10 个书架按「书架/分级/媒体/系统」四组显示，每组带计数，**没有任何书架丢失**（总数与改造前一致）
- [ ] **A2** GIVEN 视口 1440×900 WHEN 打开任意页 THEN 「创建书架」按钮完整可见、可点击，无被裁切
- [ ] **A3** GIVEN 窄屏 390×844 WHEN 看筛选区 THEN 11 个 chips 收进「筛选」抽屉且每项有文字；桌面端 11 个 chip 均带文字标签
- [ ] **A4** GIVEN 书库列表 WHEN 看任意卡片 THEN 能区分 EPUB / PDF / TED 音频 / 视频（音频与视频卡显示时长；已缓存原声有标识）
- [ ] **A5** GIVEN 顶栏 WHEN 使用搜索 THEN 只有一个搜索入口；高级筛选从该入口展开，无并排重复的第二个「搜索」按钮
- [ ] **A6** GIVEN 移动端 390×844 WHEN 在任意一级页 THEN 底部常驻「书架 / 学习 / 我的」，正文不被遮挡、无横向滚动

## B · 继续阅读

- [ ] **B1** GIVEN 用户读到 37/125 页退出 WHEN 次日从任意设备登录 THEN 首页「继续阅读」第一张卡显示该书与 `37/125`，一步点击回到原位（≤3 步满足需求验收②）
- [ ] **B2** GIVEN 同一用户同一本书 WHEN 上报两次进度 THEN `reading_progress` 只有一行（唯一约束生效），`last_read_at` 取最新
- [ ] **B3** GIVEN 进度上报缺少/错误 `csrf_token` WHEN 提交 THEN 返回 4xx 且库中无新增行（守卫）
- [ ] **B4** GIVEN `percent` 传 150 或 -5 WHEN 上报 THEN 落库被夹到 0–100（守卫）
- [ ] **B5** GIVEN 书已被删除 WHEN 加载首页 THEN 继续阅读不显示该书，页面不报 500（守卫）
- [ ] **B6** GIVEN 关闭 `reading_progress_enabled` WHEN 阅读 THEN 行为回到改造前（epub.js 本地位置），无任何库写入

## C · 今日计划 + 分级推荐

- [ ] **C1** GIVEN 登录用户 WHEN 打开 `/home` THEN 首屏依次可见「继续阅读 / 今日计划 / 分级推荐 / 随机发现」四块（空数据块隐藏，不出现空白骨架残留）
- [ ] **C2** GIVEN moon-well 正常 WHEN 看今日计划卡 THEN 显示「待复习 n 词 · 写作 m 篇」，数值与 `/learning` 页一致（同源，不允许两处口径不同）
- [ ] **C3** GIVEN moon-well 不可用 WHEN 打开 `/home` THEN 仅今日计划卡降级为「暂不可用 + 去学习页」，其余三块正常（不整页白屏）
- [ ] **C4** GIVEN 用户有名为「阶1」「分级阶2」… 的书架 WHEN 看分级推荐 THEN 每阶给出未读书目（不含已读完的书），同阶多书架合并、按阶号**数字**升序（`阶10` 必须排在 `阶2` 之后），解析不出阶号的书归「未分级」尾组而非消失
- [ ] **C5** GIVEN 匿名访问 THEN `/home` 跳登录页，不泄露任何数据（守卫）
- [ ] **C6** GIVEN 登录成功 WHEN 落点 THEN 直接进入 `/home`（`config_home_landing` 默认 `true`）；置 `false` 后重登回原 `/` 发现页（可回退）

## 全局

- [ ] **G1** 1440×900 与 390×844 两档截图与 QA 报告原截逐项对比，无裁切、无横向滚动
- [ ] **G2** 文档四问回填完成：L1（library / reading）、L2（新增端点）、L3（home-ia / reading-progress）、LLD 状态行
- [ ] **G3** 单测 + 集成 + 守卫测试全绿；`pytest` 既有用例无回归
