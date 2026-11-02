# LLD — R234 悬浮球快捷动作：AI 对话恒在第一位且不可删除（服务端不变量）

> 状态：已上线待验收（2026-10-26；挂 R223 修改意见，不建独立 PingCode idea）

## 1. 需求与定性

用户原话：「伙伴悬浮球快捷动作，AI 对话始终在第一位切不可删除」。

R223 交付时前端已是该行为：`/buddy` 页 chat chip 固定选中不可取消（保存前 `unshift("chat")`）、`renderBubbles` 恒把 chat 排第一位（`["chat"].concat(selected.filter(≠chat))`）。缺口在服务端：POST 校验只查「list / 白名单 / 去重 / 4–5 个」，不查 chat 在不在、更不查位置——直连 API 可把 chat 存成缺失（此时气泡渲染成 6 个，突破 4–5 口径）或末位；存量 `view_settings['buddy']['quickActions']` 里的旧值读回时也不归一。本条把「恒第一位、不可删」从前端约定升级为服务端不变量，前端行为不变。

## 2. 实现（`cps/routes/buddy.py`）

- 新增 `_pin_chat_first(actions)`：白名单过滤 + 保序去重 + `chat` 钉到第一位；不做数量裁决（调用方按场景定）。
- **POST 归一**：结构校验（list / 白名单 / 无重复）通过后，`selected` 经 `_pin_chat_first` 归一，**数量口径按归一后算**——`QUICK_ACTION_MIN=4 ≤ len ≤ QUICK_ACTION_MAX=5`；不带 chat 发 3 个＝补 chat 后 4 个合法，发 5 个非 chat＝6 个，**400 拒绝而非静默截断**（不丢用户选择）。落库与响应均为归一后列表。
- **读回归一**：`current_user_view_settings()` 对存量值同样 `_pin_chat_first` 后截到上限 5；归一后不足 4 个或含白名单外动作 → 回落默认四项（`QUICK_ACTION_DEFAULTS`）。R223 期服务端不校验 chat 时写入的旧值（缺 chat / chat 末位 / 连 chat 超 5）在读时全部被纠正，无需数据迁移。
- 常量钉口：`QUICK_ACTION_PINNED = "chat"`、`QUICK_ACTION_MIN/MAX = 4/5`，替代路由里的裸数字。
- 前端零行为改动；仅顺手更正 `buddy.js` 注释（「勾选 2-5 个」实为 4-5 个，并注明服务端归一兜底）。

## 3. 测试（`tests/test_buddy_page.py` +3）

- `test_quick_actions_post_pins_chat_first`：不带 chat 的 POST 由服务端补到首位并读回；chat 在中间的 POST 被前移到首位。
- `test_quick_actions_post_rejects_over_max_counting_pinned_chat`：5 个非 chat 动作＝连 chat 6 个，400 且不落库。
- `test_quick_actions_read_normalizes_legacy_values`：直写 `view_settings` 模拟存量旧值（缺 chat / chat 末位 / 连 chat 共 5 个非 chat），GET 均读回归一结果；坏数据（白名单外动作）回落默认四项。
- 既有 R223 三条用例语义不变（2 个 / 未知动作 / 重复动作仍 400 不落库）。定向回归：`test_buddy_page.py + test_reader_r215_ui.py + test_i18n_seed_contract.py` **26 passed**；`test_buddy_no_token_usage.py + test_onboarding_tour.py + buddy 全家` **50 passed**。

## 4. 边界

- 服务端归一是防御层：正常路径（`/buddy` 页 UI）永远不会发出 chat 缺失/错位的 payload，归一不改变 UI 可见行为。
- 归一化不落库纠正（读时归一、写时才持久化归一结果）：用户旧值在下一次保存前库内保持原样，属可接受惰性。
- 气泡渲染端 `renderBubbles` 的 `["chat"].concat(...)` 保留——双保险，未来若有新消费方读 `selected`，两端行为一致。
