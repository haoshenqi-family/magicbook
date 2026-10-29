## 2026-10-26（R234：悬浮球快捷动作——AI 对话恒在第一位且不可删除，升级为服务端不变量）

### R234（用户：「伙伴悬浮球快捷动作，AI 对话始终在第一位切不可删除」）

- **结论先行**：这条铁律此前只由前端保证（`/buddy` 页 chat chip 固定选中不可取消 + `renderBubbles` 恒把 chat 排第一位），服务端 POST 不校验 chat——直连 API 可把 chat 存成缺失（气泡渲染成 6 个，突破 4–5 口径）或末位，存量旧值读回也不归一。本轮把「恒第一位、不可删」落为**服务端不变量**，用户可见行为不变。
- **实现**：`cps/routes/buddy.py` 新增 `_pin_chat_first()`（白名单过滤 + 保序去重 + chat 钉首位）。POST 归一后落库：缺 chat 补首位、错位前移；数量口径连 chat 一起算（4–5），发 5 个非 chat＝6 个，**400 拒绝而非静默截断**。`current_user_view_settings()` 读回对存量旧值（R223 期写入）同样归一并截上限 5，归一后不足 4 个或含白名单外动作回落默认四项——无需数据迁移的惰性纠正。常量 `QUICK_ACTION_PINNED/MIN/MAX` 钉口替代裸数字。
- **前端零行为改动**：仅更正 `buddy.js` 注释（「勾选 2-5 个」实为 4-5 个）；`renderBubbles` 的 `["chat"].concat(...)` 保留作双保险。
- **测试**：`tests/test_buddy_page.py` +3——`test_quick_actions_post_pins_chat_first`（缺 chat 补位 / chat 中位前移，均读回归一结果）、`test_quick_actions_post_rejects_over_max_counting_pinned_chat`（5 个非 chat 400 且不落库）、`test_quick_actions_read_normalizes_legacy_values`（直写 view_settings 模拟三类存量旧值 + 坏数据回落默认）。定向回归 **26 passed**（buddy 页 + R215 结构 + i18n 契约）、buddy 全家 **50 passed**；`git diff --check` 通过。既有 R223 三条校验用例语义不变（2 个 / 未知 / 重复仍 400）。
- **文档四问**：能力 → L1 `readme/companion.md` 悬浮球条目补「恒在第一位且不可删除（R234）」；契约 → 端点形制不变（POST 语义收紧已写进基线）；实现/边界 → 新建 L3 `companion/features/buddy-quick-actions.md`；本次实现 → `iterations/1.0/r234-buddy-qa-chat-first/lld.md`。需求基线 `companion/requirements.md` §R234、R223 LLD 边界两条标注〔已被 R234 取代〕、迭代 `plan.md` 已同步。
- **台账与驻留**：R234 由 `claim.sh` 占号并 push（`500a7316`，纯台账）；实现 `bbd482ae`。写入前 response.md 已有 10 节，按「写入即检查」把最早 R224 节原样搬至 `response-archive/response-R224.md` 并登记索引，窗口恢复 10 节。worktree `../magicbook-r234-buddy-qa-chat-first`（分支 `feat/r234-buddy-qa-chat-first`）按闸门驻留待用户验收。
- **总结**：requests.md 条目 234 已从占位回填；本条为回应。冲突记录：无撞号；主检出未提交的 `messages.po` 改动（去掉积分说明里「约每千 token 消耗 1 积分」一句）经核对与 origin/develop 中 R230 `eecc514b` 已合入的同一 hunk 逐字一致（重复劳动），ff 拉齐前以 stash 挪开、push 后确认该改动已在 HEAD 中，**stash 条目保留未动**（如为并行会话在途工作可自行处置）。
