# UI 信息架构与导航分组（L3 实现说明）

> 建立：2026-10-29（R251）。读者是**要改 MagicBook 顶栏、侧栏或移动导航的人**；
> 用户视角见 L1 [`product/readme/library.md`](../../readme/library.md)，
> 本次实现与取舍见 LLD
> [`project/iterations/1.0/r251-ui-ia/lld.md`](../../../project/iterations/1.0/r251-ui-ia/lld.md)。

## 1. 产品层规则

所有可测试的信息架构规则集中在 `cps/ui_ia.py`：

| 函数 | 作用 | 不应放在模板里的原因 |
| --- | --- | --- |
| `nav_domain(path, page)` | 返回唯一一级域 | 模板里第二份路径名单会与路由漂移 |
| `l2_nav_groups(domain, path)` | 返回账号/管理的分组 L2 链接与唯一 active | 页面不能自己复制一份 L2 名单 |
| `shelf_nav_group(name)` | 识别分级 / 媒体 / 默认书架 | 规则需要单测与安全兜底 |
| `shelf_level_sort(shelves)` | 阶号按数值排序 | 字符串排序会把阶10排在阶2前 |

`cps/jinjia.py` 只把四个函数注册为 Jinja filter。新增分类规则先改 Python，
再让模板消费，不直接在 `layout.html` 写新正则。

## 2. 唯一一级域

优先级固定为：

```text
home
learning
account
admin
library
unknown ("")
```

注意事项：

- 账号路径必须优先于书库路径：`/reading/settings` 是账号，不是阅读页。
- `/stats`、`/login` 等未知页面返回空值，不得默认成书库。
- 阅读器路径 `/read/<id>` 属于书库，用户从书目进入阅读时上下文不跳域。
- 新增页面时先在 `tests/test_home_nav_shell.py::test_r251_active_domain_has_one_owner_and_unknown_has_none`
  补归属断言，再改 `LIBRARY_PAGES`、路径前缀或账号白名单。

## 3. L2：一个页面只承载一个用户任务

账号与管理不再把所有功能堆进一个页面。桌面页头显示一条纯文字 L2 导航：
分组标题用来说明任务族，链接直接进入各自页面；不使用功能卡片、仪表盘或页内折叠面板
冒充 L2。导航标题只显示“账号”或“管理”，不暴露内部层级缩写“L2”。
`partials/l2_nav.html` 只消费 `l2_nav_groups()`，不保存第二份路由表。

### 3.1 账号 A1–A7

| 编号 | L2 | 路由 | 页面只负责 |
| --- | --- | --- | --- |
| A1 | 资料与身份 | `/me` | 用户名、邮箱（14px 左对齐）、统一账号中心入口、OIDC 绑定状态、界面语言与书籍语言 |
| A2 | 伙伴与 AI 伴读 | `/buddy` | 伙伴花名册、领取/装备、快捷动作、打开共享 AI 抽屉 |
| A3 | 站内信 | `/mail` | 收件箱、单封展开已读、全部已读、系统跳转 |
| A4 | 阅读与词汇 | `/reading/settings` | 难度档位、词汇量测试/细筛、阅读主题、使用引导 |
| A5 | 积分 | `/credits` | 余额、充值、积分卡、积分明细；不渲染治理表单 |
| A6 | 成就 | `/achievements` | 成就进度、解锁与领取 |
| A7 | 我的学习数据 | `/me/export` | 创建加密/非加密导出、任务进度、下载与过期状态 |

### 3.2 管理 M1–M13

| 编号 | L2 | 路由 | 页面只负责 |
| --- | --- | --- | --- |
| M1 | 用户与权限 | `/admin/usertable` | 用户列表、角色、阅读/下载权限、编辑用户 |
| M2 | 站点与注册 | `/admin/config` | 站点、注册、匿名访问与登录相关配置 |
| M3 | 整本翻译 | `/translate-all` | 整本翻译管理员任务入口 |
| M4 | 全文单词详解 | `/word-detail-batch` | 无 `book_id` 时显示选书说明；带书进入预览/入队 |
| M5 | LLM 任务中心 | `/llm-tasks` | 手动执行、队列监控、失败恢复 |
| M6 | 积分治理 | `/admin/credits` | 积分调整、充值活动、批量发卡与卡密治理 |
| M7 | 运营站内信 | `/admin/mail` | 单发/群发、人数预览、发送历史、整批撤回 |
| M8 | UI 配置 | `/admin/viewconfig` | 书架视图与界面配置 |
| M9 | 数据库配置 | `/admin/dbconfig` | Calibre 数据库连接配置 |
| M10 | 邮件服务器 | `/admin/mailsettings` | SMTP/邮件服务器配置 |
| M11 | 计划任务 | `/admin/scheduledtasks` | 元数据、缩略图等计划任务 |
| M12 | 日志 | `/admin/logfile` | 应用日志查看与下载 |
| M13 | 调试 | `/admin/debug` | 调试信息下载 |

旧 `/admin/view` 保留 302 到 M1，供 Calibre 既有 Back/Cancel 链接兼容；顶栏“管理”直接进入 M1，
不再先经过旧仪表盘。`/admin/user/<id>` 归 M1，所有 L2 页面都只有一个 active。

### 3.3 伙伴与 AI 伴读的关系

伙伴不是与 AI 伴读并列的第二套聊天产品。伙伴是 AI 伴读的“脸”和入口：

- A2 `/buddy` 负责“我是谁/用哪个伙伴/要显示哪些快捷动作”，并提供“打开 AI 伴读”；
- 共享 AI 抽屉负责对话、记忆、工具调用、语音与站内链接；
- 阅读器里的段落 AI、悬浮球和全站抽屉继续复用同一套 AI 能力；
- 不得在 A2 再实现第二套聊天 UI。

### 3.4 用户积分与管理员治理物理分离

`/credits` 只渲染用户任务；`/admin/credits` 才渲染积分调整、活动发布和批量发卡。
拆分依据不是“管理员能不能看到”，而是任务与权限都不同：普通用户的任务是消费/充值，
管理员的任务是审计性治理。只在同一页面按角色隐藏 DOM 会让 L2 页面继续过载，也增加误操作面。

## 4. 功能地图与页面归属

用户视角的完整功能树已提升为 L1 单一来源：

- [MagicBook 功能地图](../../readme/feature-map.md)

本 L3 不再复制整棵树，只维护实现侧需要的页面归属、权限边界、active 规则和测试要求。
功能地图包含五域总览、按任务找功能、八支完整功能树，以及 A1–A7 / M1–M13 的页面索引。
新增或移动功能时先改功能地图，再同步本文件的路由与边界；两边出现冲突时以功能地图描述
“用户能做什么”，以本文件描述“技术上如何归属与约束”。

## 5. 侧栏分组契约

### 5.1 分级

```text
^(?:分级)?阶\s*(\d+)
```

只识别明确以“阶N / 分级阶N”开头的书架；`第一阶段` 不冒充阶 1。
同组按解析出的整数升序，规则不锚定结尾，允许“阶3 桥梁书”。

### 5.2 媒体

名称大小写不敏感，以 `TED`、`Audio`、`Listening`、`音频`、`听力` 开头。

### 5.3 默认兜底

除分级、媒体之外的用户书架全部进入 `Shelves`。模板用已分组 id 排除后取剩余集合，
使分类互相重叠或规则调整时仍不丢入口。

**不要为展示目的增加 `Shelf.kind`。** 当前分组是可解释的名称规则，不改变书目归属；
只有在出现“用户显式指定类型、组内排序、权限或跨设备稳定分类”的真实需求时再设计 schema。

## 6. 模板边界

- 主导航 `<ul>` 增加 `mb-primary-nav`，但仍沿用 Calibre 的 Bootstrap 3 骨架。
- 保留 `top_home` / `top_library` / `top_learning` / `top_me` / `top_admin`。
  onboarding 与测试依赖这些锚点。
- `current_domain` 是 active 的唯一来源；不要为每个页面再写一套 active 条件。
- Calibre 的 Browse 项仅在域为 `library` 且 page 匹配时 active。
- 移动底栏与桌面主导航使用同一个 `current_domain`，避免两套名单产生不同答案。
- 系统空组不渲染标题；CaliBlur 自己承接系统操作时隐藏 MagicBook 的系统标题。
- 账号/管理 L2 由 `l2_nav_groups()` 统一生成；页面模板只渲染当前任务，不再复制其他 L2 模块。
- 顶栏“管理”直接进入 M1；旧 `/admin/view` 只保留重定向兼容。

## 7. CSS 叠层

产品样式只追加在 `cps/static/css/magicbook.css`，不改 vendored Calibre CSS。

| 问题 | 处理 |
| --- | --- |
| Bootstrap `.visible-xs` 使用 `display:block!important` | `.mb-bottom-nav.visible-xs { display:flex!important; }` |
| `ai_chat.css` 后加载，同 ID 覆盖悬浮球 bottom | `body #ai-companion-fab-wrap { bottom:64px; }` 提高一级特异度 |
| CaliBlur 给 nav-head 分配 60px | 用 `body.blur #scnd-nav#scnd-nav` 收紧高度 |
| 五域在平板宽度拥挤 | 768–1199px 缩减主导航内边距 |

遇到同 ID 覆盖时优先增加作用域或特异度，不用更晚加载的重复 ID 规则互相抢。

## 8. 测试要求

每次改动至少验证：

1. 一级域归属：目标页只有唯一 active，未知页无 active。
2. 入口守恒：分组前后书架入口数量一致。
3. 排序：`阶1 < 阶2 < 阶10`。
4. 响应式：桌面与 390px 无横向滚动，移动底栏可见。
5. 主题：至少检查默认主题与 CaliBlur。
6. 关键 DOM ID 未漂移。
7. L2：A1–A7 / M1–M13 每个路由恰好一个 active；用户积分与管理员治理 DOM 分离。
8. 入口：`/buddy` 只保留一个“打开 AI 伴读”入口，不新建第二套聊天实现。

```bash
pytest tests/test_home_nav_shell.py -q
pytest tests/test_account_admin_ia_r251.py -q
```

## 9. 扩展边界

- 新增一级域前先证明它承担独立任务，且不与现有域重叠。
- 移动底栏最多四个高频入口；低频管理能力不进入底栏。
- 新分类不得静默隐藏任何既有项。
- 规则是展示层时，不顺便改模型；模型变化必须单独立需求与迁移方案。
- 一个 L2 页面只承担一个任务；需要并列完成多个任务时先问能否拆页，而不是继续加页签。
- L2 导航保持纯文字分组；只有页面内容需要行动时才使用卡片。
