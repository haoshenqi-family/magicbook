## 2026-10-24（R224：本轮测试修复未完成项收口——R219 / R212 / R213-B6 / R214-C）

### R224（用户：「review 本轮测试修复，找到哪些没有修改完成且没有推到下个迭代的」→「尽可能修复代码未完成的部分」）

- **结论先行**：真正属于代码未完成、且未排到下一迭代的是 **R219 邀请链接、R212 交付项 1/3/4、R213-B/B6 进度总开关、R214-C 估算 500 核实**。R215、R221、R223、R220 属待真机验收，不是本轮代码缺口；**只有 R213-A 侧边栏分组**按用户 2026-10-24 拍板明确留到下一迭代，不冒充本轮完成。
- **R219（已修复）**：`cps/oidc.py` 优先读取 Authentik 嵌套 `?query=itoken%3D...`，兼容旧顶层 `itoken`/`token`；`/oidc/signup` 只输出外层 `?query=`，内部同时带 `itoken` 与 `next`。`tests/test_oidc_signup.py` 覆盖嵌套解析、旧格式兼容、冲突优先级与 token alias；生产 env 与真实注册流仍待验收。
- **R212（代码完成，待真机验收）**：登录页新增价值主张与随机书墙（复用 `random_discover_books`/`common_filters`，空库或查询失败安静隐藏）；新账号 locale 按 Authentik claim → Accept-Language → 站点默认初始化；顶栏增加语言入口。复查中修掉两个隐藏依赖：① 顶栏只提交 `locale`，`/me/preferences` 仅在 `default_language` 显式出现时校验/更新，避免账号里失效的书籍语言连带拒绝界面切换；② 匿名浏览关闭时不取书、不渲染书墙，避免封面端点重定向造成破图及未授权页面泄露书名。新增 6 条中文 PO/MO 守卫，中文不再静默回退英文。
- **R213-B/B6（已补开发，待复验）**：新增 `config_reading_progress_enabled` 配置列与存量库 ALTER 迁移、管理页开关；关闭时 `/ajax/reading-progress` 返回 `{"success": true, "disabled": true}`，不写 `ReadingProgress` / `ReadBook`；EPUB/PDF/TXT 均不加载 `reader-progress.js`、不注入服务端位置，EPUB 回退 localStorage、PDF 不拼 `#page`、TXT 回到改造前行为。测试隔离也修实：管理配置 POST 会因缺失复选框清空大量字段，现将整行 `_Settings` 快照恢复并清 `ConfigSQL._settings` 缓存，避免后续用例被 kill switch 污染；另在临时旧库上验证缺列 ALTER 与默认值，不依赖测试库已含新列。
- **R214-C（代码核实，证据有缺口）**：当前 worktree 的 `cps/reading_insight/service.py` 与 `origin/develop` 完全一致，估算 500 的相关修复已在 develop（`42ddfb19`、`b28d9240`），本 worktree 无额外代码可改。生产 ES 查询返回 **401**，因此不能声称已证实生产 500 的具体异常类型；R214-C 仍需真机复核。
- **验收而非代码缺口**：R215、R221、R223、R220 的自动化/局部修复已在各自分支或 develop，剩余动作是真机验收与状态流转；本轮不把「未跑真机」写成「代码没做完」。
- **明确下迭代**：R213-A 的侧边栏四组分组（`Shelf.kind` 判定）仅此项按用户拍板留到下一迭代；本轮不改其设计，也不勾选 A1。
- **文档同步**：L1 `readme/reading.md` 更正 PDF/TXT 账号级进度；L2 `reading/interface.md` 补开关关闭响应；L3 `reading/features/reading-progress.md` 更正 `ReadBook` 在读状态与三格式下线边界；R219 工作流、L3、`.env.example` 与 R217 历史 LLD 标注现行嵌套 query（历史只标注不重写）；R212 LLD 改为交付项 1/3/4 代码完成待真机；R213 AC/LLD 与计划表统一 `config_reading_progress_enabled` 并清掉「查无此开关」旧警告。
- **验证与驻留**：定向回归 **196 passed / 0 failed**（OIDC、入口层、品牌/CSP、`/me`、导航、阅读进度、首页、R214 估算与详情），`git diff --check` 与改动 Python 文件编译通过。用户 2026-10-25 指示 merge and push 后，在最新 `origin/develop` 上执行发布态全量 **944 passed / 0 failed**。worktree `../magicbook-r224-close-out`（分支 `feat/r224-close-out`，基线 `origin/develop` `b0af8382`）保留待真机验收。
- **总结**：requests.md 条目 224 为本轮收口需求，条目 219 已回填「已开发待验收」；本条为回应。冲突记录：未改主检出、未 push；R214-C 生产异常类型未证实、ES 401 属证据缺口；R216 回应已按 10 节窗口规则原样搬至 `response-archive/response-R216.md`。
