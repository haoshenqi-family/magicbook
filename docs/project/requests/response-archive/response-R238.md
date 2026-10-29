# R238 对话回应归档

## 2026-10-28（R238：全文单词详解预览卡死——所有书共有的 jQuery 顺序缺陷 + 后台预计算）

### R238（用户：「magicbook 全文单词详解 卡在预览加载中。booi_id=145 这是为什么？所有的书是否都会这样？能否加一个异步任务，后天提前把这个算出来」）

- **结论先行**：卡住的主因不是 `book_id=145`，也不是计算慢，而是页面脚本根本没执行。模板把预览脚本放在 `{% block body %}`，早于 `layout.html` 底部 jQuery；浏览器控制台报 `ReferenceError: $ is not defined`，`/ajax/word-detail-preview` 一次都没发出，所以开始按钮永远禁用。该模板为所有书共用，**所有书都会中招**，只是短书、缓存或人工验证可能没把问题暴露出来。
- **慢链路是第二层问题**：修掉脚本后，原实现仍会在请求线程解析整本 EPUB，再按 2000 词一批串行调用 moon-well `cached-check`；moon-well 每次检查又会做索引级扫描，期间没有持久化快照或中间进度。即使最终能算，体验也可能长时间只有静态「预览加载中…」。
- **实现（`5bb6336e`）**：① 内联脚本移入 `{% block js %}`，由实际渲染顺序守卫钉住「jQuery 先于本页脚本」；② 新增 `reading_word_detail_preview` 快照表（按 `(book_id, book_format)` 唯一）与后台 worker，首请求只校验书目/指纹并立即返回 `RUNNING`，页面每 2.5 秒轮询 `EXTRACTING/CHECKING` 与已检查词数；③ `READY` 10 分钟内直接复用，`FAILED` 60 秒内复用失败，`force=true` 可绕过；④ `start()` 复用同指纹、新鲜 READY 的 `missing_json` 与计数，不再二次解析整本、重扫缓存；⑤ 建表通过 `JobServiceBase.extra_tables` 扩展，保持 B6「建表原语只有一份」。
- **费用与只读边界**：后台预计算只调用 `cached-check`，不会自动生成单词详解；真正生成仍需管理员看过数字后二次确认。没有对全库做自动预热，只有实际打开某本书预览页才计算该书，避免「看管理页就产生全库扫描」。
- **测试**：定向台账/估算/公共骨架 **68 passed / 0 failed**；扩展回归（详解、整本估算、书籍详情、翻译/朗读共用骨架、i18n）**179 passed / 0 failed**；`py_compile`、`pybabel compile`、`git diff --check` 通过。新增守卫覆盖渲染顺序、首请求不跑上游、READY/TTL/force、FAILED 退避、start 复用、迟到 worker 不重算、2000 词分批与建表原语不外叉。
- **文档四问**：能力 → L1 `docs/product/readme/vocabulary.md`；契约 → L2 `docs/product/vocabulary/interface.md`（新增 RUNNING/READY/FAILED、force、10 分钟 TTL、60 秒失败退避）；实现/边界 → L3 `docs/product/vocabulary/features/word-detail-preview.md`；本次实现 → `docs/project/iterations/1.0/r238-word-detail-preview/lld.md`（状态：已上线待用户最终验收）。另补建 vocabulary 需求基线并同步 `plan.md`。
- **驻留与上线**：R238 占号为 `c90ce790`，实现 `5bb6336e`，merge `9577c541`。用户已授权全量测试、push 与生产验收；正式发布态全量 **1014 passed / 0 failed / 4 warnings**，merge 后定向 **68 passed / 0 failed**。已 push `origin/develop`（`c0f4f598`），fnOS build `c0f4f5982d02de4c1e41e05ebb2da5939255db04` 于 2026-10-28 14:33 部署成功，容器 running，build SHA 与登记一致。worktree `../magicbook-r238-word-detail-preview`（分支 `fix/r238-word-detail-preview`）按闸门保留，待用户最终验收后再清理。
- **生产验收（2026-10-28）**：`book_id=145&book_format=epub` 从「正在读取正文」自动进入 READY，去重 4,345 / 已有 1,952 / 待生成 2,043，开始按钮启用；另一本 `book_id=50&book_format=epub` 为 6,111 / 2,269 / 3,411，按钮启用。两本书均实际发出预览 AJAX 并落库，控制台无 `$ is not defined`。`book_id=50` 在 10 分钟窗口内刷新后立即显示 READY，数据库 `computed_at=2026-10-28 06:36:00.278545` 未变化，确认命中同一快照。验收未点击「开始补缺」，未触发生成或 token 费用。
- **后续**：moon-well `cachedLookupKeys()` 的全索引扫描优化未夹带在本任务，建议另立跨仓编号改为按输入词表 `terms` 查询或加短 TTL 缓存。
- **窗口**：写入前 10 节已满，按「写入即检查」把最早 R227 整节原样搬至 `response-archive/response-R227.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 238 已从占位回填；本条为回应。冲突记录：无撞号；本轮把用户所写「后天」按「后台」理解。
