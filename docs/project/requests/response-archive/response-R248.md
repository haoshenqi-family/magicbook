
## 2026-10-29（R248：整本任务进度条只在书籍详情页显示）

### R248（用户：「进度条不应该显示在这里啊。应该显示在书籍详情页，全文任务那里」；截图为书架页/书卡弹层顶部的进度条）

- **结论先行**：已修复，进度条不再挂在书架页或书卡弹层的全局顶部；现在只在完整书籍详情页的「整本任务」按钮下方出现。
- **根因**：`detail.html` 的整本任务 partial 原先只受管理员门禁控制，XHR 书卡弹层也会加载它；`whole-book-panel.js` 初始化时又把 `#whole-book-progress` 移到 `body > .navbar` 之后。于是弹层片段被插入书架页后，进度条脱离书籍详情上下文，出现在书架页面顶部。
- **修复**：详情页新增专用 `#whole-book-progress-slot`，slot、partial 和 JS 统一加 `not is_xhr` 门禁；JS 只把进度条追加到该 slot，不再挂全局导航；进度条改为详情页内联布局，有活跃批次时隐藏「整本任务」按钮，收起后恢复按钮，收起状态在轮询期间保持。
- **边界**：只改进度条挂载与显示位置；三条整本任务的 start/status/retry 端点、轮询频率、缓存、计费与归档取书语义均未变。书卡弹层内的「整本任务」入口仍跳完整详情页。
- **测试**：新增 slot 双门禁、XHR 片段不下发 partial、进度条挂载到详情页 slot、收起后不被轮询重新弹出四条守卫；相关定向回归 **123 passed / 0 failed**，`node --check cps/static/js/whole-book-panel.js` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 明确进度条位置；契约 → 无变化；实现/边界 → L3 `docs/product/library/features/whole-book-progress.md`；本次实现 → R214 LLD §20、AC C11、需求基线与迭代 `plan.md`。
- **生产验收**：修复 `c2d5efa5` 已推 `origin/develop`，fnOS 构建 `END OK`、app-manager `deploy SUCCESS`，容器 `running/healthy` 且 `house.build-sha=c2d5efa5cf111f6e53be0bd5c463c08bda8c5777`。生产 `/shelf/5` 已无整本任务进度条；`/book/145` 的进度条位于工具栏下方、书名上方，并显示「全文单词详解 · 进行中」。
- **状态与驻留**：worktree `../magicbook-r248-progress-detail-only`（分支 `fix/r248-progress-detail-only`）已上线待用户验收；挂 R214 修复，不建独立 idea。
- **窗口与总结**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R236 整节原样搬至 `response-archive/response-R236.md` 并登记索引，窗口恢复 10。requests.md 条目 248 已从占位回填；本条为回应。冲突记录：无撞号。

