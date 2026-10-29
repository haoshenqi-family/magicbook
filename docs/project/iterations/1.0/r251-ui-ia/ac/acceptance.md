# AC — R251 MagicBook UI 信息架构与导航分组

> 状态：已上线待验收（2026-10-29；实现 `1910fce7`，移动账号标签修正与发布 `70aa636c`；定向 12 passed / 0 failed；正式发布态全量 1188 passed / 0 failed）

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
