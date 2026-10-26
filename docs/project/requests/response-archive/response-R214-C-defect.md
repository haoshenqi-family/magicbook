## 2026-10-24（R214-C 验收缺陷：入口按钮落进书卡弹层 + 估算 500）

- **现象**：点「整本任务」后页面错乱（整页被套进「书籍详情」弹层）；Console 两条硬事实——
  `/ajax/whole-book-estimate` **500**、`isotope` 报错（后者是弹层里套整页带出来的噪音）。
- **定位一（错乱的真因）**：列表页点书卡是 **XHR 片段**——`show_book` 把 `detail.html`
  渲染成 `fragment.html`，片段没有 `block js`，面板 modal + JS 整块不下发，但按钮在
  `block body` 里照旧渲染。于是 `data-target` 选不到 `#whole-book-panel`，Bootstrap
  data-api 空转并与既有的 `#bookDetailsModal` 抢这次点击 ⇒ 整页被塞进弹层。
  **修**：按钮加 `not is_xhr` 门禁（整本任务只在完整详情页出现）+ 改 JS 显式绑定
  （`preventDefault` / `stopPropagation`），不再依赖 data-api。
- **定位二（500）**：估算链路两处**辅助查询**裸奔——`_history_rate`（台账采样）与
  `active_jobs`（活跃批次）。任一抛错就把整块面板打成 500，而 `.fail` 收到的是 HTML，
  界面只剩「估算失败：500 Internal Server Error」，既不知原因也不知该不该重试。
  **修**：两处各自 try/except 降级（没有样本 / 没有活跃批次 + 落 warning）；路由补兜底
  `except Exception`，落 `traceback.format_exc()` 并把 `类型: 消息` 回给前端——下次再失败，
  面板上会直接写着原因，不用再靠猜。
- **定位三（顺带修的形制级 bug）**：`data-t-start-wordDetail` 属性名带大写，被 HTML
  解析器小写成 `...worddetail`，而 JS 用 `t('start-' + kind)` 取 camelCase ⇒ 详解 tab
  的主按钮文案是空的。模板改全小写、JS 侧 `toLowerCase()`。
- **测试**：新增 5 条（data-api 禁用 / is_xhr 门禁 / 显式绑定 / 键名小写 / 路由兜底源码守卫）
  + 2 条降级行为测试（query 抛错时 `_history_rate` 回 `(None, 0)`、`active_jobs` 回全 None）。
  全量 **853 passed / 0 failed**。
- **待确认**：500 的具体异常类型要等这次上线后看面板上的那行红字（已含异常类型与消息），
  本轮先把「不可读的失败」变成「可读的失败」，再按实际原因收口。
