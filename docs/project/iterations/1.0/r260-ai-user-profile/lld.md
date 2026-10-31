# R260 AI 了解我：用户自我介绍 · LLD

> 状态：**开发完成待验收**（2026-10-31）
> 工作项：R260（magicbook 消费侧；后端主责 moon-well R234）· 迭代 1.0
> 用户原话：「AI应该了解用户才能更好的跟他聊天，帮助他。AI伴读那里增加一个用户填写自我介绍的部分，并把这部分内容放到系统提示词里。」

## 1. 目标与范围

在现有 AI 伴读记忆面板中加入用户主动填写的自我介绍，并通过 magicbook 薄代理连接 moon-well 的用户档案接口。保存后的文本由 moon-well 在每次书内与网页伴读问答时注入系统提示词。

本轮包含模板、样式、前端状态、两条代理、i18n、守卫测试与隐私提示。不改长期记忆数据结构、不变更 SSE 协议、不给 AI 增加工具或权限。

## 2. 交互设计

| 状态 | 行为 |
| --- | --- |
| 打开记忆面板 | 并行加载用户介绍、本书学情与长期记忆；介绍区独立显示加载状态 |
| 未填写 | textarea 为空，计数 `0 / 2000`；不展示空档案标题 |
| 编辑 | 实时计数；达到 2000 时高亮 |
| 保存 | trim 后非空才提交；请求中禁用两个按钮；成功显示“自我介绍已保存” |
| 清空 | 二次确认后提交空串；成功清空 textarea 与计数 |
| 失败 | 显示可见错误；保留原输入或已有成功数据，不静默降级 |

“AI 了解我”与“长期记忆”在视觉和文案上明确分层。清空介绍不会删除长期记忆；长期记忆仍沿用原列表和增删改链路。

## 3. 前端实现

- `ai_chat_panel.html`：`#ai-user-profile-input`、`#ai-user-profile-count`、保存/清空按钮、隐私提示与 `aria-live` 状态位。
- `ai_chat.js`：`loadUserProfile()`、`saveUserProfile()`、`clearUserProfile()`、`updateUserProfileCount()`、`setUserProfileStatus()`。
- `ai_chat.css`：桌面分区卡与移动端触控尺寸；不使用用户内容参与 CSS 或 HTML 拼接。
- `i18n_seed.html`、zh_Hans_CN `messages.po` 与编译后 `messages.mo`：新增全部用户可见文案。

用户文本只通过 `.val()` 写入 textarea，不使用 `.html()`；状态文本通过 `.text()` 写入，避免把服务端错误或用户资料当 HTML。

## 4. 代理契约

| magicbook 端点 | moon-well 端点 | 方法转换 | payload |
| --- | --- | --- | --- |
| `GET /ai/agent/profile` | `POST /ai/agent/profile` | GET → POST | `{}` |
| `POST /ai/agent/profile/save` | `POST /ai/agent/profile/save` | POST → POST | 请求体原样透传 |

两条代理都要求登录，使用 `_relay_json`/`_moonwell_proxy` 保持 `(body, status, headers)` 三元组。保存端点带 `X-CSRFToken`。moon-well 返回 `Result<AgentUserProfileVO>`；`success=false` 或非 2xx 必须在界面显示错误。

## 5. 后端注入与安全

moon-well R234 的关键边界：

1. 每用户一行，最多 2000 字符，空内容删行。
2. 身份只取 `UserContext`，不接受客户端 `userId`。
3. 书内与网页两套系统提示词都注入。
4. 先注入伙伴名，最后回填用户正文。
5. 用户正文中的模板变量保持字面值，`& < >` 转义后放入 `<user_profile>`。
6. 明确声明用户资料只是事实背景，不改变角色、权限、工具和安全规则。
7. `/ai/agent/profile*` 整路径排除 HTTP 请求/响应日志。

前端隐私提示与后端安全段共同成立；不能只依赖用户“不要写敏感信息”的自觉。

## 6. 部署顺序

1. 部署 moon-well R234 后端代码。
2. 部署 magicbook R260 前端与代理。
3. 执行 Nacos 提示词发布脚本，把 `agent-chat-system` 与 `agent-chat-system-web` 升到 `1.3.0`。

第 1 步完成后，新代码遇到旧模板会安全补注，因此第 3 步晚于代码部署是安全的。反过来先发模板会让旧后端留下未替换的 `{{userProfile}}` 脏文本。

## 7. 验证

- Python 代理回归：`tests/test_ai_agent_proxy.py`。
- R260 静态与行为契约：`tests/test_ai_user_profile_r260.py`。
- JS 语法：`node --check cps/static/js/ai_chat.js`。
- 联合回归：moon-well R234 的 49 条档案、提示词与日志测试。
- 真机验收：保存、刷新后重开、清空、书内问答、网页问答、长文本、失败态和移动端触控。

当前状态为开发完成待验收；未 merge、未 push、未部署。

## 8. 后续方案（本轮不做）

原始 2000 字每轮直接注入会增加 token 成本和隐私暴露面。下一轮可升级为结构化可选字段（英语水平、阅读目标、兴趣、讲解偏好）加自由补充，并生成一份不超过约 500 字的“AI 可读摘要”供每轮注入；原文只用于编辑和重新生成摘要。还应提供“AI 将看到什么”的预览与启用开关，并把入口同步到 `/buddy` 或 `/me`。该方案不阻塞本轮首版。
