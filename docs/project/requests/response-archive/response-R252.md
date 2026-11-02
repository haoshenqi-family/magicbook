# response 归档：R252（2026-10-29）

> 2026-11-01 R261 写入触发窗口轮转，从 response.md 原样搬移（不总结、不改写、不改编号）。

## 2026-10-29（R252：书籍详情页展示整本朗读与翻译费用及缓存费用）

> 2026-10-29 R253 注记：本节翻译缓存 0 积分的口径已被 R253 取代；R252 的其余实现与验收记录保留原貌。

### R252（用户：「书籍详情页写一下完整听完大概需要多少token，完整翻译完大概需要积分，如果已经缓存了就写缓存需要的积分加原始需要的积分，比如 【完整朗读预计花费1（100）积分】1是缓存 100是全文朗读预计。详情也写一下。」）

- **结论先行**：已实现，书籍详情页在缓存齐备标识后固定显示两行成本摘要。用户例子里的「1（100）」信息结构保留为「缓存值（全文原价）」，但数字按真实计费口径计算，不把整本朗读缓存总价机械写成 1。
- **口径纠正**：翻译按 token，`chars/4` 粗估后用 moon-well R222 公式 `ceil(tokens × creditsPer1kToken / 1000)`；翻译命中缓存不调用模型，缓存阅读为 **0 积分**。TTS **不按 token**，全文生成按字符 `floor(chars / charsPerCredit)`；已缓存收听按 moon-well R213 的 **1 积分/段**，所以页面写「约 N 字符（TTS 不按 token）」与「缓存收听 A 积分（全文生成原价约 M 积分）」。
- **实现**：`reading_insight/parser.py` 在速览解析时顺带记录去重后的 `billableParagraphCount` / `billableCharCount`，不解析第二遍 EPUB；新增 `reading_insight/cost.py::build_book_cost_summary()` 纯函数；`show_book()` 复用 `entry.insight` 与 `entry.cache_readiness`，读取 moon-well `/credit/billing`（沿用 5 分钟进程缓存，详情页超时 2 秒）。详情页不调用 `find-translations`、`cached-check` 或逐段 TTS 探针，费率故障只让积分暂缺，不拦页面。旧速览快照没有去重字段时回退到 `charCount` / `paragraphCount`。
- **展示**：未缓存时只显示全文生成原价；翻译已缓存时显示「缓存阅读 0 积分（全文生成原价约 M 积分）」；朗读已缓存时显示「缓存收听 A 积分（全文生成原价约 M 积分）」，其中 `A = readiness.tts.total × 1`。费率不可得显示「暂不可得」，TTS 费率字段缺失也不会伪装成 0；明确 `tts.enabled=false` 时才显示全文生成 0。
- **同步修正**：`/ajax/whole-book-estimate` 的翻译积分从旧的「不足千按千」回正为 R222 比例计费并向上取整；定向测试中 22 字 / 5.5 token 从错误的 10 积分改为 1 积分，上界 2。
- **测试**：新增成本纯函数与模板/接线守卫，覆盖未缓存、翻译已缓存、朗读已缓存、两者已缓存、费率不可得、TTS 关闭、TTS 字段缺失、旧快照回退、2 秒费率超时；同时补 parser 去重规模断言。相关定向回归 **118 passed / 0 failed**，全量 **1133 passed / 0 failed / 4 warnings**，`py_compile` 与 `git diff --check` 通过。
- **文档四问**：能力 → L1 `docs/product/readme/library.md` 新增「整本费用预估」；契约 → 无对外 HTTP 契约变化；实现/边界 → 新建 L3 `docs/product/library/features/book-cost-summary.md`；本次实现 → R252 LLD 与 AC、需求基线、`REQUIREMENTS.md`、迭代 `plan.md`。LLD 状态为「已上线待验收」。
- **上线**：实现提交 `004c6a1f` 已快进推送 `origin/develop`；fnOS 构建 `END OK`，app-manager 部署 `SUCCESS`，容器 `healthy` 且 `house.build-sha=004c6a1fc7ea89f2756b3dba116e7df870afa025`，线上 `/login` 返回 200。worktree 原样保留待用户验收。
- **窗口与驻留**：写入前窗口 10 节，新增后达 11；按「写入即检查」把最早 R238 整节原样搬至 `response-archive/response-R238.md` 并登记索引，窗口恢复 10。worktree `../magicbook-r252-book-cost-summary`（分支 `feat/r252-book-cost-summary`）按闸门保留待验收。
- **总结**：requests.md 条目 252 已从占位回填；本条为回应。冲突记录：无撞号；本轮按用户「多少 token」的提问明确区分了翻译 token 与 TTS 字符口径。
