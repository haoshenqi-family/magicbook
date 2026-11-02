## 2026-10-29（R253：缓存翻译按 1 积分/缓存段计费）

### R253（用户：「缓存翻译不是也要1个积分吗」；随后拍板「按 1 积分/缓存段修改」）

- **结论先行**：已把书籍详情页的翻译缓存成本从 R252 的 0 改为 **1 积分/缓存段**。翻译行现在显示「缓存翻译 A 积分（全文生成原价约 M 积分）」，其中 `A = cache_readiness.translate.total × 1`。
- **段数隔离**：翻译与朗读分别使用 `translate.total` 与 `tts.total`。即使两本台账段数不同也不会互相顶替；新增回归钉住翻译 70 段、朗读 101 段时分别显示 70 与 101 积分。
- **文案一致**：整本翻译缓存标识的悬浮说明同步从「命中缓存不额外计费」改为「命中缓存按 1 积分/段计」；朗读仍为「缓存收听」1 积分/段。
- **实现**：`cps/reading_insight/cost.py` 新增 `TRANSLATION_CACHED_CREDITS_PER_SEGMENT = 1`，翻译 `cachedCredits = total × 1`，并返回 `cachedSegments/cachedPerSegment`；`detail.html` 成本行与缓存标识同步。详情页仍不探测缓存，整本翻译后台任务仍按 token 计费。
- **测试**：`test_book_cost_summary.py + test_whole_book_estimate.py + test_book_insight.py + test_cache_readiness.py` 共 **57 passed / 0 failed**；`git diff --check` 通过。
- **文档四问**：能力 → L1 `readme/library.md`；契约 → 无 HTTP 契约变化；实现/边界 → L3 `book-cost-summary.md` 与 `cache-ready-badge.md`；需求与本次实现 → 需求基线 R253、`REQUIREMENTS.md`、迭代 plan、本 LLD/AC。R241/R252 历史文档只加取代注记，不改写正文。
- **跨仓**：moon-well R231 已实现真实缓存翻译扣费；本仓只同步展示口径，部署顺序 moon-well 先、magicbook 后。
- **上线**：实现提交 `1e525b18` 已快进推送 `origin/develop`；fnOS 构建 `END OK`，app-manager 部署 `SUCCESS`，magicbook healthy，线上镜像 `house.build-sha=1e525b18703cc0e638a28507a2c77f18bb6b0630`。
- **窗口与驻留**：写入前窗口 10 节，新增后 11；按「写入即检查」把最旧 R239 整节原样搬至 `response-archive/response-R239.md` 并登记索引，窗口恢复 10。worktree `../magicbook-r253-cached-translation-billing`（分支 `feat/r253-cached-translation-billing`）按闸门保留待验收。
- **总结**：requests.md 条目 253 已从占位回填；本条为回应。冲突记录：无撞号。
