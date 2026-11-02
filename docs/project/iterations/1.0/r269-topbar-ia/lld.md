# LLD — R269 顶栏信息架构收敛（搜索/上传/任务/语言/注销归位）

> 状态：**开发完成待验收**（2026-11-02）
> 工作项：R269 · 迭代 1.0
> 需求基线：[library requirements](../../../../product/library/requirements.md) 的 R269 条 · 用户原话见 `docs/project/requests/requests.md` 269

## 1. 用户原话与目标

> 「搜索只在书库有就可以了其他四个主入口不要。同样的上传书籍也是。最右边的用户跟主用户重复了，
> 是相同的功能，还有注销按钮，和语言按钮，只放到账号中。任务列表只放到管理权限中。
> 右上角只留帮助按钮」

按截图（默认主题顶栏：`logo | 搜索书库+搜索+高级搜索 | 首页 书库 学习 账号 管理权限 | 上传书籍 任务列表 语言 帮助 hsq 注销`）
逐条落地：

| # | 用户要求 | 本轮处置 |
| --- | --- | --- |
| 1 | 搜索只在书库有 | 搜索表单按 `current_domain == 'library'` 门控 |
| 2 | 上传书籍同样只在书库 | 上传表单按 `current_domain == 'library'` 门控（保留 `role_upload` + `g.allow_upload`） |
| 3 | 最右用户名与「账号」重复 → 去掉 | 默认主题不再渲染登录态 `#top_user`；匿名分支改为纯登录入口 |
| 4 | 注销只放账号 | 顶栏 `#logout`（主题 0/1 两处）删除，改 `/me` 的 `#me-logout` |
| 5 | 语言只放账号 | 顶栏 `#top_language` 整块删除，语言面板 `/me` 的 `#me-language` 已在（R251） |
| 6 | 任务列表只放管理权限 | 顶栏 `#top_tasks` 删除，入口进 `ADMIN_L2_GROUPS`（系统组 `admin-tasks`），`/tasks` 归属管理域 |
| 7 | 右上只留帮助 | `#top_mb_settings` 是右侧唯一常驻项（匿名除外，保留登录） |

非目标：不动搜索页/筛选/排序、不改上传接口、不改 `/tasks` 访问权限、不改统一账号中心 SSO。

## 2. 判定原则：控件跟着域走

R251 解决「页面归哪个一级域」（`nav_domain`）；本轮补上「跨域控件属于哪个域」。判定一律用
`current_domain`，不写页面白名单——白名单会与 `ui_ia.py` 的路由归属漂移，而域判定已有单测。

```text
library   -> 搜索框 + 高级搜索 + 上传书籍
home / learning / account / admin / ""（未知） -> 不渲染这两组控件
```

书库域天然覆盖：`/`（书目首页）、各 Browse 页、`/search`、`/advsearch`、`/book/<id>`、`/shelf/*`。
匿名可浏览（`g.allow_anonymous`）时书库域照旧有搜索框。

## 3. 改动清单

### 3.1 `cps/templates/layout.html`

| 位置 | 改动 |
| --- | --- |
| 顶栏搜索表单 | 条件加 `and current_domain == 'library'` |
| 主题 0 上传表单 | 条件加 `current_domain == 'library'` |
| `li.top_tasks` | 删除（入口迁至管理域 L2） |
| `li#top_language` 整块（含 R257 折叠菜单） | 删除（语言归 `/me`） |
| 主题 0 的 `#top_user` / `#logout` | 登录态删除；`#top_user` 仅保留匿名登录分支 |
| 主题 1 头像下拉的 `#logout` | 删除（与账号域重复；头像仍链到 `/me`） |
| L2 导航 include 条件 | 管理域追加 `current_user.role_admin()` 守卫 |

主题 1（CaliBlur）只在头像下拉里删了注销一项，其余皮肤结构不动——它不是当前默认主题，
且 `caliBlur.css` 有大量 `#main-nav > li:nth-child(n)` 定位规则，动结构风险高于收益。

### 3.2 `cps/ui_ia.py`

```python
ADMIN_PATH_PREFIXES = ('/tasks', '/translate-all', '/word-detail-batch', '/llm-tasks')
```

`ADMIN_L2_GROUPS` 的「系统」组首位新增 `admin-tasks`（`endpoint=tasks.get_tasks_status`,
`matches=('/tasks',)`）。管理页数 13 → 14。

### 3.3 `cps/templates/me.html`

A1 资料面板新增 `#me-logout`（GET 链接到 `web.logout`），文案复用既有 msgid `Logout`（zh：注销），
零新词条。语言面板 `#me-language` 保持 R251 形态（`<select>` 铺全量语言 + 书籍语言）。

### 3.4 连带清理

- `cps/static/js/main.js`：删除 R257 方案六的 `#mb-lang-more-toggle` 手风琴开关（元素已不存在）。
- `cps/static/css/style.css`：`.navbar-language-option` 保留定义并加注释（无模板引用；先留复用位）。

## 4. 语义边界

| 情况 | 行为 | 原因 |
| --- | --- | --- |
| 普通用户访问 `/tasks`（书签/直链） | 200，能看到自己的任务 | `/tasks` 权限未变（`user_login_required`），本轮只搬入口 |
| 普通用户在 `/tasks` | 不渲染管理域 L2、不点亮「管理」 | 管理 L2 有 `role_admin()` 守卫；否则会摊出一串 403 链接 |
| 管理员在 `/tasks` | 点亮「管理」，L2 高亮 `admin-tasks` | `/tasks` 进 `ADMIN_PATH_PREFIXES` |
| 匿名 + `g.allow_anonymous` | 书库域有搜索框，顶栏无帮助下拉 | 帮助下拉只在登录态渲染（R212 起） |
| 匿名 + 关闭注册 | 仍有 `#top_user`（登录） | 下方 login/register 依赖 `g.allow_registration`，不覆盖此情形 |
| 上传进度模态 | 只在书库页可能触发 | `uploadprogress` 绑定 `#form-upload`，缺失即 no-op |

## 5. 测试

新增 `tests/test_topbar_ia_r269.py`（14 例）：书库域有搜索/上传、其他三域都没有；
登录态顶栏无 `top_tasks/top_language/logout` 且保留帮助；`/me` 有 `me-logout`/`me-language`；
管理员在 `/tasks` 有 `admin-tasks` 且点亮管理域；普通用户在 `/tasks` 拿不到管理链接。

契约演进（改断言而非删断言）：

- `tests/test_entry_layer_r212.py`：`TestTopNavLanguage` → `TestLanguageEntry`，改断「顶栏无语言入口、`/me` 有语言表单」。
- `tests/test_design_plan_r257.py`：方案八改断「语言表单在 `/me`、`next` 白名单仍在」；方案六改断「折叠菜单整体下线」。
- `tests/test_account_admin_ia_r251.py`：管理 L2 计数 13 → 14，路由矩阵加 `/tasks`，新增 `admin-tasks` 归属断言。

闸门：定向 8 个文件 121 passed；全量 `pytest tests/` **1287 passed / 0 failed**（运行需
`TMPDIR=/tmp/...`——默认沙箱 tmp 目录会让 69 个用例的 `tmp_path` 报 `FileExistsError`，属环境问题）。

## 6. 风险与回归面

- **书库外无法搜索**：用户明确要求；从其他域回书库一次点击即可，且 `/search` 结果页属书库域仍可改词。
- **普通用户失去任务列表入口**：`/tasks` 直链仍可用；本轮按指令不为常态用户保留顶栏位。
- **CaliBlur 皮肤**：只删了头像下拉的注销项；`#main-nav` 子项数量变化在主题 0，`magicbook.css`
  无 `nth-child` 定位规则（`caliBlur.css` 的 nth-child 规则只作用于 `body.blur`）。
- **onboarding**：`#query`/`#advanced_search` 仍在书库域页面存在，锚点在源码层未变；在非书库域启动
  导览时这两步按既有「锚点缺失即跳过」规则降级（引擎 R109 起就支持）。

## 7. 文档四问

- 能力变了 → L1 `readme/library.md`（顶栏控件跟域走）、`readme/account.md`（A1 含注销、语言与注销只在此页）、`readme/admin.md`（14 页 + 任务列表条目）
- 契约变了 → 无 HTTP 契约变化；导航契约变更记入 L3 `product/library/features/ui-information-architecture.md` §5 顶栏控件归属
- 实现/边界变了 → 同上 L3，含非管理员 `/tasks`、匿名分支、上传模态降级边界
- 本次怎么实现 → 本 LLD
