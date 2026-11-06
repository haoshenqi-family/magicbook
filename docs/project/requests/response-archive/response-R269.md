# 回应归档 · R269


## R269 · 顶栏信息架构收敛：搜索/上传只在书库、任务列表归管理、语言与注销归账号（2026-11-02）

### R269（用户：「搜索只在书库有就可以了其他四个主入口不要。同样的上传书籍也是。最右边的用户跟主用户重复了，是相同的功能，还有注销按钮，和语言按钮，只放到账号中。任务列表只放到管理权限中。右上角只留帮助按钮」）

- **结论先行**：顶栏从「全站工具栏」改成「按域说话」——搜索与上传只在书库域出现，右上只剩帮助；语言、注销归账号页，任务列表归管理页头。判定用 `current_domain` 而不是页面白名单，跟着 R251 的域归属一起漂移才不会二次分叉。
- **搜索与上传（书库域专属）**：`layout.html` 的搜索表单与 `#form-upload` 各加一个 `current_domain == 'library'` 条件；上传保留原来的 `role_upload()` + `g.allow_upload` 双重门控。书库首页 `/`、各 Browse 页、`/search`、`/advsearch`、`/book/<id>`、`/shelf/*` 都算 library，所以「在书库里随时能搜、能传」的体验没变，只是不再跟着你去首页、学习、账号、管理。
- **右上只留帮助**：删掉登录态的 `#top_user`（用户名链接，和「账号」一级域同一件事）与 `#logout`。匿名分支保留一个登录入口——`g.allow_registration` 关掉时下方 login/register 不渲染，它是唯一去处，不能一起删。
- **语言与注销归账号**：顶栏 `#top_language` 整块撤掉（含 R257 方案六的「更多语言」折叠菜单，元素没了开关也一并删）；语言继续用 `/me` 的 `#me-language` 面板（全量语言 `<select>` + 书籍语言）。注销在 A1 资料面板下新增 `#me-logout`，复用既有 msgid `Logout`/「注销」，零新词条。
- **任务列表归管理**：顶栏 `#top_tasks` 删除；`ADMIN_L2_GROUPS` 的「系统」组首位新增 `admin-tasks`（M8，`/tasks`），管理页数 13 → 14（M9–M14 顺延）。`/tasks` 进 `ADMIN_PATH_PREFIXES`，管理员在任务页会点亮「管理」并在 L2 上看到高亮。
- **权限边界（本轮特别处理）**：`/tasks` 的访问权限没动（仍是 `user_login_required`），普通用户从书签直达仍可用自己的任务页；但管理域 L2 加了 `current_user.role_admin()` 守卫——否则非管理员会在 `/tasks` 上看到一串点进去就 403 的管理链接。
- **测试**：新增 `tests/test_topbar_ia_r269.py` 14 例（书库域有/其他三域无 `#query`+`#form-upload`；登录态顶栏无 `top_tasks/top_language/logout` 且保留帮助；`/me` 有 `me-logout`+`me-language`；管理员 `/tasks` 有 `admin-tasks` 且点亮管理域；普通用户 `/tasks` 拿不到管理链接）。三处旧契约演进而非删断言：R212 语言入口改断「顶栏无、`/me` 有」，R257 方案八/方案六改断「表单在账号域、折叠菜单下线、`next` 白名单仍在」，R251 管理 L2 计数 13 → 14 并补 `/tasks` 归属。定向 8 个文件 **121 passed**；全量 `pytest tests/` **1287 passed / 0 failed**（默认沙箱 tmp 会让 69 个 `tmp_path` 用例 `FileExistsError`，改 `TMPDIR` 后全绿，与本轮改动无关）。
- **文档四问**：能力 → L1 `readme/library.md`（顶栏控件跟域走）、`readme/account.md`（A1 含注销 + 语言/注销只在此页）、`readme/admin.md`（14 页 + 任务列表条）；契约 → 无 HTTP 契约变化，导航契约进 L3 `library/features/ui-information-architecture.md` 新增 §5「顶栏控件归属」；实现/边界 → 同 L3（非管理员 `/tasks`、匿名登录分支、上传模态降级）；本次实现 → `docs/project/iterations/1.0/r269-topbar-ia/lld.md`；需求基线 → `library/requirements.md` R269 条 + `REQUIREMENTS.md` 变更记录。
- **未做 / 留给验收**：主题 1（CaliBlur）只在头像下拉里删了注销一项，其余皮肤结构不动（`caliBlur.css` 有大量 `#main-nav > li:nth-child(n)` 定位，动结构风险高于收益）；普通用户失去任务列表的顶栏入口是有意为之，如果还想让他们看到自己的任务队列，再单独加一条。
- **状态与驻留**：**已上线待验收**。用户 2026-11-02 21:42 指令「push」后推 `origin/develop`（`fc3a9154..066bb8e9`，含实现 `49406fe8` + merge `066bb8e9`），fnOS 链自动构建部署；线上核验：`/static/js/main.js` `last-modified 2026-11-02T13:42:54Z`（即部署时刻）、已无 `mb-lang-more-toggle`，`/static/css/style.css` 已含 R269 注记，站点 `/` 302 → `/login`（应用在服务）。worktree `../magicbook-r269-topbar-ia`，分支 `feat/r269-topbar-ia`，按闸门保留待验收。
- **窗口与总结**：写入前窗口 10 节，新增后 11；按「写入即检查」把最旧 R255 整节原样搬至 `response-archive/response-R255.md` 并登记索引，窗口恢复 10。requests.md 条目 269 已从占位回填。冲突记录：无撞号（claim.sh 对 `origin` 台账算号得 269）。
