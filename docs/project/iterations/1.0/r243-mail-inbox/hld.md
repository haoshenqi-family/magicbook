# HLD — R243 站内信前端：伙伴信封、抽屉 Mail 与独立收件箱

> 状态：**设计已确认（待开发）**（2026-10-29）
> 关联：Ship MB-234 / `tBWd4R5g` · 迭代 `1.0` · 跨仓 moon-well R228。
> 设计范围：需求基线、HLD/LLD/AC；编码阶段从 `origin/develop` 建独立 worktree，并回填 L1/L2/L3。

## 1. 目标与结论

用户要的是一条低打扰、可回看的系统通知链路：伙伴负责“到访提示”，邮件负责“持久记录”。

- 伙伴头像出现信封，是未读邮件的可视提醒，不是新的领取入口；
- 点击伙伴在有未读时进入 AI 抽屉的 `Mail` 页签，无未读时保持原 `Chat` 行为；
- 设置菜单提供完整 `/mail` 收件箱；
- 邮件只通知和跳转，伙伴、成就、积分的领取仍在各自业务页面完成；
- 三类通知统一展示，不按业务各做一套消息 UI。

结论：magicbook 新增消费侧 `mail` 路由域与 `MBMail` 前端状态层，复用现有 Buddy FAB、AI 抽屉、设置菜单和 `_moonwell_proxy`；moon-well R228 提供全部邮件事实与接口。

## 2. 现状与约束

| 事实 | 对设计的影响 |
| --- | --- |
| Buddy FAB 已支持头像、拖拽吸附、hover 径向气泡与点击开关抽屉 | 信封必须叠加在现有 FAB 上，不能另盖点击层；点击逻辑必须区分 FAB 与“对话”气泡 |
| AI 抽屉当前只有 Chat、记忆面板与会话工具条 | 新增 Chat/Mail 双页签；切页签不得销毁聊天状态，也不得因打开 Mail 自动全部已读 |
| `layout.html` 与 `read.html` 加载顺序不同 | Mail 状态层不能只依赖 `MBApi`；四个阅读模板与普通 layout 必须接入同一初始化入口 |
| `readtxt.html` / `readpdf.html` 结构差异较大；`readcbr.html` 当前未挂载 Buddy 面板 | 不在阅读器里复制 Mail UI；Mail 页签与角标只在共享的 `ai_chat_panel.html` / `ai_chat.js` 内实现。本轮覆盖已挂载 Buddy 的 `layout` / `read` / `readtxt` / `readpdf`；不顺手给 `readcbr` 新增 Buddy |
| 设置菜单位于 `layout.html` | 新增 `top_mail` 与未读角标；阅读器独立骨架没有设置菜单，不影响 FAB 与抽屉收信 |
| 已有 `_moonwell_proxy` 三元组契约 | 新代理必须原样返回三元组，测试桩也必须返回三元组 |
| 现有静态 JS 文案走 `mbT` + i18n 种子/PO/MO | 所有新增 JS 文案进入生成链路与契约测试 |
| 管理员积分表单已通过 `/ajax/credit/admin-adjust` 薄代理 | 只扩展表单字段和透传 payload，不新增管理员邮件后台 |

## 3. 方案选型

| 方案 | 结论 | 理由 |
| --- | --- | --- |
| A. 复用 Buddy FAB + 抽屉双页签 + 独立 `/mail` 页面 | **采用** | 伙伴是已确认的邮差入口；抽屉适合“顺手看一眼”，独立页适合完整回看；不引入新浮层体系 |
| B. 单独做全站通知中心浮窗 | 否决 | 与 Buddy 已有交互竞争，用户已明确“伙伴 + 专门邮件功能” |
| C. 点伙伴直接打开 `/mail` 新页面 | 否决 | 打断当前阅读/聊天上下文；用户要“点击伙伴可以收信”，抽屉内先看更轻 |
| D. 有未读就自动把最近邮件标已读 | 否决 | 打开页签不等于阅读内容，会造成“没看却消失”的不可信状态 |
| E. 前端轮询或 WebSocket 实时推送 | 否决（本轮） | 三类事件频率低；页面初始化、可见/聚焦刷新已足够，避免新增常驻连接与后台任务 |
| F. 邮件内直接领取伙伴/成就 | 否决 | 扩大权限面；用户已确认信中只跳转 |

## 4. 架构

```mermaid
flowchart LR
    M[Moon-well R228 /mail/*] --> P[cps/routes/mail.py 薄代理]
    P --> S[MBMail 前端状态层]
    S --> F[Buddy FAB 信封]
    S --> N[设置菜单角标]
    S --> D[AI 抽屉 Mail 页签]
    S --> I[/mail 独立收件箱]
    C[credits.js 管理员表单] --> A[/ajax/credit/admin-adjust]
    A --> M2[Moon-well R228 管理员通知]
```

边界：

- moon-well 拥有邮件事实、幂等、已读/已解决与三类投递；
- magicbook 拥有入口、渲染、locale 文案、交互状态与错误呈现；
- 邮件不得反向授予业务权限；
- `/mail` 页面与抽屉共用同一 API 与状态层，不各自拼装一套数据。

## 5. 关键不变量

1. 信封与角标只由 `unreadCount > 0` 驱动。
2. 三个未读展示位（FAB、设置菜单、抽屉页签）只读 `MBMail` 的同一计数，不各自请求后自行保留不同值。
3. FAB 点击行为：抽屉关闭时，有未读打开 Mail，无未读打开 Chat；抽屉已打开时沿用原有关闭行为。
4. “对话”快捷气泡永远显式打开 Chat，不能被 FAB 的未读分流误送进 Mail。
5. 打开 Mail 页签不标已读；只有展开单封才调用已读接口。
6. 已解决邮件保留历史，不计入未读；前端不自行推断 resolved 状态。
7. 邮件列表与未读数失败必须显示错误态；不得把失败渲染为空收件箱。失败时数字 badge 隐藏并标记不可用，FAB 信封只按最近一次成功计数决定是否保留。
8. 邮件正文只以文本节点渲染结构化参数和自定义纯文本，不把服务端字符串拼进 `innerHTML`。
9. 跳转只允许 `/buddy`、`/achievements`、`/credits`；不信任服务端返回的其他路径。
10. 所有 `/ajax/mail/*` 代理保持 `_moonwell_proxy` 三元组，不新增二元组返回分支。
11. 不新增后台任务、定时器、MQ、WebSocket 或 localStorage 邮件正文缓存。

## 6. 接口摘要

| magicbook 代理 | moon-well | 用途 |
| --- | --- | --- |
| `GET /ajax/mail/unread-count` | `POST /mail/unread-count` | 全站未读数 |
| `GET /ajax/mail/page?pageNo&pageSize` | `POST /mail/page` | 抽屉与 `/mail` 分页 |
| `POST /ajax/mail/read` | `POST /mail/read` | 展开单封时标已读 |
| `POST /ajax/mail/read-all` | `POST /mail/read-all` | 全部已读 |
| `POST /ajax/credit/admin-adjust` | `POST /credit/admin/adjust` | 扩展 `notify` / `notificationMessage` |

详细字段、页面结构、状态同步与测试见 [LLD](./lld.md)；验收见 [AC](./ac/acceptance.md)。

## 7. 跨仓分工

| 仓库 | 责任 |
| --- | --- |
| moon-well R228 | `user_mail`、三类投递/解决、分页/未读/已读接口、管理员 DTO 扩展、hedwig 回填 |
| magicbook R243 | `cps/routes/mail.py`、`MBMail` 状态层、FAB 信封、抽屉 Mail、`/mail` 页面、设置入口、管理员表单、i18n 与错误态 |

契约守卫：

- magicbook：每个 mail 代理测试桩必须返回 `(body, status, headers)`；新代理不得返回二元组。
- magicbook：i18n 种子 key、zh PO 与 MO 三处一致；新增 `mbT` 字面量不得静默回英文。
- magicbook：FAB 拖拽 `pointerdown/move/up` 行为有回归断言；`chat` 气泡显式打开 Chat。
- moon-well：`MailController` 显式 `Result`，唯一键并发与三态 SQL 有测试。

## 8. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| 信封角标拦截 FAB 点击或拖拽 | 角标 `pointer-events:none`；不新增覆盖层；保留 wrap 命中区与拖拽阈值测试 |
| 有未读时“对话”气泡误开 Mail | FAB 与气泡使用两个明确入口；气泡 `dispatchBubbleAction("chat")` 直接 `openDrawer("chat")` |
| 打开 Mail 页签就全部已读，用户错过内容 | 只展开单封才已读；页签打开仅拉列表；全部已读必须显式点击 |
| 各组件计数漂移 | `MBMail` 单例状态 + 统一渲染；所有变更接口返回最新 `unreadCount` |
| 阅读器模板缺少 `MBApi` 或 i18n | 在共享 `ai_chat.js` 内封装请求与 CSRF 探测；四个模板统一 include 顺序与初始化 |
| 接口失败被渲染成空态 | 区分 `loading / ready / error`；错误态显示 message 与重试，不用空数组兜底 |
| 邮件正文 XSS | 结构化参数与自定义正文全部 `text()` / `textContent`；不拼 HTML |
| 跳转被伪造外链 | 前后端双白名单；非白名单只显示正文，不生成按钮 |
| 管理员误发负数“到账”通知 | 表单负数时禁用并清空通知；moon-well 再拒绝 `notify && amount<=0` |
| 登出后残留上一账号邮件 | 页面级内存状态，不落 localStorage；登出/换页自然销毁 |

## 9. 实施难度评估

**总体：中等偏上**。难点不在页面数量，而在三件事同时成立：跨仓契约、三类业务事件的投递/解决事务、以及复用现有 Buddy 交互而不破坏拖拽与聊天气泡。

| 工作块 | 难度 | 主要原因 |
| --- | --- | --- |
| moon-well 邮件事实、幂等与查询 | 中高 | 新表 + 唯一键并发 + 三态口径；分页/已读/全部已读要统一 |
| 伙伴、成就、积分接线 | 高 | 伙伴是派生提示需独立事务；成就当前走 `AFTER_COMMIT + @Async`，需补事务边界；积分必须同事务落账 |
| magicbook FAB、抽屉双页签与统一未读状态 | 中高 | 共享面板覆盖普通页与三种阅读器；拖拽、气泡、聊天分流不能回归 |
| `/mail` 独立页与设置入口 | 中 | 页面本身直接，但分页、空态/错误态、已读联动与移动端要一起验收 |
| 管理员通知表单与代理扩展 | 中低 | 复用既有积分代理，新增字段与负数禁用逻辑 |
| i18n、守卫与回归测试 | 中 | 文案链路五步、代理三元组、FAB 行为与跨模板结构断言都要覆盖 |

粗估 **5–7 人日**（不含真机验收与等待部署），其中后端事务接线和前端 FAB/抽屉回归占主要成本。若第二轮决定缩减为“只做 `/mail` + 设置入口，不做 FAB 信封/抽屉 Mail”，可降到约 3 人日，但不满足当前“伙伴收信”的核心诉求。

## 10. 回滚与发布

- moon-well R228 先上线，旧前端不调用新接口也不受影响。
- magicbook R243 后上线；关闭入口只需撤掉 FAB/设置/`/mail` 与代理，不影响既有 Buddy Chat。
- 回滚代码不删除 moon-well 已发出的邮件历史；再次上线仍可读取。
- 管理员表单字段为向后兼容新增项，旧请求不带 `notify` 时默认不通知。

## 11. 文档四问预答

- **能力变了吗？** 是：新增伙伴信封、抽屉 Mail、独立 `/mail` 与管理员到账通知选项；开发阶段更新 L1。
- **契约变了吗？** 是：新增四个 mail 代理与管理员 DTO 字段；开发阶段更新 L2/接口说明。
- **实现/边界变了吗？** 是：开发阶段新增 `companion/features/mail-inbox.md` 与 `credit` 侧管理员通知说明。
- **本次怎么实现？** 本文件 + [LLD](./lld.md) + [AC](./ac/acceptance.md)，编码阶段回填状态与交付四问。

## 12. 已确认口径（2026-10-29）

1. 管理员积分通知允许可选自定义正文，最多 500 字。
2. 上线只为尚未领取的 `hedwig` 补发，历史成就与历史积分不补发。
3. 抽屉内打开 Mail 页签不标已读、展开单封才标已读。
4. 已解决邮件保留历史但不再计入未读。
5. 伙伴派生通知失败不阻断花名册，成就/积分通知失败回滚业务。
6. `readcbr` 当前没有挂载 Buddy 面板，本轮不扩展。
7. 产品归 companion，magicbook 代码使用独立 `mail` 域。
