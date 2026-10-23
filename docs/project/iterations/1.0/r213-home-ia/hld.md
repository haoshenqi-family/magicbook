# HLD — R213 首页信息架构（继续阅读 / 今日计划 / 分级推荐 + 侧边栏分组 + 移动端底部导航）

> 状态：**草案，待第二轮讨论定稿**（2026-10-23；四问已拍板，§7 四条细节待拍板）
> 迭代：1.0 · PJM 工作项 [MB-12](https://haoshenqi.pingcode.com/pjm/workitems/cc_nhJnW)（用户故事）· Ship 需求 MAGICBOOK-220
> 来源：首访体验 QA 报告 §三.2–3.6、§八（`docs/project/qa/2026-10-23/2026-10-23-qa-report.md`）
> 需求基线：[`docs/product/library/requirements.md`](../../../product/library/requirements.md) §2 R213

## 1. 目标与范围

一条 L 量级的体验改版，拆成三个可独立验收的工作项：

| 子项 | 内容 | 外部依赖 | 量级 |
| --- | --- | --- | --- |
| **A 导航与外壳** | 侧边栏分组 + 计数、`创建书架`裁切修复、11 个 chips 补文字（窄屏抽屉）、卡片格式徽标、搜索入口合并、移动端底部导航 | 无 | M |
| **B 继续阅读** | 新建 `reading_progress` 表 + 阅读器进度回传 + 首页「继续阅读」模块 | 无（纯本仓） | M |
| **C 今日计划 + 分级推荐** | 新 `/home` 路由（登录后默认落点）、今日计划聚合卡（复用现有 `/ajax/learning/*` 代理）、分级推荐规则、随机发现降级 | 无（本条不新建 moon-well 接口） | M |

依赖顺序 **A → B → C**：A 是外壳（`/home` 复用 A 的卡片与侧边栏产出），B 提供「继续阅读」数据源，C 把两者拼成首屏。

## 2. 现状诊断（代码事实，2026-10-23 核查）

| 事实 | 证据 | 影响 |
| --- | --- | --- |
| 首页只有随机发现 + 通用列表 | `cps/templates/index.html`（156 行，`Discover (Random Books)` + `entries` 循环） | 三模块等于新建页面，不是改内容 |
| **`ub.ReadBook` 没有时间与位置** | `cps/ub.py:405`：只有 `book_id / user_id / read_status`（未读/在读/读完） | 「按最近阅读排序」和「37/125」都取不到 → B 必须新建表 |
| 网页阅读器位置只存浏览器本地 | `cps/static/js/reading/*.js` 无 position/cfi 上报；epub.js 位置在 localStorage | 换设备/换浏览器即丢；L1 宣称的「进度记忆」实为设备级 → 本条把它升级为账号级 |
| Kobo 通道另有自己的位置字段 | `cps/ub.py` `KoboReadingState.current_bookmark.progress_percent` | **不得复用**：它是 Kobo 协议的私有结构，网页写它会让 Kobo 端拿到脏位置 |
| 侧边栏平铺渲染 | `cps/templates/layout.html`：`for shelf in g.shelves_access` + 每行 badge 计数 + `nav_createshelf` | 分组是模板层改造，计数已有现成数据 |
| `ub.Shelf` **没有类型字段** | `cps/ub.py`（Shelf：name / is_public / user_id） | 分组的判定依据缺失 → §7 待拍板 |
| 今日计划数据已现成 | `cps/routes/learning.py`：`/ajax/learning/plan/today`、`/ajax/learning/srs/stats` 均已存在并带登录校验 | C 的「待复习词数」**不需要** moon-well 新接口 |
| 写作只有按 taskId 取详情 | `cps/routes/learning.py:258` `/ajax/learning/writing/task?taskId=`（R168），另有 `history` | 「写作待办条数」无现成聚合 → §5 两条落法二选一 |
| 无难度阶字段 | `cps/ub.py` / `cps/web.py` 均无 `difficulty` | 分级推荐的数据源缺失 → §7 待拍板 |

## 3. 方案选型

### 3.1 首页路由：新开 `/home`（拍板）

| 方案 | 结论 |
| --- | --- |
| **新开 `web.home` → `home.html`；`/` 保持原样** | ✅ 采用。旧发现页随时可回退，验收期可开关切换，两套模板互不影响 |
| 改 `web.index` 内部按 flag 渲不同模板 | 否决：`index` 同时服务 `/`、`/hot`、`/discover` 等 entry（`render_read_books` 共用），改它会波及全部书库列表页 |
| 直接替换 `/` 行为 | 否决：不可回退；现网用户书签全落 `/` |

### 3.2 进度存储：新建 `reading_progress`（拍板）

| 方案 | 结论 |
| --- | --- |
| **新表 `reading_progress`（user × book × format 唯一）** | ✅ 采用。位置/页码/百分比/最近阅读时间同表，`ReadBook` 保持「只记读完」语义不被污染 |
| `ub.ReadBook` 加 `last_read_at` + `position` 列 | 否决：`ReadBook` 是 calibre-web 原表，被 `render_read_books`、书库过滤、Kobo 同步多处读写；加列会把「读没读完」与「读到哪」两件事绑死，且与 `KoboReadingState` 语义重叠 |
| 复用 `KoboReadingState` | 否决：Kobo 私有协议结构，网页写入会污染 Kobo 端读取 |
| 只存 localStorage（维持现状） | 否决：跨设备丢失，首页「继续阅读」无法在服务端排序 |

### 3.3 今日计划：复用现有代理，不新建 moon-well 接口

「待复习词数」直接消费已存在的 `/ajax/learning/plan/today`（`LearningPlanVO.reviews`）或 `/ajax/learning/srs/stats`，`/home` 首屏异步拉、失败降级为「今日计划暂不可用」并保留入口链接——沿用 R166 的「页面零上游调用」原则。

唯一待定的「写作待办」有两条落法（§5），若需 moon-well 加字段，则按跨仓同源占号（moon-well 侧新占一个 R 编号，挂 MAGICBOOK 产品）。

### 3.4 分级推荐：规则化，不做模型

规则：按难度阶（阶 1..N）× 用户未读（`ReadBook.read_status != FINISHED`）取每阶 N 本，随机打散；无难度信息的书归「未分级」尾组。**不引入个性化权重、不做协同过滤**（需求非目标）。

**难度阶来源（2026-10-23 拍板）**：**按书架名解析 `阶N`**——`ub.Books` 没有 difficulty 字段，而「分级」在数据上本来就是「按阶建的书架」。解析规则（LLD §4.2 定形制）：书名匹配 `^阶\s*(\d+)` 或 `^(?:分级)?阶\s*(\d+)` 取数字为阶号，同阶多书架并入一阶，按 N 升序；解析不出阶号的书架不进推荐池。长期若要精细化，再给 Books 加 calibre 自定义列 `#difficulty`（本条不做）。

## 4. 拆单与依赖

```
A 导航与外壳 ──┐
                ├─→ C 今日计划 + 分级推荐（/home 组装）
B 继续阅读 ────┘
```

- A 与 B 可并行，C 等两者合并后再开工（C 的模板要复用 A 的卡片组件与 B 的数据接口）。
- 三个工作项各自一个 worktree、各自 merge 待验收；`/home` 的落地开关在 C 验收通过后才打开。

## 5. 跨仓契约

| 契约 | 现状 | 本条动作 |
| --- | --- | --- |
| `GET /ajax/learning/plan/today` | 已有，`LearningPlanVO`（reviews / newWords / strands） | 只读复用，不改形制 |
| `GET /ajax/learning/srs/stats` | 已有 | 备选数据源（到期词数口径更直接） |
| 写作待办 | 无聚合字段 | **已定方案 ①（零跨仓）**：`/ajax/learning/writing/history` 每条带 `lastDraftNo`（`null`＝出题后一稿未写），按其与 createdAt 数「今日未完成」；若列表响应缺 createdAt，则退方案 ②（moon-well 在 `/learning/plan/today` 增 `writingPending`，需同源占号 + 契约守卫） |

## 6. 风险与回滚

| 风险 | 处置 |
| --- | --- |
| `/home` 上线后首屏依赖多路异步，慢网变白屏 | 各模块独立 loading 骨架 + 任一失败只降级该模块；页面本身零同步上游调用 |
| 进度回传写库过频（长读用户） | 前端节流（翻 5 页或 10s 一次）+ 服务端 upsert；仅在位置变化显著时写 |
| `sendBeacon` 不带自定义头，CSRF 校验失败 | beacon 走 `application/x-www-form-urlencoded` 并带 `csrf_token` 字段（与表单字段校验同路径），LLD §3 钉守卫测试 |
| 新旧路径并存导致「读到一半」体验分裂 | 阅读器读回优先级：服务端 `reading_progress` → localStorage → 书首；迁移期双写在 LLD 明确 |
| 侧边栏分组判断错，用户书架被分错组 | A 的 `kind` 判定规则可回退为「全部进书架组」，分组只是展示层 |

## 7. 拍板结果

| # | 问题 | 结论（2026-10-23） | 阻塞 |
| --- | --- | --- | --- |
| 1 | 「难度阶」数据从哪来 | **按书架名解析 `阶N`**（见 §3.4）；不新增 Books 字段 | ✅ 已定 |
| 2 | 侧边栏四组如何判定书架归属 | **未定**：分类信息在数据层不存在（`shelf` 表只有 name/is_public/user_id/kobo_sync），三种来源各有代价，且「系统」组没有对应实体。细化说明与三个方案见 §7.1 | A |
| 3 | `/home` 是否作为登录后默认落点 | **直接作为默认落点**（`config_home_landing` 默认 `true`）；保留开关供回退 | ✅ 已定 |
| 4 | 「写作待办」取什么口径 | **按建议走方案 ①**：`/ajax/learning/writing/history` 数「今日未完成」（`lastDraftNo == null`），零跨仓；若 history 缺 createdAt 再用方案 ② | ✅ 已定 |

### 7.1 待定项细化：侧边栏四组怎么判定（#2）

现状事实（决定这个问题为什么难）：`shelf` 表字段只有 `id / uuid / name / is_public / user_id / kobo_sync / created / last_modified`——**没有任何「这个书架属于哪一类」的字段**，分组要的「类」在系统里根本不存在，不是「有但没读」。侧边栏现在只是把 `g.shelves_access` 平铺，一个书架一行。

于是要分四组，必须先回答三个子问题：

1. **类的来源**：名字约定 / 新增字段 / 硬编码白名单（见下表）。
2. **「系统」组装什么**：现无对应实体。候选＝`is_public=1` 的公开书架、`kobo_sync=1` 的书架、管理员专用书架；也可以**砍掉这一组**，只留三组（书架 / 分级 / 媒体）。
3. **分级组要不要按阶号排序**：若「分级」是多阶书架并列，组内需按 `阶N` 数字升序（与 #1 共用一套解析）。

| 方案 | 做法 | 代价 |
| --- | --- | --- |
| A 名字解析（零 schema） | 正则 `^阶\s*\d+` → 分级；含 TED/音频/听力 → 媒体；其余 → 书架 | 用户改书架名就换组；「系统」组无依据；多语言/新建易误判 |
| **B 新增 `shelf.kind` 列（建议）** | `kind` ∈ shelf/level/media/system，默认 `shelf`；迁移按 A 的正则一次性初判回填，之后书架编辑页可改 | 动 schema（有现成先例：`ub.py` 的 `migrate_oidc_user_columns()` 就是「检查列缺失 → ALTER ADD COLUMN」） |
| C 白名单硬编码 | 按 shelf id / 名字白名单分组 | 换库/换环境即失效，不可维护 |

建议 **B**：分类从此是数据而不是字符串约定，且「系统」组有明确归属；迁移成本是一次 `ALTER TABLE` + 一次回填。
