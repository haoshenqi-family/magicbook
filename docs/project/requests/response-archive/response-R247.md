
## 2026-10-29（R247：归档书内容速览误报 `book is unavailable`）

### R247（用户：「报错了」；截图为归档书 `/book/145` 的内容速览错误）

- **结论先行**：已修复，归档书不是数据损坏。`/book/145` 的详情页明确允许查看归档书，但内容速览复用了整本任务默认的取书过滤，导致同一本书在详情页可见、在内容速览中却报 `book is unavailable`；影响所有归档 EPUB。
- **根因**：`show_book()` 使用 `get_book_read_archived(..., allow_show_archived=True)`；内容速览的 `reading_insight.service._book_file()` 则调用 `JobServiceBase._book_file()` 的默认路径，最终走到 `calibre_db.get_filtered_book(book_id)`，默认排除归档书。内容速览、AI 简介、估算、活跃批次和缓存标识共用这个入口，所以错误不只出现在首屏解析。
- **修复**：`JobServiceBase._book_file()` 新增可选参数 `allow_show_archived=False`；默认分支保持原调用，整本翻译/朗读/详解边界不变。内容速览入口显式传 `allow_show_archived=True`，与详情页可见性对齐，一次覆盖速览、简介、估算、活跃批次与缓存标识。
- **测试**：新增 `test_archived_book_can_build_insight`，从生产同款 `book is unavailable` 红灯转为成功生成章节；新增 `test_book_file_default_keeps_archived_filter_for_whole_book_jobs`，确认整本任务仍排除归档书。内容速览、详情、估算、缓存标识与三条任务链路相关回归 **174 passed / 0 failed**；后续执行 `git diff --check`。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 明确归档书仍可看内容速览；契约 → 无变化；实现/边界 → 新建 L3 `docs/product/library/features/book-insight.md`，并修正缓存标识 L3 的归档口径；本次实现 → R214 LLD §19、AC B9、R214 需求基线与迭代 `plan.md`。
- **驻留**：worktree `../magicbook-r247-archived-insight`（分支 `fix/r247-archived-insight`）按闸门保留待用户验收；挂 R214 修复，不建独立 idea。
- **生产验收**：修复已随 `dfe30ed4` 上线，容器 `running/healthy`。刷新生产 `/book/145` 后，原 `内容速览解析失败：book is unavailable` 已消失，简介、目录（5 章 / 1393 段）与首章试读正常显示；同一页的整本任务进度条显示「全文单词详解 · 进行中」。
- **窗口与总结**：写入前 10 节，新增后达 11 节；按「写入即检查」把最早 R234 整节原样搬至 `response-archive/response-R234.md` 并登记索引，窗口恢复 10。requests.md 条目 247 已从占位回填；本条为回应。冲突记录：无撞号。
