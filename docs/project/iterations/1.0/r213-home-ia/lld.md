# LLD — R213 首页信息架构（三子项实现细节）

> 状态：**A（非分组部分）与 B 已开发待验收 / A 侧边栏分组与 C 未定稿**（2026-10-23；A 已实现 chips 文字标签、卡片格式徽标、搜索合并、移动底部导航、创建书架裁切修复，**侧边栏四组分组按用户要求暂缓**等拍板；C 依赖 A/B 合入）
> 迭代：1.0 · PJM 工作项 [MB-12](https://haoshenqi.pingcode.com/pjm/workitems/cc_nhJnW) 及拆出的 A/B/C 三个任务（MB-16/17/18） · Ship 需求 MAGICBOOK-220
> 实现落点：worktree `../magicbook-r213-home-ia`，分支 `feat/r213-home-ia`（A/B/C 共用一树，按同编号互斥纪律）
> 上游：[hld.md](./hld.md)（方案选型与被否方案）· 需求基线 [`product/library/requirements.md`](../../../../product/library/requirements.md)
> 本文档只管「怎么实现」。§1–§3 与子项 B 相关，§4–§8 分别对应 A/C。

## 1. 数据模型：`reading_progress`（子项 B）

落 `cps/ub.py`（与其它 `ub.*` 同文件，随 `ub.init_db()` 的 `create_all` 自动建表——不重复 AI 表「导入晚于 create_all」的坑）。

```sql
CREATE TABLE reading_progress (
    id                      INTEGER PRIMARY KEY,
    user_id                 INTEGER NOT NULL REFERENCES user(id),
    book_id                 INTEGER NOT NULL,
    book_format             VARCHAR(16) NOT NULL,   -- EPUB / PDF / TXT / CBR
    position                VARCHAR(512),           -- EPUB: CFI；PDF: 页号；TXT: 字符偏移
    progress_percent        FLOAT,                  -- 0–100，卡片进度条
    page_current            INTEGER,                -- 37
    page_total              INTEGER,                -- 125
    last_read_at            DATETIME NOT NULL,
    updated_at              DATETIME NOT NULL
);
CREATE UNIQUE INDEX uq_reading_progress_user_book_fmt
    ON reading_progress (user_id, book_id, book_format);
CREATE INDEX ix_reading_progress_user_time
    ON reading_progress (user_id, last_read_at);
```

边界（与既有结构的分工，**不许交叉写**）：

| 结构 | 语义 | 谁写 |
| --- | --- | --- |
| `ub.ReadBook.read_status` | 读完 / 在读 / 未读 | 保持原逻辑（阅读器开合、书库过滤） |
| `reading_progress` | 读到哪（位置、页码、时间） | 本条新增端点 |
| `KoboReadingState.current_bookmark` | Kobo 设备同步位置 | 仅 Kobo 通道（`cps/kobo.py`） |

## 2. 进度回传端点（子项 B）

```
POST /ajax/reading-progress        # @user_login_required，CSRF 校验
form: book_id, format, position, percent, page_current, page_total, csrf_token
→ {"success": true, "last_read_at": 1793...}
```

- **upsert**：按 `(user_id, book_id, book_format)` 查到则更新，否则插入；`last_read_at` 每次刷新。
- **入参防御**：`book_id` 必须数字且在库；`format` 白名单（EPUB/PDF/TXT/CBR）；`percent` 夹到 0–100；`page_current ≤ page_total`；`position` 截断 512 字符。
- **失败不打扰读者**：任何校验失败返回 4xx + `{"success": false}`，前端静默丢弃（进度不是关键路径），但**控制台留 warning**——不做静默失败（家族纪律 ⑦：故障要在界面上可见，这里可见面是 devtools 而非 toast）。
- **节流**：前端 10 秒或翻 5 页触发一次；`pagehide` + `visibilitychange(hidden)` 补最后一笔，用 **`fetch(..., {keepalive: true})`**——不是 `sendBeacon`。这是本仓既有姿势（`reading_time_tracker.js` 同款），keepalive fetch 能带 `X-CSRFToken` 头，绕开「beacon 不能加自定义头、只能把 token 塞 body」的绕路方案（初稿写的就是那条绕路，实测后按仓内先例收口）。
- **格式覆盖**：**EPUB/KEPUB、PDF、TXT 均已接线**（2026-10-23 二次提交）。PDF 走 readpdf.html 内联脚本挂 `PDFViewerApplication.eventBus('pagechanging')`，恢复用 viewer 原生 `#page=N` 片段（`viewer.js` 是 vendored 文件，不动它）；TXT 走 txt_reader.js 位移计页（`homeLeft - offset` / `pageWidth`），**TXT 由此第一次拥有进度记忆**。CBR/CBZ 未接（`readcbr.html` kthoom 链路，同口径后续再接）。
- **`ReadBook.last_time_started_reading` 不能当「最近阅读」用**：该字段只有 `cps/kobo.py:804` 写入，网页读者恒为 NULL（这是「不能靠 ReadBook 排序」的直接证据，比「只有三态」更硬）。

### 2.1 读回优先级（阅读器进入时）

```
服务端 reading_progress.position  →  localStorage 旧位置  →  书首
```

- 服务端有值时以服务端为准，并把同一位置回写 localStorage（保持离线可用）。
- 首次迁移期：账号在服务端无记录但 localStorage 有 → 直接用本地位置并**上报一次**，自然完成回填（不写迁移脚本、不猜历史）。
- 关闭 `reading_progress` 读回（开关见 §8）时行为完全回到今天。

### 2.2 各格式取位置的方式

| 格式 | position | page 计数 |
| --- | --- | --- |
| EPUB | `rendition.currentLocation().start.cfi` | `rendition.location.start.displayed.page/total`（epub.js `locations.generate` 后可用；未生成时只报 percent） |
| PDF | 页码字符串 | `PDFViewerApplication.page` / `pagesCount` |
| TXT | 页码（复用 page_current 列，position 留空） | 位移计页：`(homeLeft - offsetLeft) / (width + gap)` + 1，总页 `ceil(scrollWidth / pageWidth)` |
| CBR | 页码 | `kthoom` 当前页 |

## 3. 「继续阅读」模块取数（子项 B → C 消费）

```python
# cps/web.py 内辅助函数，供 home 视图调用
def recent_reading(user_id, limit=6):
    rows = session.query(ub.ReadingProgress).filter_by(user_id=user_id) \
        .order_by(ub.ReadingProgress.last_read_at.desc()).limit(limit).all()
    # join Books 取元数据；已被删除的书静默跳过；读完的书（ReadBook=FINISHED）不进入列表
```

- 卡片显示：封面、书名、`37/125` 或百分比、上次阅读时间（今天/昨天/日期）。
- 兜底：`reading_progress` 为空时，读 `ReadBook.read_status == IN_PROGRESS` 取最多 6 本，只显示「继续阅读」不带页码（新用户/老账号迁移期不出现空模块）。

## 4. `/home` 路由与页面结构（子项 C）

```python
@web.route("/home")
@user_login_required
def home():
    return render_title_template("home.html", title=_("Home"))
```

- 模板 `cps/templates/home.html` 继承 `layout.html`，区块顺序：

```
┌──────────────────────────────────────────────┐
│ 继续阅读（recent_reading，横向卡片，最多 6）      │  ← 服务端渲染
├──────────────────────────────────────────────┤
│ 今日计划（待复习 n 词 · 写作 m 篇）→ /learning  │  ← 异步 /ajax/learning/plan/today
├──────────────────────────────────────────────┤
│ 分级推荐（按难度阶分组，每阶 4–6 本）             │  ← 服务端渲染（规则化）
├──────────────────────────────────────────────┤
│ 随机发现（原首页内容，降级为一个模块）             │  ← 复用 index.html 的卡片循环
└──────────────────────────────────────────────┘
```

- **页面零同步上游调用**：今日计划由 `home.js` 异步拉，失败只降级该卡（显示「今日计划暂不可用 · 去学习页看看」并保留链接）。
- 卡片循环抽成 `_book_card.html`（include 宏），供 `home.html` 与 `index.html` 共用，避免两处样式漂移。

### 4.1 今日计划取数（两块，两个接口）

```js
// cps/static/js/home.js
GET /ajax/learning/plan/today   → LearningPlanVO.reviews（待复习词数）
GET /ajax/learning/writing/history → 数「今日未完成」
```

- **待复习词数**：直接取 `plan/today` 的 `reviews`，与 `/learning` 页同源（C2 判据：两处数字必须一致）。
- **写作待办**（2026-10-23 拍板走方案 ①，零跨仓）：`history` 每条带 `lastDraftNo`（`null` ＝出题后一稿未写），按 `createdAt` 落今日的条目中 `lastDraftNo == null` 计数。
- **前置核实（开发第一步）**：确认 `history` 响应确实带 `createdAt`（`moon-well/docs/product/learning/interface.md` §B1b 只写了 `lastDraftNo`，未明写时间字段）。缺则退方案 ②（moon-well 加 `writingPending`，同源占号），**不猜字段名、不前端造数据**。
- 两个请求并行发出，各自 catch；任一失败只让该行显示 `—`，不整卡报错。

### 4.2 分级推荐规则（按书架名解析阶号）

```python
LEVEL_RE = re.compile(r"^(?:分级)?阶\s*(\d+)")   # 匹配「阶1」「分级阶2」「阶 3」

def level_of_shelf(name):  # 解析不出 → None
    m = LEVEL_RE.match((name or "").strip())
    return int(m.group(1)) if m else None
```

- **归阶**：书架名命中正则 → 该阶；同阶多个书架的书合并成一阶（去重按 book id）。
- **排序**：按阶号升序（1..N），不按书架名 ASCII 序（否则「阶10」会排在「阶2」前——这是本条的真坑）。
- **取书**：每阶取未读（`ReadBook.read_status != FINISHED`，含无 ReadBook 记录的书）最多 `home_level_picks`（默认 6）本，同阶内随机打散；已读完的书不进推荐。
- **无阶书架**：解析不出阶号的书架不进推荐池，其书归「未分级」尾组（不隐藏、不报错）。
- **性能**：一次查出「书架 → 书」映射再在内存分组，禁止每阶一次查询（N+1）。

## 5. 侧边栏分组（子项 A）

改造点 `cps/templates/layout.html`：`g.shelves_access` 平铺 → 分组渲染。

```
书架   （kind=shelf，用户自建）
分级   （kind=level，阶 1..N 升序，组内按 4.2 的解析排序）
媒体   （kind=media，TED / 音频）
系统   （kind=system，内置/管理用途）
```

- **分组判定仍待拍板**（HLD §7.1）：分类信息在 `shelf` 表里不存在（只有 name/is_public/user_id/kobo_sync），三种来源＝名字解析（零 schema，改个名就换组）/ 新增 `shelf.kind` 列（建议，先例 `ub.py: migrate_oidc_user_columns()`）/ 硬编码白名单。**「系统」组装什么也需一并定**（公开书架 / kobo_sync 书架 / 直接砍掉这一组）。
- 无论选哪种，硬约束：**「判定不出 → 归书架组」，任何书架都不许消失**（数量守恒，AC A1 判据）。
- 组标题右侧显示书架数 / 书籍数（现有 `shelf.books.all()|length` 已有；避免 N+1：一次 `outerjoin` 聚合到 `g`）。
- 「创建书架」裁切：`.create-shelf` 从侧栏底部静态定位改为随内容流（`position: static`）+ 侧栏 `overflow-y: auto`，加 900px 高度回归用例。

## 6. 卡片徽标 / chips / 搜索合并 / 移动端底部导航（子项 A）

| 项 | 落点 | 做法 |
| --- | --- | --- |
| 格式徽标 | `index.html` 两处封面循环（随机区 + 列表区） | 角标显示主文本格式（`main_format` 过滤器：第一个非音频格式）+ 音频徽标。**已实现（2026-10-23）**。**偏差**：时长/「已缓存」未做——缓存状态在 moon-well，列表页同步拉会 N 打它的接口，留异步批量接（C 或单独小单）；EPUB/PDF 不加时长照原案 |
| chips 文字 | `index.html` filterheader | 每个 chip 加 `<span class="chip-label">`（msgid 走 Babel，zh_Hans_CN 已补词条）；`<768px` 整排收进 Bootstrap collapse 抽屉，「筛选与排序」按钮开合，桌面端媒体查询强制展开。**已实现（2026-10-23）** |
| 搜索合并 | `layout.html` 顶栏 | 高级搜索入口并入搜索框输入组（input-group-btn 内的 `⏷` 按钮，保留 `id="advanced_search"`——onboarding 引导步骤选中它），主导航不再并排。**已实现（2026-10-23）**。**偏差**：原案的「`⏷` 展开内联高级面板」未做，改为直达高级搜索页——内联面板与 C 的筛选能力重叠，留给 C 一并设计 |
| 移动端底部导航 | `layout.html` 尾部 + `style.css` | `@media (max-width: 767px)` 固定底栏：书库 `/` · 学习 `/learning` · 我的（未登录显示登录）；`body { padding-bottom: 54px }`。**已实现（2026-10-23）**。样式落 `style.css`（非 caliBlur——caliBlur 是主题覆盖层，基础组件样式应进主表） |
| 「创建书架」裁切 | `style.css` `.navigation` | `max-height: calc(100vh - 80px); overflow-y: auto;`（仅 ≥768px，侧栏不脱离文档流）。**已实现（2026-10-23）** |
| 高级搜索「阅读状态」 | `search_form.html` + `search.py` | **见 §6.1**（顺手修，不在原始拆单范围内但同属「搜索入口可用」） |

### 6.1 高级搜索「阅读状态」四态化（2026-10-23 追加）

**问题**：这个下拉原样继承自 Calibre-Web，选项是布尔三态的直译——`Any/Empty/Yes/No` → **任何 / 空 / 确认 / 没有**。在中文语境里：
- 「确认」「没有」完全无法对应「读过 / 没读过」；
- 未配置 calibre 自定义阅读列时，`Empty` 与 `False` 落到**同一个 SQL 条件**（`coalesce(read_status,0) != FINISHED`），等于两个名字不同、行为相同的选项；
- 本仓 `ReadBook` 早就是三态（UNREAD/IN_PROGRESS/FINISHED），但界面上没有「在读」这个最常用的选项。

**改法**：
- 界面改成互斥且穷尽的三态 + 「不限」，并加一行说明兜住边界：**未读**（从没打开过或标记未读）/ **在读**（打开过没读完）/ **已读**（读完了）。
- 后端取值改为语义化 `unread` / `in_progress` / `finished`；旧 URL 的 `True` / `False` / 空值**保持兼容**（`True`→已读、空→未读、`False`→历史「未读完」语义）。
- `unread` 用 `NOT EXISTS(... IN (IN_PROGRESS, FINISHED))` 实现——从没打开过的书**没有 ReadBook 行**，等值匹配会把它们全漏掉，而它们才是「未读」的主体。
- 配了 calibre 自定义阅读列的实例退化成布尔三项（该列只有是/否），措辞改为「未填写 / 是 / 否」，不再出现「空/确认/没有」。
- 搜索条回显把内部值翻成人话（`Read Status = '未读'`），不再把 `in_progress` 直接糊到页面上。
- 同页自定义布尔列下拉（`cc.datatype == 'bool'`）是同一套直译，一并换成「未填写 / 是 / 否」。
- i18n 新增 9 条 msgid 并编译；**没有改全局的 `Yes`/`No`/`Empty`**——`Yes` 在别处（如确认对话框）仍是「是」，改全局会连带误伤。

**测试**：`tests/test_adv_search_read_status.py` 7 例（三态条件互不相同、unread 必须走 NOT EXISTS、旧值兼容、模板与 .mo 词条守卫）。测试环境无 calibre 库、跑不起 `/advsearch` 渲染，故界面断言落在模板源码 + 已编译译文上。

## 7. 异常与边界

| 场景 | 行为 |
| --- | --- |
| 书被删除但 `reading_progress` 残留 | 查询 join 不到即跳过；提供清理 SQL（文档记录，不自动跑） |
| 同一本书两种格式（EPUB + PDF） | 按格式各一行，首页只展示最近一条（避免同名两卡） |
| 用户从未读过任何书 | 继续阅读模块整块隐藏，首页首屏从今日计划开始 |
| moon-well 不可用 | 今日计划卡降级，其余模块不受影响 |
| 无难度阶数据的书 | 进「未分级」尾组，不隐藏 |
| 窄屏 + 抽屉 + 底栏同现 | 抽屉 z-index 高于底栏；打开抽屉时底栏 `pointer-events: none` |

## 8. 配置项与开关

| 开关 | 位置 | 默认 | 作用 |
| --- | --- | --- | --- |
| `config_home_landing` | 站点配置（boolean） | **`true`（2026-10-23 拍板：`/home` 直接作为登录后默认落点）** | 登录/回站后落 `/home`；置 `false` 即回退到原 `/` 发现页 |
| `reading_progress_enabled` | 站点配置（boolean） | `true` | 总开关；关＝不写不读，回退 localStorage |
| `home_recent_limit` | 常量 | 6 | 继续阅读条数 |
| `home_level_picks` | 常量 | 6 | 每难度阶推荐本数 |

## 9. 文档四问预答

| 问 | 答案 |
| --- | --- |
| 能力变了吗 → L1 | 要改：`product/readme/library.md`（首页三模块、侧边栏分组、底部导航）、`product/readme/reading.md`（「进度记忆」从设备级改为账号级，措辞必须改，否则文档说谎） |
| 契约变了吗 → L2 | 要改：`product/library/interface.md` 增 `POST /ajax/reading-progress`；`product/reading/interface.md` 增读回约定；若走 moon-well 加 `writingPending`，同步 `moon-well/docs/product/learning/interface.md` |
| 实现 / 边界变了吗 → L3 | 要改：新建 `product/library/features/home-ia.md`、`product/reading/features/reading-progress.md` |
| 本次怎么实现 → LLD | 本文件（状态行随里程碑回填） |

守卫测试清单（开发阶段落地）：① `reading_progress` 唯一约束（同 user/book/format 二次写不新增行）；② 端点 CSRF 缺失 → 400 且不落库；③ `percent` 越界被夹取；④ `recent_reading` 排除已读书与被删书；⑤ `/home` 登录保护（匿名访问跳登录）；⑥ 侧边栏分类不丢书架（每个书架必属一组）。
