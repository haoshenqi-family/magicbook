
## 2026-10-29（R246：整本任务进度条补齐任务类型与状态）

### R246（用户：「进度条什么都不显示，不知道是哪个任务的进度条」）

- **结论先行**：已修复并上线待验收。截图的 `735 / 990` 是全文单词详解任务；进度条并非没有数据，而是左侧任务标题取空，只剩百分比与计数。
- **根因**：R214 子项 C 的进度标题复用按钮文案 `t('start-' + kind)`。详解的 `kind` 是 camelCase `wordDetail`，但浏览器把 `data-t-start-wordDetail` 属性名解析成小写 `data-t-start-worddetail`，键名不一致使 `t()` 返回空串；即使补上小写，按钮动作「打开详解页面」也不是任务名。
- **修复**：模板新增独立的 `data-t-progress-kind-{translate,tts,worddetail}` 与四种状态句式；`renderProgress()` 先将 `kind` 小写化，再渲染「全文单词详解 · 进行中」等标题，并对缺键保留回退，避免未来新增链路再次出现空标题。三条整本 job 的端点、轮询频率、缓存与计费均未改。
- **测试**：新增 `test_progress_title_names_task_and_status`，钉住三类任务名、四种状态句式、小写化与缺键回退；定向回归 10 个相关文件 **155 passed / 0 failed**，`node --check cps/static/js/whole-book-panel.js` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 补进度条标识说明；契约 → 无变化；实现/边界 → 新建 L3 `docs/product/library/features/whole-book-progress.md`；本次实现 → R214 LLD §18 与 AC C10。需求基线、迭代 `plan.md`、requests.md R246 已同步。
- **上线**：实现 `fad1be71` 已推 `origin/develop`；fnOS `build END OK`，app-manager `deploy SUCCESS`，容器 `running/healthy` 且 `house.build-sha=fad1be7155fec3c4ff30f1b18bdcf0c6d9b99521`。生产静态 JS 与镜像内模板均已确认包含 `progress-kind-*`、`progress-running` 和 `kind.toLowerCase()`。
- **真机验收点**：管理员打开任意书详情页，运行任一整本任务；吸顶进度条应分别显示「整本翻译 / 整本朗读 / 全文单词详解 · 进行中」，结束后显示已完成、有失败段落或已取消。截图对应的详解任务应显示「全文单词详解 · 进行中」。
- **窗口与驻留**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R233 整节原样搬至 `response-archive/response-R233.md` 并登记索引，窗口恢复 10。worktree `../magicbook-r246-wholebook-progress-label`（分支 `fix/r246-wholebook-progress-label`）按闸门保留待验收，验收通过后删除。
- **总结**：requests.md 条目 246 已从占位回填；本条为回应。冲突记录：无撞号。
