# LLD — R256 黑盒体验报告缺陷修复（OIDC 建号侧栏位 / 空书架 / 已读歧义 / 实体解码）

> 状态：**已上线待验收（2026-10-31）**
> 工作项：R256 · 迭代 1.0
> 需求来源：新用户黑盒体验报告（2026-10-30，`magicbook-体验报告-2026-10-30.md`，账号 mbtester1030）

## 1. 缺陷与根因

| 编号 | 现象 | 根因 | 证据 |
| --- | --- | --- | --- |
| B1 | 新 OIDC 用户侧栏九个浏览入口（分类/丛书/作者/出版社/语言/评分/文件格式/最高评分/已下载）全部 404 | `oidc.py` OIDC 建号漏设 `sidebar_view`，落列默认值 1（只含 DETAIL_RANDOM 位）；浏览路由以 `check_visibility(SIDEBAR_X)` 为门槛，位缺失 `abort(404)` | 生产库 `mbtester1030.sidebar_view=1`；手动恢复 `262143`（= config_default_show）后 `/author` 立即 200，因果闭环 |
| B2 | 空标题书架可创建，侧栏显示残缺（空名+计数），无界面入口可清理 | `shelf.create_edit_shelf` 对 `title` 无空值校验，`check_shelf_is_unique("")` 照样通过 | 测试账号实测创建出 `/shelf/13`「书架：」 |
| B4 | 新用户所有书籍详情页都显示「已读」 | `detail.html` 阅读状态开关的固定 label 复用 msgid `"Read"`，po 译「已读」；label 与 checkbox 状态无关，所有书都渲染 | book 148/278/541 均复现；模板 420-422 行为 checkbox 标签 |
| B5 | 听写页材料下拉显示 `Why you need a good night&#039;s sleep` 原始实体 | Calibre 元数据里标题存着未解码实体；前端 `textContent` 不解码，忠实显示 | `learning-common.js loadMaterials` 用 `opt.textContent`；数据源即含实体 |

修复范围裁决：B3（删除书架 div 按钮点击无反应）与 B6（听写载入段落卡顿）在自动化环境中无法证伪/复现一次，**本轮不修**，报告中列为存疑待真机复核。

## 2. 修复设计

### 2.1 B1：建号默认值收拢为唯一入口

- 新增 `oidc.new_user_sidebar_view()`：取 `config.config_default_show`，与本地 `/register` 同口径；配置未初始化回退 0（不猜位组合）。
- 新增 `oidc.create_oidc_user(username, email, claims)`：角色（R211）/语言/侧栏位三项站点默认值一次取齐；回调建号唯一入口。
- 回调 `callback()` 改为委托 `create_oidc_user`。
- R211 契约测试（`test_oidc_admin_role.py`）随之钉到 helper：回调内不得出现任何 `role=` 直写，`role=resolve_new_user_role()` 恰好一次且只在 helper。
- **存量数据修复（一次性 SQL，运维执行）**：
  ```sql
  -- OIDC 建号且从未被管理员改过侧栏位的存量用户（sidebar_view=1 为缺陷特征值）
  UPDATE user SET sidebar_view = (SELECT config_default_show FROM settings WHERE id = 1)
  WHERE sidebar_view = 1;
  ```
  测试账号 mbtester1030 已在诊断阶段按此口径恢复并复验（无活跃改写者，2 分钟后复查仍 262143）。

### 2.2 B2：创建入口拒绝空标题

`create_edit_shelf` 在唯一性检查前加 `shelf_title.strip()` 空判：flash「书架名称不能为空」并 302 回首页（与该文件既有 redirect 惯例一致）。编辑路径共用该函数，同步受保护。

### 2.3 B4：label 换无歧义 msgid

`detail.html` 阅读状态开关 label 由 `_('Read')` 改为新 msgid `_('Reading status')`（中文「阅读状态」），msgid `"Read"` 的「已读」翻译不动（筛选器等场景语义正确）。po/mo 同步。

### 2.4 B5：展示层解码

`learning-common.js` 新增 `decodeHtmlEntities()`（textarea innerHTML 一次性解码，脚本不执行），`loadMaterials` 的 title/author 进 `textContent` 前先解码。听写/复述/重读三处下拉共用收益。

## 3. 验证

```text
pytest tests/test_newuser_sidebar404_r256.py   # 10 passed（新增守卫）
pytest tests/test_oidc.py tests/test_oidc_signup.py
  tests/test_oidc_admin_role.py tests/test_home_route.py
  tests/test_home_nav_shell.py tests/test_book_detail_r214.py
  tests/test_book_detail_r222.py tests/test_adv_search_read_status.py
  tests/test_i18n_seed_contract.py tests/test_learning_pages_static.py
  tests/test_learning_hub_cards.py tests/test_learning_voice.py  # 全绿（含 2 个契约用例随结构演进更新）
```

- 新增 10 用例：建号位组合/九浏览位覆盖/config 未初始化回退/helper 三项取齐 ×4、空标题拒绝(2 参数化)+正常可建、po/mo 词条双侧校验、JS 解码契约。
- 契约更新 2 用例：`TestCallbackContract` 随 R256 收拢结构演进（意图不变：建号不得直写角色、合并路径不动角色）。

### 3.1 上线验证（2026-10-31）

- push `db3f445f..7906fa5b`；fnOS `build END OK (7906fa5b)`，容器 `Up (healthy)`，容器内代码含 `new_user_sidebar_view`。
- 存量 SQL 已执行（LLD §2.1 口径 + 排除 Guest）：sunny/uxprobe/r214probe/mbtester1030 → 262143；**Guest 保留 1**（匿名 Helper 账号受限侧栏是 Calibre 原版语义，不属于缺陷）。
- 端到端：全新 OIDC 用户 `mbtester1031` 注册登录，库内 `sidebar_view=262143`；九入口抽验 `/category /series /publisher /language /ratings /formats /rated /author` 均 200。

### 3.2 已知边界（不夹带修复）

`/downloadlist` 对普通用户仍 404：Calibre 原版该路由是双重门槛 `check_visibility(SIDEBAR_DOWNLOAD) and role_admin()`（下载统计列表仅管理员可达），而侧栏渲染只查可见性位——普通用户看得到入口点不开。修复前后行为不变差（修复前位缺失同样 404），属原版遗留的「入口与门槛不一致」，归体验报告设计方案一（入口盘点对齐：侧栏只承诺真实可达的入口）后续处理。

## 4. 文档四问

- 能力变了：无（缺陷修复，恢复既有承诺行为）。
- 契约变了：无对外 HTTP 契约变化；建号内部结构收拢（helper 单一入口）。
- 实现/边界变了：本 LLD。
- 本次怎么实现：本文档；台账 R256。
