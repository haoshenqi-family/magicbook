# LLD — R257 按产品设计方案实施（方案一/三/四/六/七/八/九 可落地项）

> 状态：**开发中（待验收）**
> 工作项：R257 · 迭代 1.0
> 设计来源：[magicbook-产品设计方案-2026-10-30.md](../../../../../magicbook-产品设计方案-2026-10-30.md)（用户 2026-10-31 拍板「按照设计方案修复」）

## 1. 范围裁决

用户拍板按设计方案实施。十个方案按设计文档自身的 ⚡/🏗 标记与「不做什么」原则裁剪：

| 方案 | 本轮处置 | 说明 |
| --- | --- | --- |
| 一 入口修复与收敛 | ✅ 实施剩余部分 | B1 路由已由 R256 修复；本轮做「入口盘点对齐」：普通用户不再渲染必 404 的「已下载书籍」 |
| 二 生词判定与黄金区 | ⏸ 待拍板 | 🏗 跨 moon-well（专名过滤/词族归一），单独占号实施 |
| 三 生词本与空态 | ✅ 最小闭环 | 空态解释性文案 + 测试结果旁「查看复习队列」直达；完整生词本列表页（新页面+词表接口）为剩余部分，待拍板 |
| 四 文案分离 | ✅ | 下载/阅读两处权限提示去后台路径 |
| 五 充值卡重排 | ⏸ 待拍板 | 🏗 信息架构性重排（五段式卡片），涉及支付转化文案，单独拍板 |
| 六 i18n 收口 | ✅ 部分 | 实测缺口已比体验报告时小（多数词条 R251-R256 间已补）；本轮补积分页 3 + 稀有度 4 + 伙伴页 1 + 语言菜单收敛（29→3+折叠） |
| 七 横幅降权 | ✅ | 书库首页移除难度横幅；模板保留（阅读器/设置页可复用） |
| 八 切语言反馈 | ✅ | 原地停留（next 白名单）+「界面语言已切换」 |
| 九 书架 CRUD | ✅ 剩余部分 | B2 空标题校验 R256 已修；本轮 div→真按钮 + 存量空名兜底（确认弹窗 main.js confirmDialog 原本就有，体验报告 B3 系自动化环境假阴性） |
| 十 已读口径 | ⏸ 待拍板 | 🏗 需先数据诊断（B4 文案歧义 R256 已修，状态口径待核） |

## 2. 实现要点

- **方案一**：`render_template.get_sidebar_config` 删除非管理员的 `Downloaded Books` else 分支（原链接指向 `web.books_list` download 页，该页 `check_visibility && role_admin()` 双门槛对普通用户必 404）；管理员分支不变。
- **方案三**：`learning_review.html` 空态改为解释排程语义（回答「词去哪了/下次什么时候见」）；`reading_settings.html` 测试结果旁新增 `vt-notebook-link-row`（→ `web.learning_review_page`），`vocab-test.js` 在 `addedToNotebook >= 1` 时显示。
- **方案四**：`detail.html` 下载提示改「下载功能未开放；在线阅读不受影响。」+「如需下载权限，请联系站点管理员。」；R225 的阅读权限提示同口径。
- **方案六**：`credits.js` 三处文案经文件内 `t()`（mbT 同源）接入 i18n；`buddy.js` 稀有度改字面量映射（可被 generate_i18n_seed 扫描）；seed 由脚本自动 +3（稀有度）、手动 +3（积分页，`t()` 字面量脚本扫不到）；语言菜单收敛为常用三项+当前语言直出、其余「更多语言」折叠（main.js toggle），完整列表保留在 /me。
- **方案七**：`index.html` 移除 `difficulty_entry.html` include；模板本体保留。
- **方案八**：`web.update_preferences` 成功分支分场景 flash（带 `default_language` 的 /me 表单仍「资料已更新」；顶栏纯切语言→「界面语言已切换」）；redirect 优先表单 `next`（只收 `/` 开头且非 `//` 的站内相对路径，防 openredirect），兜底 /me；顶栏语言表单带 `next=current_path`。
- **方案九**：`shelf.html` 删除书架 `div.btn` → `<button type="button">`（语义/键盘可达；form 内必须显式 type 防提交外层表单）；侧栏三组书架空名兜底「未命名书架」，书架详情页 title 同兜底。

## 3. 验证

- 新增 `tests/test_design_plan_r257.py` 20 用例（源码契约 + mo 词条 + HTTP redirect/openredirect）。
- 契约演进 4 处（设计决策驱动，意图不变）：
  - `test_me_preferences.py::test_home_mounts_difficulty_entry_once` → include 0 次 + 模板保留；
  - `test_auth_reader_covers_r225.py` 两用例 → 门禁解释保留但断言无后台路径；
  - `test_entry_layer_r212.py::test_only_new_user_creation_initializes_locale` → R256 收拢后 `locale=` 只允许出现在 `create_oidc_user`（该文件在 R256 收尾时漏跑，本轮全量暴露后一并钉住）。
- 全量 `pytest tests/`（除 test_ai_agent_proxy 网络依赖、slow）：**1228 passed / 0 failed**。

## 4. 文档四问

- 能力变了：L1（切语言不再跳转、首页无难度横幅、普通用户侧栏无「已下载书籍」、语言菜单折叠）——随验收回填 readme。
- 契约变了：无对外 HTTP 契约变化（`/me/preferences` 新增可选 `next` 表单字段，白名单校验）。
- 实现/边界变了：本 LLD。
- 本次怎么实现：本文档；台账 R257。
