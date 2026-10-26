# R232 · AI 伴读面板不再显示 token 用量

> 状态：**开发完成，待验收**（2026-10-26）
> 需求原话：「AI 伴读不要显示token 使用量（可以记录，但是不要显示）。积分token用量仅在【设置】【积分】那里查看即可。」

## 1. 要解决的是什么

伴读面板每轮回答结束后，会在气泡下方追加一行灰色小字 `tokens 8123/456`（`ai_chat.js` 的 `final` 分支读 `obj.usage.promptTokens/completionTokens` 渲染 `.ai-chat-usage`）。

问题不在「准不准」，在于**位置错了**：

- 对话区是读正文的地方。逐轮挂一行输入/输出 token，既解释不了这条回答为什么好，也不影响下一次提问，只制造噪音；
- 这个数字是**账务信息**，唯一有意义的对照是「这一笔扣了多少积分」——那是【设置】【积分】消耗明细的活；
- 同一屏里既有「回答」又有「计费」，会让人以为字数越多越贵，而实际计费口径（每千 token 折 10 积分、TTS 按字符、ASR 按秒）比一行的 `x/y` 复杂得多，展示一个数反而误导。

## 2. 改法（只动展示，不动记录）

| 文件 | 改动 |
| --- | --- |
| `cps/static/js/ai_chat.js` | `case "final"` 删掉 usage 渲染块，保留 `conversationIdFromFinal = obj.conversationId`（首条消息靠它回传服务端建会话）；`speechTextOf()` 的清洗选择器去掉 `.ai-chat-usage` |
| `cps/static/css/ai_chat.css` | 删 `.ai-chat-usage` 规则，避免「节点没了样式还在」诱导后人加回去 |
| `tests/test_buddy_no_token_usage.py` | 新增 5 条守卫（见 §4） |

**没动的地方（重要）**：
- SSE 的 `final` 事件里 `usage` 字段照旧下发，前端只是不消费——要排查线上计费时抓包/看日志仍拿得到；
- moon-well `CreditServiceImpl.consumeForLlmTask` 照旧按 `total_tokens` 扣费并落库，流水 `remark` 是「AI任务消耗 N token、每千 token 折 10 积分」；
- 积分页消耗明细（`credits.html` 的 `#credit-consume-table`：时间/类型/原因/功能/积分）一行未改——**「原因」列就是那个 token 数**，这轮等于把用量的可见入口收敛到唯一一处。

## 3. 为什么不做成「可展开」

考虑过「默认折叠、点一下展开」。否决理由：用户要的是「不要显示」，折叠仍然要占一行、要一个点击、要一句文案，噪音只是从常显变成常驻入口；而真正需要核对用量的人（对账、报障）在积分页能看到完整的「时间 + 原因 + 扣了多少」，比聊天里一行 `x/y` 信息量更大。

## 4. 守卫（`tests/test_buddy_no_token_usage.py`）

1. `ai_chat.js` 不含 `ai-chat-usage` / `promptTokens` / `completionTokens`；
2. **全站** `cps/static/js/*.js` 都不许读这两个字段——面板自 R220 起全站挂载，漏一个页面就又冒出来；
3. `final` 分支仍回传 `conversationIdFromFinal`（删用量不许顺手把分支删了），且该分支不再出现 `obj.usage`；
4. `ai_chat.css` 无 `.ai-chat-usage` 残留；
5. 积分页仍保留 `#credit-consume-rows` 与「原因 / 功能 / 积分」三列——用量入口被删会让用户彻底查不到。

笔误防线也踩了一次：CSS 注释里原本写了 `.ai-chat-usage` 类名，第 4 条守卫直接红——这正是这类字面量守卫的价值，注释里的类名一样会误导人。

## 5. 边界与遗留

- **历史会话**：删除的只是渲染代码，存量消息里本来就没有把用量存进正文（当时是即时 DOM 节点），所以刷新后旧会话也没有残留。扩展侧另说（见上）。
- **Chrome 扩展 magiclens 仍会显示用量（本轮未修，已知遗留）**：`magiclens/extension/chat.js:366` 在 `onFinal` 里写 `tokens x+y` 到消息的 `.meta` 行。它不共用 magicbook 的面板脚本，属另一个仓、另一条发版链（扩展需重新打包分发），故本轮只记录、不夹带修改。**修正**：本条最初误判为「扩展侧无需改」，原因是 BSD `grep` 不认识 `\|` 交替导致假阴性，后续用 ripgrep 复核才发现——同一坑也差点漏掉 `CreditServiceTest` 里的活动倍率用例。
- **不涉及计费口径变更**，moon-well 仓零改动。
