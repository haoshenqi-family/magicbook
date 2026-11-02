# R214 子项 C（整本任务代价面板）回应 · 原文归档

> 2026-10-25 R229 写入触发轮转搬移，原文无改写。

## 2026-10-24（R214 子项 C：整本任务代价面板）

### R214-C（承接「继续」→ 子项 C 开发）

- **任务定位**：R214 收口件，PJM MB-13 / Ship MAGICBOOK-221。三个整本入口（翻译/朗读/详解）
  从「点一下就下单」改成「先看代价再决定」，落 LLD §4.3/§5/§6/§7。
- **后端**：`reading_insight/service.py` 补 `estimate()` + `active_jobs()`；`routes/book_detail.py`
  加 `POST /ajax/whole-book-estimate`（admin + `_llm_task_admin_gate`）；`web.py` 加
  `_credit_billing_rates()`（moon-well `/credit/billing`，5 分钟进程内缓存，取不到回 None）
  与 show_book 的活跃批次快照注入。
- **实现修正（与 LLD 原文不同，已回填 §4.3 表）**：
  ① `units.billable` 新增——翻译/朗读台账的 item 都按 `text_hash` 唯一，拿全书段落数当工作量
  会把重复段算两遍，耗时与积分一起虚高；`paragraphs` 仍保留书目真实段数。
  ② `activeJobs` 新增——§7.5 要的「页面初始进度态」需要服务端承载字段，估算与首屏共用同一个
  `active_jobs()`，两条路径 `total/done` 不会分叉。
  ③ `duration.known` 显式化 + **详解没有常量兜底**（无实测支撑秒/词，样本不足就明说不知道）。
  ④ `credits.rate` 只回传本条链路用到的字段。
  ⑤ 详解覆盖率直接分批调 cached-check，不走 `preview()`（后者会重抽一遍正文；`notWordLike`
  只在预览页有解释位）。
- **前端**：新增 `partials/whole_book_panel.html`（三 tab + 卡片 + 进度条 + 全部文案在 data-*）
  与 `whole-book-panel.js`（切 tab 拉估算并按 kind 缓存、主按钮二次确认带预计时长/积分、
  进度轮询 4s/5s/30s、有活跃批次直接进进度态）；`detail.html` 三个并列按钮合并为单个
  「整本任务」入口并把内联 jQuery 整体迁出；`book-detail.css` 补面板与吸顶进度条样式。
  **详解保持两步式**：面板主按钮只跳 `word_detail_batch_page`，不替管理员下单（R176 边界）。
- **测试**：新增 `tests/test_whole_book_estimate.py` ×10（去重计费单位、朗读不探缓存、
  详解只走 cached-check、lookup 失败不报 0、费率不可得、tts 关闭计费专属原因、历史中位数优先、
  活跃批次透传、非法 kind、空段落）；`test_book_detail_r214.py` 补 5 条（入口 admin 门禁、
  面板三 tab、旧并列按钮不许复活、「不修改原书文件」可见、模板真渲染 + endpoint 存在、
  估算端点只读守卫）。**改了两条既有守卫**：R176 的「三个整本按钮各一处」（形制已合并，
  改判「入口一处 + 面板三 tab」）、R214 自己的 `test_whole_book_buttons_admin_gated`（同因）。
  全量 **804 passed / 0 failed**。
- **未做**：真机验收未跑（面板要真书 + admin 账号）；push 闸门留给你——本节代码在
  `feat/r214-book-detail` 分支上，未合 develop、未 push。
- **窗口**：本条写入后 `## ` 节数再 +1。按上一轮约定（R218 条已说明）轮转待统一整理，
  避免与并行会话的归档改动撞车，本轮不搬移。
