# companion · L2 接口说明

> 读者：调用者 / 集成者。本文件登记站内信消费侧代理、管理员运营发信后台、独立伙伴邮件弹层与 R260 AI 用户自我介绍代理；companion 的 AI 对话、伙伴目录等历史接口仍以文末指针为准。后端邮件事实、幂等、已读/已解决语义唯一权威是 moon-well R228；运营发信事实与批次审计唯一权威是 moon-well R230；用户自我介绍存储与提示词注入唯一权威是 moon-well R234。

## 能力边界

magicbook 只提供登录后的邮件入口、页面、纯文本渲染与薄代理，不创建、不解决、不删除邮件。伙伴、成就和积分邮件只负责通知与跳转，不能从邮件内直接领取。管理员运营发信页面只调用 moon-well 的管理员接口；发送批次、撤回与审计事实仍由 moon-well 持有。

## 页面

| magicbook 端点 | 方法 | 说明 |
| --- | --- | --- |
| `GET /mail` | 页面 | 登录用户完整收件箱；Flask endpoint 为 `web.mail_inbox_page` |
| `GET /admin/mail` | 页面 | 管理员运营发信后台；Flask endpoint 为 `web.admin_mail_page`，仅 `role_admin()` 可访问 |

## JSON 代理

四个用户侧代理全部要求 `@user_login_required`。成功与上游失败均原样返回 `_moonwell_proxy` 三元组 `(body, status, headers)`；例外只有 `read` 的本地非法 `id` 校验返回 400。

| magicbook 端点 | moon-well 端点 | 上游方法 | 超时 | 说明 |
| --- | --- | --- | --- | --- |
| `GET /ajax/mail/unread-count` | `POST /mail/unread-count` | POST | 10s | 无 payload |
| `GET /ajax/mail/page?pageNo=1&pageSize=20` | `POST /mail/page` | POST | 10s | `pageNo` 默认 1、上限 100000；`pageSize` 默认 20、上限 50；非法字符串回落默认 |
| `POST /ajax/mail/read` | `POST /mail/read` | POST | 10s | 只接受 JSON 对象中的正整数 `{"id": N}`，不接受 `userId`；非对象、bool/0/字符串/缺失本地 400 |
| `POST /ajax/mail/read-all` | `POST /mail/read-all` | POST | 10s | 空 payload；只影响本人当前未解决未读邮件 |

### 响应形态

- `MailPageVO`：`{records, total, pageNo, pageSize, unreadCount}`。
- `MailUnreadCountVO`：`{count}`。
- `MailReadVO`：`{id, readAt, unreadCount}`。
- `MailReadAllVO`：`{affected, unreadCount}`。
- `MailVO`：`{id, mailType, title, params, customMessage, actionPath, readAt, resolvedAt, createdAt}`；`title` 仅运营邮件有值，系统事件邮件为 `null`。
- 时间字段均为 epoch milliseconds；`MailPageVO.records` 由服务端按 `createdAt DESC` 返回。

## 前端消费契约

- 未读数、设置菜单角标、FAB 信封与独立伙伴邮件弹层只读 `window.MBMail` 的同一状态。
- 页面初始化、重新可见、窗口聚焦、`pageshow`、打开伙伴邮件弹层时刷新；不轮询。
- 未读数请求失败时数字角标隐藏并标记不可用；FAB 只按最近一次成功计数决定是否保留信封。
- `read` / `read-all` 成功后用返回的 `unreadCount` 更新同一状态，不额外请求未读数。
- 邮件正文由前端按当前 locale 渲染结构化参数；`customMessage` 覆盖默认正文，但始终以文本节点显示。
- 跳转只允许 `/buddy`、`/achievements`、`/credits`、`/learning`、`/mail`，其余 `actionPath` 不生成按钮。运营邮件无按钮时服务端返回 `actionPath=null`。
- AI 对话抽屉只承载 Chat 与记忆面板；邮件由 `#buddy-mail-popover` 独立承载。FAB 在无浮层打开时按未读分流：有未读开邮件、无未读开聊天；任一浮层打开时再点 FAB 关闭。快捷气泡“对话”始终直接打开 Chat。

## AI 用户自我介绍代理（R260）

两条代理都要求 `@user_login_required`，只操作当前登录用户在 moon-well 的档案；浏览器不能传 `userId`。成功与上游失败均原样保持 `_moonwell_proxy` 三元组 `(body, status, headers)`，失败必须进入界面可见错误态。

| magicbook 端点 | moon-well 端点 | 上游方法 | 超时 | 说明 |
| --- | --- | --- | --- | --- |
| `GET /ai/agent/profile` | `POST /ai/agent/profile` | POST | 默认 | 无业务 payload；读取本人档案 |
| `POST /ai/agent/profile/save` | `POST /ai/agent/profile/save` | POST | 默认 | 透传 `{"selfIntroduction": "..."}`；空串清空 |

### 响应形态

moon-well 返回统一 `Result`：

```json
{
  "success": true,
  "result": {
    "selfIntroduction": "我正在准备四级，喜欢科幻，希望先给结论。",
    "updatedAt": "2026-10-31T12:34:56"
  },
  "message": null,
  "code": null
}
```

- `selfIntroduction` 最多 2000 字符；未填写或已清空时为空串。
- `updatedAt` 在未填写、已清空或上游返回空对象时为 `null`。
- 空串、纯空白或 `null` 均表示清空；保存成功返回同一 VO。
- `success=false` 或上游非 2xx 时，前端展示 `message`/HTTP 错误，不得静默显示成“没有填写”。

### 前端消费契约

- 记忆面板打开时加载一次；输入框 `maxlength=2000`，计数按当前文本长度显示。
- 用户文本只能用 `.val()`/文本节点写入，禁止拼 HTML。
- 保存必须带 `X-CSRFToken`；保存中禁用保存与清空按钮，完成后恢复。
- 清空必须二次确认；失败保留原输入并展示错误。
- 不在 localStorage/sessionStorage 保存档案正文；退出登录不得继续显示上一账号档案。

## 管理员运营发信代理（R250）

五个 `/ajax/admin-mail/*` 代理全部要求登录且先校验 `current_user.role_admin()`；非管理员返回 JSON 403 且不调用上游。成功与上游失败均保持 `_moonwell_proxy` 三元组 `(body, status, headers)`，本地参数非法返回 400。

| magicbook 端点 | moon-well 端点 | 上游方法 | 超时 | 说明 |
| --- | --- | --- | --- | --- |
| `GET /ajax/admin-mail/users?keyword=&limit=` | `POST /mail/admin/users` | POST | 10s | `keyword` 最长 80 字；`limit` 默认 100、上限 500 |
| `GET /ajax/admin-mail/audience-count` | `POST /mail/admin/audience/count` | POST | 10s | 无 payload，返回全体用户人数整数；用于发送前精确预览 |
| `POST /ajax/admin-mail/send` | `POST /mail/admin/send` | POST | 30s | 只透传 `audienceType/userIds/title/body/actionPath`；`ALL` 丢弃客户端 userIds；去重后超过 5000 本地 400 |
| `GET /ajax/admin-mail/campaigns?pageNo=&pageSize=` | `POST /mail/admin/campaigns/page` | POST | 10s | `pageNo` 默认 1、上限 100000；`pageSize` 默认 20、上限 50 |
| `POST /ajax/admin-mail/recall` | `POST /mail/admin/recall` | POST | 10s | 只接受正整数 `campaignId`，不接收 operator |

### 运营响应形态

- `users`：`AdminMailUserVO[]`，字段 `userId/username/nickname/email`。
- `audience-count`：整数。
- `send`：`{campaignId, targetCount, deliveredCount, createdAt}`；整批同成同败，不返回部分成功。
- `campaigns`：`{records, total, pageNo, pageSize}`；每条含 `id/operatorUserId/audienceType/title/body/actionPath/targetCount/deliveredCount/createdAt/recalledAt/recalledBy`。
- `recall`：`{campaignId, recalled, affected}`；已撤回批次重复调用保持幂等。

## 滚动复习消费的端点（R285 / R289）

R285 只消费两个既有薄代理（均 `@user_login_required`）；R289 新增一个**只读缓存**批量代理，前端仍零直连 moon-well。后端契约权威在 moon-well：`GET /learning/srs/queue`、`GET /vocabulary/known/{word}`、`POST /vocabulary/detail/cached-batch`（R248）。

| magicbook 端点 | moon-well 端点 | 超时 | 用法 |
| --- | --- | --- | --- |
| `GET /ajax/learning/srs/queue` | `GET /learning/srs/queue` | 10s | 页面初始化拉一次，取 `Result.result` 数组；**不带 `?limit=`**——本仓代理用扁平路径且不透传 query，上游 `defaultValue=20` 正好是需要的 20 条 |
| `POST /ajax/reading-word-mark` | `GET /vocabulary/known/{word}`（`unknown=false`） | 8s | 点「认识」时发 `{"word": <lemma>, "unknown": false}`；POST 需带 `X-CSRFToken` |
| `POST /ajax/vocabulary/detail-cached-batch`（R289 新增，`routes/vocab.py`） | `POST /vocabulary/detail/cached-batch`（moon-well R248） | 10s | 队列拉到后发 `{"words": [...]}`（≤50，词形白名单过滤），取 `result` 对象（键=归一词）装配详情分页；**只读缓存，上游绝不触发生成**，未命中词不在结果里 |

### 消费字段与口径

- `LearningReviewItemVO` 只取 `word` / `meaning`（中文首义项，上游 `shortMeanings` 只读 ES 缓存）/ `contextSentence`（阅读原句）/ `contextBook`；`scheduleId`、`questionType`、`choices`、`answer`、`audioUrl` 一律不用。
- R289 详情分页只取缓存详解的 `meaning`（前 2 义项）/ `etymology` / `phrases` / `forms` / `synonyms` / `antonyms` / `slang` / `funFacts`；每词展示「基本意思 + 1 个随机模块」、每页 ≤3 行、每词 ≤4 页。`isVariant` 角标与变体说明不在此消费（分页正文不展示）。
- 上游队列筛选为 `state IN ('LEARNING','REVIEW') AND due_at <= now`（**全部到期积压，不是今日新增**），排序 `lastReviewedAt DESC, dueAt ASC`；随机由前端 Fisher-Yates 洗牌实现，上限 20 条。
- **不调用** `/ajax/reading-word-detail`（缓存 miss 会触发 LLM 生成、15~30s 且计费）、`/ajax/reading-tts*`（本次不出声）、`/ajax/learning/srs/answer`（本次不改 SRS 排程）；R289 的 `detail-cached-batch` 是唯一与详解沾边的调用，且为只读缓存（对端 R248 端点与生成链路物理分离）。
- `known/{word}` 的语义是把 `vocabulary_notebook.familiarity` 置 7 并异步把 SRS 调度行毕业 `MASTERED`；**不写 `learning_answer_log`、不计 x/20**。前端成功后只从本地轮播数组移除该词，失败保留并显示上游 `message`。
- 解包统一走 `MBApi.getJson/postJson` + `unwrapResult/unwrapStrict`（R177 单点），CSRF 走 `MBApi.csrfToken()`；服务端内容只用文本节点渲染。详情批量失败静默回退简卡（增强层语义，可观测性在代理日志）。

## 调用方契约

- 鉴权：当前用户 moon-well JWT 由 magicbook 代理注入，浏览器不接触 token。
- CSRF：浏览器调用本站 POST 代理时必须带 `X-CSRFToken`；`mail.js` 统一从 `MBApi.csrfToken()` 取值。
- 错误：moon-well `Result.message` 必须进入可见错误态，不得把失败渲染为空收件箱。
- 管理员发信：页面与五个代理先验 `role_admin()`；moon-well 再验 `credit.admin-user-ids`。全体人数未知或超过 5000 时前端不得预览/发送，服务端仍做最终校验。

## 历史接口指针

- AI 对话：[ai-agent 历史设计](../../project/_legacy/feat/ai-agent/design/magicbook-side-design.md)
- 阅读伴读：[ai-reading-companion 历史设计](../../project/_legacy/feat/ai-reading-companion/design/ai-reading-companion-implementation-plan.md)
- 伙伴悬浮球：[buddy quick actions L3](features/buddy-quick-actions.md)
