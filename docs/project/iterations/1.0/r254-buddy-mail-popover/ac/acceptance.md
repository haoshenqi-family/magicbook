# AC - R254 伙伴邮件弹层与 AI 对话抽屉分离

> 状态：**开发完成待部署**（2026-10-29；定向 138 passed，正式发布态全量 1203 passed / 0 failed）
> 上层设计：[lld.md](../lld.md)

## A. 浮层结构

- [x] AI 伴读抽屉只保留 Chat 与记忆面板，不含 Mail tab、Mail pane、邮件列表或邮件操作。
- [x] 登录态渲染独立 `#buddy-mail-popover`，包含标题、关闭、未读数、全部已读、加载/空/错误/列表与查看全部。
- [x] 匿名页面不渲染邮件弹层、FAB 信封或邮件入口。
- [x] `/mail` 完整收件箱保持可用。

## B. 点击路由

- [x] 无未读、无浮层时点击 FAB 打开 AI 对话。
- [x] 有最近成功未读、无浮层时点击 FAB 打开独立邮件弹层。
- [x] 邮件弹层已打开时点击 FAB 关闭弹层。
- [x] AI 抽屉已打开时点击 FAB 关闭抽屉。
- [x] 悬停快捷气泡“对话”始终打开 AI 对话，不受未读影响。

## C. 互斥与邮件状态

- [x] 打开邮件弹层会关闭 AI 抽屉。
- [x] 打开 AI 抽屉会关闭邮件弹层。
- [x] 打开邮件弹层不自动已读。
- [x] 展开单封才调用 `MBMail.markRead(id)`。
- [x] “全部已读”后弹层、FAB、设置菜单角标与 `/mail` 同步更新。
- [x] 最近 5 封、空态、错误重试与“查看全部”入口可用。

## D. 回归与发布

- [x] `test_mail_ui_r243.py`、`test_admin_mail_r250.py`、`test_buddy_animations_r244.py`、`test_i18n_seed_contract.py` 全绿。
- [x] 邮件、代理、管理员发信、伙伴动效、i18n、账号 IA、首页壳与 API 契约合计 138 passed。
- [x] `node --check` 与 `git diff --check` 全绿。
- [x] 正式发布态全量 `pytest tests/` 为 1203 passed / 0 failed。
- [ ] merge/push 后 fnOS 构建、app-manager 部署、容器健康与镜像 SHA 核验通过，状态回填为“已上线待验收”。
