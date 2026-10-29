# LLD — R243 站内信前端：伙伴信封、抽屉 Mail 与独立收件箱

> 状态：**前后端已实现，待验收**（2026-10-29；moon-well R228 + magicbook R243，未 push、未部署）
> 上层设计：[hld.md](./hld.md) · 验收：[ac/acceptance.md](./ac/acceptance.md)
> 需求基线：[companion R243](../../../../product/companion/requirements.md)
> 后端契约：`moon-well` 仓库 `docs/project/iterations/1.0/r228-mail-inbox/lld.md`（跨仓文档不写相对链接）

## 1. 代码布局

实际新增：

```text
cps/routes/mail.py                 # /ajax/mail/* 薄代理
cps/templates/mail.html            # 完整收件箱
cps/static/js/mail.js              # MB Mail 状态层 + /mail 页面控制器
cps/static/css/mail.css            # 抽屉 Mail、/mail、FAB 信封与角标样式
cps/static/css/ai_chat.css         # 与 R244 隐藏/唤回动画共用的 FAB 样式
tests/test_mail_proxy_r243.py      # 代理三元组、参数与鉴权
tests/test_mail_ui_r243.py         # 模板/JS 结构、FAB 分流、R244 联动、页签与 i18n
```

接线点：

- `cps/routes/__init__.py`：注册 `mail`
- `cps/routes/credit.py`：管理员积分代理无需改路径，只透传新增字段
- `cps/templates/layout.html`：设置菜单 `top_mail` + 角标；引入 `mail.css`，并在 `common/api.js` 之后、`ai_chat_panel.html` 之前引入 `mail.js`（共享面板和页面脚本都依赖 `MBMail`）
- `cps/templates/ai_chat_panel.html`：FAB 信封节点、抽屉 Chat/Mail 页签、Mail 列表骨架
- `cps/templates/read.html`、`readtxt.html`、`readpdf.html`：共享面板的脚本/样式接线；三者在 `ai_chat_panel.html` 之前引入 `common/api.js` 与 `mail.js`（`readcbr` 当前未挂载 Buddy，本轮不扩展）
- `cps/static/js/ai_chat.js`：FAB 分流、`openDrawer(tab)`、Chat 气泡显式打开 Chat、Mail 页签控制器
- `cps/templates/credits.html`、`cps/static/js/credits.js`：管理员通知复选框与正文
- `cps/templates/i18n_seed.html`、zh `.po` / `.mo`

## 2. 代理契约

```python
@web.route("/ajax/mail/unread-count", methods=["GET"])
@user_login_required
def mail_unread_count():
    body, status, headers = _moonwell_proxy(
        "/mail/unread-count", None, 10, "mail unread count", method="POST")
    return body, status, headers

@web.route("/ajax/mail/page", methods=["GET"])
@user_login_required
def mail_page_proxy():
    page_no = _positive_int(request.args.get("pageNo"), default=1, maximum=100000)
    page_size = _positive_int(request.args.get("pageSize"), default=20, maximum=50)
    body, status, headers = _moonwell_proxy(
        "/mail/page", {"pageNo": page_no, "pageSize": page_size}, 10, "mail page")
    return body, status, headers

@web.route("/ajax/mail/read", methods=["POST"])
@user_login_required
def mail_read():
    payload = request.get_json(silent=True) or {}
    mail_id = payload.get("id")
    if not isinstance(mail_id, int) or isinstance(mail_id, bool) or mail_id <= 0:
        return jsonify({"success": False, "message": "id is required"}), 400
    return _moonwell_proxy("/mail/read", {"id": mail_id}, 10, "mail read")

@web.route("/ajax/mail/read-all", methods=["POST"])
@user_login_required
def mail_read_all():
    return _moonwell_proxy("/mail/read-all", {}, 10, "mail read all")
```

- `_positive_int` 非法值归一为默认值，前端不因参数错误看到 500。
- 所有成功/失败路径都返回 `_moonwell_proxy` 的三元组；本地参数错误返回既有 Flask 二元组（400），这是代理前的校验分支，不伪装成上游响应。
- `read` 不接受 `userId`，归属由 moon-well 登录上下文决定。

## 3. 前端状态层 `MBMail`

在 `mail.js` 暴露一个只读 API：

```text
window.MBMail = {
  refreshUnread(): Promise<number>,
  loadPage(pageNo, pageSize): Promise<MailPage>,
  markRead(id): Promise<MailReadResult>,
  markAllRead(): Promise<MailReadAllResult>,
  openInbox(): void,
  subscribe(listener): unsubscribe,
  getState(): { unreadCount, lastKnownUnreadCount, status, error, lastUpdatedAt },
  getUnreadForRouting(): number
}
```

状态：

```text
status: "idle" | "loading" | "ready" | "error"
unreadCount: number | null
error: string | null
```

- `unreadCount=null` 表示尚未成功取得，不能当成 0；信封与角标只在 `ready && unreadCount > 0` 显示。
- 请求失败时进入 `error`，保留 `lastKnownUnreadCount` 仅用于“FAB 信封是否保留”的视觉提示；数字 badge 隐藏并加不可用状态。从未成功时三处不显示“无邮件”，而是显示错误提示。
- `unreadCount` 是当前可展示值；`lastKnownUnreadCount` 只在 `error` 时参与 FAB 分流与信封显隐，不用于任何数字 badge。
- 变更接口成功后用响应中的最新 `unreadCount` 更新状态，再广播给 FAB、设置菜单、抽屉与 `/mail`。
- `mail.js` 与现有共享脚本统一依赖 `window.MBApi`（`common/api.js`）：CSRF 探测复用 `MBApi.csrfToken()`，不新增第四套 DOM 选择器；`layout.html`、`read.html` 已载入，`readtxt.html`、`readpdf.html` 必须补载且排在 `ai_chat_panel.html` 之前。
- `mail.js` 必须在共享面板脚本之前载入：`ai_chat.js` 初始化 FAB 分流时读取 `window.MBMail`，晚载入会把“有未读进 Mail”静默降级成“永远进 Chat”。
- `mail.js` 在登录态下的 `layout` / `read` / `readtxt` / `readpdf` 四类页面初始化 `MBMail`；匿名阅读不加载 Mail CSS/JS、不漏出信封或页签。`/mail` 页面不重复初始化第二套计数，只复用同一状态层与 DOM 订阅。
- 请求使用 `fetch(..., credentials: "same-origin")` 与 `X-CSRFToken`；`GET` 不发送 CSRF 头。`MBApi` 缺失或 POST 取不到 CSRF 时，由页面错误态明确呈现，不静默。
- 扩展 `tests/test_common_api_contract.py`：四个挂载 Buddy 的模板都载入 `common/api.js` 且先于共享面板；`mail.js` 只经 `MBApi` 取 CSRF。

### 3.1 刷新时机

1. 页面初始化后一次。
2. `visibilitychange` 变为 visible 时一次。
3. `window.focus` 时一次（同一 1 秒窗口内去重）。
4. 抽屉切到 Mail 页签时一次。
5. 单封已读、全部已读成功后用响应计数更新，不额外请求。
6. 页面 `pageshow`（bfcache 返回）时一次。

不设置 `setInterval`；不在后台标签页高频请求。

## 4. FAB 信封与点击分流

### 4.1 结构

`ai_chat_panel.html` 的 `#ai-companion-fab-wrap` 内新增：

```html
<span id="ai-companion-mail-badge" class="ai-mail-badge" hidden aria-hidden="true">✉</span>
```

`mail.css`：

- 角标绝对定位于 FAB 左上，`pointer-events:none`；右上留给 R244 隐藏 ✕，两者不重叠；
- 无未读时 `hidden`；
- 有未读时只显示信封，不显示数字，避免角标过大遮挡头像；
- 小屏与拖拽吸附后仍跟随 wrap；
- `z-index` 低于抽屉，但高于 FAB 头像。
- `✉` 只是视觉字符；节点已带 `aria-hidden=true`，可读状态由页签与设置菜单 badge 的文本提供。

### 4.2 点击

`ai_chat.js` 把 `openDrawer()` 统一为：

```text
openDrawer(tab = "chat")
```

行为：

1. 打开抽屉并激活指定页签。
2. `mail` 页签触发 `MBMail.refreshUnread()` 与 `loadPage(1, pageSize)`。
3. 抽屉已打开时点击 FAB 仍关闭，不重新分流。

FAB click：

```text
var unread = window.MBMail && typeof window.MBMail.getUnreadForRouting === "function"
  ? window.MBMail.getUnreadForRouting() : 0;
if drawer open: closeDrawer()
else if unread > 0: openDrawer("mail")
else: openDrawer("chat")
```

`getUnreadForRouting()` 只在最近一次成功计数大于 0 时返回该值；`error` 且从未成功时返回 0，`error` 但有旧值时返回旧值。这样接口故障不会把有旧未读的用户静默送进 Chat，也不会把未知状态当成 0 数字展示。

气泡“对话”：

```text
dispatchBubbleAction("chat") -> openDrawer("chat")
```

必须显式打开 Chat，不能 `trigger("click")` 复用 FAB 分流。其余气泡动作保持现状。

### 4.3 拖拽

`initBuddyFabDrag` 的 wrap 命中区、6px 拖动阈值、延迟 `setPointerCapture`、吸附与 `dragged` 抑制 click 逻辑不变。信封节点 `pointer-events:none`，不参与拖拽。

### 4.4 R244 隐藏/唤回联动

- 可见 FAB 只显示 R243 的 `#ai-companion-mail-badge` 信封，不再叠加 R244 `.buddy-has-letter::before` 红点，避免同一未读出现两个提示。
- 伙伴隐藏后，`MBMail` 渲染时调用 `window.AICompanion.syncLetterBadge()`；仅当 FAB 处于 `buddy-hidden` 且仍有未读时，才把同一状态映射到右缘唤回药丸的 `.ai-letter-badge`，不播放收不到主体的飞信动画。
- 打开抽屉时清理 R244 的唤回提示状态；服务的未读事实仍只由 R243 `MBMail` 持有，页签/设置/FAB/药丸不维护独立计数。
- 伙伴复原时清除药丸红点并恢复可见 FAB 信封；若邮件仍未读，R243 信封继续存在。

## 5. AI 抽屉双页签

### 5.1 结构

抽屉 header 下新增页签：

```html
<div id="ai-companion-tabs" role="tablist">
  <button id="ai-tab-chat" role="tab" data-tab="chat">Chat</button>
  <button id="ai-tab-mail" role="tab" data-tab="mail">Mail <span id="ai-tab-mail-badge" hidden></span></button>
</div>
<section id="ai-chat-pane" role="tabpanel">... existing chat ...</section>
<section id="ai-mail-pane" role="tabpanel" hidden>...</section>
```

Chat 区域原节点不搬家、不销毁，只加 pane 容器；会话、输入框、语音、记忆面板与发送逻辑不变。

### 5.2 Mail 页签

- 顶部：未读数 + “全部已读”按钮。
- 列表：最近 5 封，按 `createdAt DESC`；每行显示类型标题、摘要、时间、未读点。
- 单封：点击行展开正文与跳转按钮；首次展开调用 `markRead(id)`，成功更新该行状态与未读数。
- 已解决邮件仍显示，标题旁标“已完成/已领取”的轻量状态；不显示未读点。
- 底部：“查看全部”跳 `/mail`。
- 空态：无邮件时显示“还没有邮件”，不是错误。
- 错误态：显示接口 message 与“重试”按钮；不得用空态替代。

打开 Mail 页签本身只加载列表，不标已读；切回 Chat 再切回 Mail 不重复拉取已展开单封的正文（页面级缓存只在内存中）。

### 5.3 页签状态

- 初始默认 Chat。
- 有未读时 FAB 点击进入 Mail；用户手动切页签后以手动选择为准。
- 关闭抽屉不重置页签；下次 FAB 点击仍按未读分流。
- 记忆面板打开时切到 Mail，先关闭记忆面板，避免两个覆盖层叠放。

## 6. 设置菜单

`layout.html` 设置下拉新增：

```html
<li>
  <a id="top_mail" href="{{ url_for('web.mail_inbox_page') }}">
    <span class="glyphicon glyphicon-envelope"></span> {{_('Mail')}}
    <span id="top-mail-badge" class="badge" hidden></span>
  </a>
</li>
```

- 仅登录用户可见，位置在“成就”之前或之后均可，但必须与伙伴/积分同组。
- 角标显示未读数字；`0` 时隐藏。
- 设置菜单只在 `layout.html` 存在；阅读器独立骨架不渲染该入口，FAB 仍可收信。

## 7. 独立 `/mail`

### 7.1 路由

`cps/routes/mail.py`：

```text
GET /mail -> render_title_template("mail.html", title=_("Mail"))
```

Flask endpoint 名必须区分页面与代理：页面函数命名 `mail_inbox_page`（endpoint `web.mail_inbox_page`），分页代理命名 `mail_page_proxy`。禁止两者都叫 `mail_page`，否则 `url_for('web.mail_page')` 会命中代理或直接抛 endpoint 冲突。

`@user_login_required`；匿名访问走既有登录跳转。

### 7.2 页面

- 标题 + 未读计数 + “全部已读”。
- 分页列表，默认每页 20，页大小 10/20/50 可选（若首版不做选择器，固定 20）。
- 单封卡片：默认折叠；点击展开正文与跳转按钮；展开时标已读。
- 已解决邮件显示历史，但无未读点。
- 分页按钮：上一页/下一页 + 当前页/总页数；空列表禁用。
- 空态、加载态、错误态分离。
- 页面继承 `layout.html`，使用其已有 `input[name=csrf_token]` 与 `common/api.js`；不另造 `#mail-csrf`。

### 7.3 正文渲染

按 `mailType`：

| 类型 | 默认标题 | 默认正文 |
| --- | --- | --- |
| `BUDDY_CLAIMABLE` | 新伙伴来访 | `{buddyName}` 正在等你领取，去伙伴页看看吧。 |
| `ACHIEVEMENT_UNLOCKED` | 成就解锁 | 你解锁了「{achievementName}」：{description}（+{points} XP）。 |
| `CREDIT_GRANTED` | 积分到账 | 管理员为你发放了 {amount} 积分，当前余额 {balanceAfter}。 |

- `customMessage` 非空时覆盖默认正文，但仍按纯文本渲染。
- 标题始终由前端按类型生成，不使用服务端标题字段（当前契约没有标题）。
- 参数缺失时显示稳定的通用正文，不抛 JS 异常。

### 7.4 跳转

`actionPath` 映射到按钮文案：

- `/buddy` → 去伙伴页
- `/achievements` → 查看成就
- `/credits` → 查看积分

前端再次校验 path 是否在上述集合；不合法时不渲染按钮。

## 8. 管理员积分通知表单

`credits.html` 在金额与原因后新增：

```html
<label><input type="checkbox" id="credit-admin-notify"> {{_('Send arrival notification')}}</label>
<textarea id="credit-admin-notification-message" maxlength="500"
          placeholder="{{_('Optional message (plain text)')}}"></textarea>
```

- 金额变化时：`amount <= 0` → 复选框取消勾选、禁用，正文清空并禁用。
- 正数时恢复可用，但不默认勾选。
- 提交 payload：

```json
{"userId": 7, "amount": 500, "reason": "...", "notify": true,
 "notificationMessage": "..."}
```

- `notify=false` 时不发送 `notificationMessage`（或发送空串），避免误导。
- 确认框追加“并发送到账通知”提示。
- 成功/失败沿用现有 alert；失败必须显示上游 message。
- 表单 reset 后恢复通知复选框与正文的初始禁用/清空状态。

## 9. i18n

- 模板 `_()` 词条：`Mail`、`Chat`、`All mail`、`Mark all as read`、`No mail yet`、`Failed to load mail`、`Retry`、`View all`、`Send arrival notification`、`Optional message (plain text)` 等。
- JS 动态文案统一用调用时 `t()` / `mbT()`；新增字面量先写入 `i18n_seed.html`，再跑 `scripts/generate_i18n_seed.py` 更新清单。
- zh `messages.po` 补齐所有新 msgid，只编译 `zh_Hans_CN` 的 `.mo`；不得用全量 `pybabel compile -f` 触发其他 locale 历史占位符错误。
- 守卫：`tests/test_i18n_seed_contract.py` 全绿，新增 `mbT` 字面量无遗漏。

## 10. 可访问性与移动端

- 页签用 `role=tab` / `aria-selected` / `aria-controls`，键盘可切换。
- 信封角标 `aria-hidden=true`，未读信息由页签文本和设置菜单 badge 提供可读状态。
- 展开卡片用真实 `button`，带 `aria-expanded`。
- 移动端 FAB 点击仍可进 Mail；hover 气泡不是唯一入口。
- 抽屉 Mail 页签在 420px 覆盖式抽屉内不横向溢出；列表长文本换行。

## 11. 测试计划

### 11.1 代理

- 四个代理均登录门禁；匿名不命中上游。
- `/ajax/mail/page` 参数归一：缺省 1/20、超过上限截到 50、非法字符串回落默认。
- `read` 的 `id` 缺失/0/字符串/布尔 → 400，不打上游。
- 四个代理成功路径均返回 `_moonwell_proxy` 三元组；桩返回三元组。
- 上游 503/业务失败原样透传，body/status/headers 不被改写。

### 11.2 UI 结构

- `layout.html` 含 `top_mail` 且仅登录用户渲染。
- `ai_chat_panel.html` 含 FAB 信封、双页签与 Mail 骨架；信封 `pointer-events:none`。
- `read.html` / `readtxt.html` / `readpdf.html` 都接入 `mail.js` / `mail.css` 与共享面板；`readcbr` 保持现状。
- `readtxt.html` / `readpdf.html` 的 `common/api.js` 位于 `ai_chat_panel.html` 之前；`layout.html` / `read.html` 的既有顺序不回归。
- `/mail` 页面含空态、错误态、重试、分页与全部已读。
- 管理员表单含通知复选框与正文，负数禁用逻辑存在于 `credits.js`。

### 11.3 行为

- Node 执行 `ai_chat.js` 的分流函数：有未读 → Mail，无未读 → Chat，抽屉已开 → 关闭。
- `dispatchBubbleAction("chat")` 始终 Chat，即使有未读。
- 打开 Mail 页签不调用 `read`；展开单封才调用 `read`。
- 单封已读/全部已读后 `MBMail` 计数与三处 badge 同步。
- 接口失败进入 error 态；角标不伪装成 0。
- 伙伴隐藏后同一未读映射到唤回药丸；可见 FAB 不额外生成第二个红点。
- 跳转 path 白名单：合法三类生成按钮，外链/协议相对/危险协议不生成。
- 结构化参数与 `customMessage` 以文本节点渲染，HTML 字符串不执行。

### 11.4 回归

- FAB 拖拽、吸附、位置记忆、hover 气泡与键盘聚焦。
- Chat 会话列表、发送、语音、记忆面板、站内链接渲染。
- 设置菜单既有入口与角色显隐。
- 积分页既有余额、档位、流水与管理员调整。
- i18n 种子/PO/MO 契约。

## 12. 文档回填

- L1：开发阶段更新 `product/readme/companion.md`、`credit.md`，新增 `mail` 用户手册（若产品决定保留独立 mail L1）。
- L2：开发阶段更新 `companion/interface.md` 或新建 `mail/interface.md`，并更新 `credit/interface.md` 的管理员 DTO。
- L3：开发阶段新增 `companion/features/mail-inbox.md`、`credit/features/admin-notification.md`。
- LLD：本文件状态行随开发/上线回填。

## 13. 已知取舍

- 首版抽屉只显示最近 5 封，完整历史在 `/mail`；不把抽屉做成第二套完整收件箱。
- 不做实时推送；低频通知用页面可见/聚焦刷新足够，避免新增常驻连接。
- 不展示邮件数字角标在伙伴头上，只显示信封；数字在设置菜单与抽屉页签。
- `/mail` 首版固定每页 20；若用户后续要求可选页大小，再迭代，不阻塞本轮。
