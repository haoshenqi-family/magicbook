# AC — R251 MagicBook UI 信息架构、导航分组与账号/管理 L2 拆页

> 状态：已上线待验收（第二轮；第一轮 `70aa636c`、初始实现 `af551307`、验收修正 `3a75a695` 均已上线）

## A. 一级导航

- [x] 登录后的桌面主导航统一为首页 / 书库 / 学习 / 账号 / 管理五个一级域。
- [x] 管理员入口位于一级主导航，不再混在 Settings 下拉。
- [x] 普通用户不渲染管理入口。
- [x] 每个页面最多一个一级域带 `active` 与 `aria-current="page"`。
- [x] `/reading/settings` 只点亮账号，不点亮书库。
- [x] 未知页面不误点亮书库。
- [x] 既有 `top_home` / `top_library` / `top_learning` / `top_me` / `top_admin` DOM ID 保留。

## B. 侧栏分组

- [x] Browse、书库、分级、媒体、系统形成稳定层级。
- [x] `阶1` / `阶 2` / `分级阶3` 进入分级组。
- [x] TED / Audio / Listening / 音频 / 听力进入媒体组。
- [x] 规则识别不出的书架进入默认书库组。
- [x] 非空组显示数量徽标，空组不显示标题。
- [x] 分级组按数字升序：`阶1 < 阶2 < 阶10`。
- [x] 真实渲染中书架入口数量守恒，不因分组丢任何入口。
- [x] 不新增 `Shelf.kind`，不执行数据库迁移。

## C. 响应式与主题

- [x] 1440×1200 无横向滚动。
- [x] 390×844 无横向滚动。
- [x] 移动底栏为四列 flex，不再被 `.visible-xs` 的 `display:block!important` 覆盖。
- [x] 移动底栏第四项固定显示“账号”，不直接使用可能过长的用户名。
- [x] 移动悬浮球与底栏不重叠。
- [x] 平板宽度下五个一级域仍保持可见。
- [x] CaliBlur 分组标题不再占 60px。
- [x] CaliBlur 下系统空标题不渲染。

## D. 最小侵入

- [x] 产品规则集中在 `cps/ui_ia.py`。
- [x] `cps/jinjia.py` 只保留必要的 import 与三个模板过滤器注册。
- [x] 未修改 vendored Calibre CSS。
- [x] 未重写 Calibre 路由与书架模型。
- [x] 保留原有导航骨架、页面链接和关键 DOM ID。

## E. 测试与文档

- [x] `pytest tests/test_home_nav_shell.py -q`：12 passed / 0 failed。
- [x] `pytest tests/ -q`：1188 passed / 0 failed / 4 warnings。
- [x] `git diff --check` 通过。
- [x] `py_compile cps/ui_ia.py cps/jinjia.py` 通过。
- [x] 产品 L1、L3、需求基线、LLD、AC 已同步。
- [x] 长期信息架构原则已沉淀到 `docs/kb/instructions/coding/`。
- [x] `70aa636c` 已推送并在生产部署；容器 `running / healthy`，`/login` 返回 200。

## F. 功能树与 L2 规则

- [x] L1 独立文档 `readme/feature-map.md` 列出 MagicBook 非 Calibre 功能的完整树状结构，小功能拆到叶子；产品 README 提供入口。
- [x] 功能树覆盖首页、书库增强、阅读器增强、词汇、学习、伙伴与 AI 伴读、账号、管理八支。
- [x] L3 不再复制完整功能树，只链接到 L1 功能地图并保留实现边界。
- [x] 账号 A1–A7、管理 M1–M13 有唯一编号、路由和单页任务表。
- [x] L2 导航由 `l2_nav_groups()` 单一来源生成；纯文字分组，不使用功能卡片。
- [x] “账号 / 管理”页头只显示域名称，不显示内部层级缩写“L2”。
- [x] 每条 A/M owned route 恰好一个 L2 active；旧 `/admin/view` 不属于新 L2 active。

## G. 账号拆页

- [x] `/me` 只保留资料、OIDC 绑定和语言，不再含难度、词测、主题、伙伴、导出。
- [x] `/me` 的用户名、邮箱为 14px 左对齐，不再使用 `dl-horizontal` 的右对齐标签列。
- [x] `/me` 底部不再显示“阅读难度、词汇量测试与阅读主题见…”迁移提示。
- [x] `/me` 的账号说明下方提供“前往统一账号中心”，指向 `https://account.haoshenqi.top/`，新窗口打开且带 `noopener noreferrer`。
- [x] 难度、词汇量测试/细筛、主题、使用引导在 `/reading/settings`。
- [x] 学习数据导出在 `/me/export`，原有创建、轮询、下载能力保持可用。
- [x] `/buddy` 是伙伴入口页，有且只有一个“打开 AI 伴读”按钮。
- [x] 该按钮复用 `window.AICompanion.openChat()`，没有新建第二套聊天 UI。

## H. 管理拆页

- [x] 管理 M1–M13 各自独立成页，不再渲染旧 all-in-one 仪表盘。
- [x] 顶栏“管理”直达 M1 `/admin/usertable`。
- [x] 旧 `/admin/view` 保留 302 到 M1，兼容 Calibre 既有 Back/Cancel。
- [x] M4 `/word-detail-batch` 无 `book_id` 时显示选书说明，不再返回 400。
- [x] 用户 `/credits` 只渲染充值/积分卡/明细，不渲染治理 DOM。
- [x] 管理员 `/admin/credits` 独立渲染积分调整/充值活动/批量发卡，普通用户访问 403。

## I. 最小侵入与兼容

- [x] 不重写 Calibre 路由、模型和 vendored CSS。
- [x] 保留 `top_home/top_library/top_learning/top_me/top_admin` 等关键 DOM ID。
- [x] 新页面只使用产品层模板/CSS/JS；旧 Settings 入口收敛为最小 Help 菜单。
- [x] 用户与管理员共用积分代理和样式，但不共享页面 DOM。

## J. 第二轮验证

- [x] `node --check` 通过全部改动/新增 JS。
- [x] `py_compile` 通过改动 Python 与新增测试。
- [x] `git diff --check` 通过。
- [x] 第二轮定向回归 150 passed / 0 failed / 2 warnings。
- [x] 正式发布态全量 pytest 0 failed：1206 passed / 4 warnings。
- [x] CDP 设备指标 390×844 下关键账号页 `scrollWidth == innerWidth`，移动底栏四项完整可见。
- [x] 1440px 下账号/管理 L2 与页面内容无横向溢出。
- [x] 验收修正 `3a75a695` 已推送 `origin/develop`；fnOS 构建、app-manager 部署、容器健康与生产匿名路由检查完成。
- [x] 统一账号中心入口 `2de2a538` 已上线；390×844 / 1440×1200 无横向溢出，生产容器 `running/healthy`，`house.code-digest=533d440f819b943e`。
- [x] L1/L2/L3、需求基线、LLD、AC、response 与长期 KB 已同步。
