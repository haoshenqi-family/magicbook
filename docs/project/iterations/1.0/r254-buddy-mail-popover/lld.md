# LLD - R254 伙伴邮件弹层与 AI 对话抽屉分离

> 状态：**已上线待验收**（2026-10-29；实现/部署 `96a75611`；定向 138 passed，正式发布态全量 1203 passed / 0 failed；容器 healthy）
> 需求基线：[companion R254](../../../../product/companion/requirements.md)
> 验收：[ac/acceptance.md](./ac/acceptance.md)

## 1. 结论

R243 把 Mail 做成 AI 对话抽屉里的第二个页签，导致“收信”和“与 AI 对话”共用一个浮层。R254 将邮件从 `#ai-companion-drawer` 完全拆出：

- AI 抽屉只保留 Chat、会话工具与记忆面板；
- 登录态新增独立 `#buddy-mail-popover`；
- FAB 有未读时开邮件弹层，无未读时开 AI 对话；
- 两个浮层互斥，任一打开时再点 FAB 关闭当前浮层；
- 快捷气泡“对话”仍固定调用 `openDrawer()`。

## 2. 代码落位

```text
cps/templates/ai_chat_panel.html   # 删除 Mail tab/pane，新增独立邮件弹层
cps/static/js/ai_chat.js           # FAB 分流、弹层开关、最近 5 封预览
cps/static/js/mail.js              # 统一未读状态映射到独立弹层
cps/static/css/mail.css            # 桌面右下浮层、移动全屏、列表与状态样式
tests/test_mail_ui_r243.py         # 结构、路由、互斥、未读与匿名守卫
```

## 3. FAB 路由

纯函数：

```js
function chooseFabTarget(panelOpen, unread) {
  if (panelOpen) return null;
  return Number(unread) > 0 ? "mail" : "chat";
}
```

事件处理：

| 当前状态 | 点击 FAB |
| --- | --- |
| 邮件弹层或 AI 抽屉已打开 | 关闭当前伙伴浮层 |
| 都关闭且最近成功未读数 > 0 | `openBuddyMail()` |
| 都关闭且无未读 | `openDrawer()` |

FAB 只负责伙伴入口分流；`dispatchBubbleAction("chat")` 不走 FAB click，始终直接打开 Chat。

## 4. 独立邮件弹层

模板骨架：

```html
<aside id="buddy-mail-popover" role="dialog"
       aria-labelledby="buddy-mail-title" aria-hidden="true" hidden>
  <header>...</header>
  <div class="buddy-mail-tools">...</div>
  <div id="buddy-mail-loading">...</div>
  <div id="buddy-mail-empty">...</div>
  <div id="buddy-mail-error">...</div>
  <div id="buddy-mail-list"></div>
  <footer>查看全部</footer>
</aside>
```

行为：

- 打开时设置 `hidden=false`、`aria-hidden=false`，并调用 `closeDrawer()`；
- `openDrawer()` 反向调用 `closeBuddyMail()`，保证互斥；
- 最近 5 封复用 `MBMail.loadPage(1, 5)` 与 `buildMailItem()`；
- 打开弹层不调用已读；展开单封才调用 `MBMail.markRead(id)`；
- “全部已读”复用 `MBMail.markAllRead()`，成功后刷新本地预览；
- 列表失败显示上游 message 与重试，不把失败渲染为空态。

## 5. 样式与可达性

- 桌面：右下角固定浮层，宽 `min(420px, calc(100vw - 48px))`，底部留出 FAB 命中区。
- 移动端（≤600px）：全屏覆盖，关闭与“全部已读”触控目标至少 44px。
- `[hidden] { display:none !important; }` 防止 flex 样式覆盖 hidden。
- 弹层使用 `role=dialog`、标题关联与可见关闭按钮；列表滚动不带动页面滚动。
- 不新增动画，不改变 `prefers-reduced-motion` 下的伙伴动效。

## 6. 状态与边界

- `window.MBMail` 仍是唯一未读事实来源；FAB 信封、设置菜单角标、弹层计数与 `/mail` 共享状态。
- 不新增轮询、WebSocket、后台任务、存储缓存或第二套未读计数。
- `/mail` 页面、管理员运营发信、R250 `ADMIN_ANNOUNCEMENT` 渲染不变。
- 匿名用户不渲染 `#buddy-mail-popover`、FAB 信封或邮件入口。
- `readcbr.html` 仍不挂 Buddy，不在本轮扩展。

## 7. 测试

- 模板守卫：AI 抽屉无 Mail tab/pane；登录态有独立弹层；匿名为空。
- Node 守卫：`chooseFabTarget(false, 0) = chat`、`(false, n>0) = mail`、`(true, *) = null`。
- 源码守卫：邮件路由执行 `openBuddyMail()`，不执行 `openDrawer("mail")`。
- 互斥守卫：`openBuddyMail()` 关抽屉，`openDrawer()` 关弹层。
- 快捷气泡守卫：chat 分支直接 `openDrawer("chat")`。
- 已读守卫：打开弹层/加载预览不调用 `markRead`，只有卡片 `onOpen` 调用。
- 回归：`test_mail_ui_r243.py`、`test_admin_mail_r250.py`、`test_buddy_animations_r244.py`、`test_i18n_seed_contract.py`。
