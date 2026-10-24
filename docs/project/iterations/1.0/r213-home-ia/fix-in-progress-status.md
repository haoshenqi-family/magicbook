# 修复方案：「阅读状态 = 在读」搜不到结果（R213-A 缺陷）

> 状态：**已实施**（2026-10-24；2026-10-23 定位根因，用户拍板后落代码 + 回填）
> 关联：MB-16 / MAGICBOOK-220｜涉事改动 `3c2c6a6d`（阅读状态四态化）
> 报告样例：book 145（`/read/145/epub#epubcfi(/6/6!/4/186/1:0)`）

## 0. 拍板结果（2026-10-24）

| # | 问题 | 决定 |
| --- | --- | --- |
| 1 | 只打开不翻页算不算「在读」 | **算**（percent=0 也落状态）。已由前端保证：`reader-progress.js` 首次采集时 `lastSentPage === null`，必发一次 |
| 2 | 已读完的书回看是否退回「在读」 | **不退回**，`FINISHED` 是用户的显式标记 |
| 3 | 回填与代码是否同批 | **同批**（代码上线后立即执行 §5 SQL，避免窗口期） |

## 1. 结论

**不是查询写错了，是「在读」这个状态在数据里根本不存在。**

搜索「在读」筛的是 `book_read_link.read_status == 2`（`STATUS_IN_PROGRESS`），
而当前系统里**只有 Kobo 设备同步会写这个值**（`cps/kobo.py:801`）。网页阅读器
从头到尾都不碰 `book_read_link`。

## 2. 证据（生产库实测，只读）

| 检查项 | 结果 |
| --- | --- |
| `book_read_link` 状态分布 | `status=0` 3 条、`status=1` 1 条、**`status=2` 0 条** |
| book 145 在 `book_read_link` | **没有记录**（一行都没有） |
| book 145 在 `reading_progress` | 有：user 3 / EPUB / 90–1467 页 / 7% / `2026-10-23 15:09:55` |
| `reading_progress` 总量 | 1 条（1 用户 / 1 书） |
| 有进度但 ReadBook 无记录 | 1 条（就是这本） |
| `config_read_column` | `0`（未配置自定义阅读列 → 走 `ReadBook` 分支） |

代码侧：

| 写入 `read_status` 的位置 | 写入的值 |
| --- | --- |
| `cps/helper.py:315-320`（「标记已读」按钮） | 只有 `FINISHED(1)` 与 `UNREAD(0)` |
| `cps/kobo.py:801-805`（Kobo 同步） | 唯一会写 `IN_PROGRESS(2)` 的地方 |
| `cps/web.py` `read_book` 路由（打开阅读器） | **不写任何状态**，只读 `ReadingProgress` 拼位置 |
| `cps/routes/reading.py`（`POST /ajax/reading-progress`） | **只写 `reading_progress`**，不碰 `book_read_link` |

查询侧没有问题：`generate_linked_query`（`cps/db.py:819-824`）的 join 是
`LEFT OUTER JOIN book_read_link ON (user_id = 当前用户 AND book_id = books.id)`，
`adv_search_read_status` 里的 `and_(user_id, read_status==2)` 能正常过滤。
**只要有 status=2 的数据，就一定能查到。**

## 3. 根因

R213-B 把「读到哪」从 `ReadBook` 拆进新表 `reading_progress`——这个拆分是对的
（位置与状态是两件事）。但当时只安排了「谁写位置」，**没有安排「谁把书标成在读」**。

结果三个状态里：

- **已读**：准（手动标记会写 `FINISHED`）
- **未读**：准（没读完的本来就算未读）
- **在读**：**永远是空集**（只有 Kobo 会写 2，而用户在网页读）

这是 R213-A 四态化时的疏漏：我确认了 `ReadBook` 有这个常量，没有确认
「谁会写它」。设计时把「模型有能力表达」当成了「数据里会有」。

## 4. 三个方案

### 方案 A（推荐）：阅读器写位置时，顺手把状态标成「在读」

> **已实施**（2026-10-24，`cps/routes/reading.py`）。落地形态与下文一致。

在 `POST /ajax/reading-progress`（`cps/routes/reading.py`）里，upsert
`ReadingProgress` 的同时 upsert `ReadBook`：

| 当前 ReadBook 状态 | 动作 |
| --- | --- |
| 没有记录 | 新建，`read_status = IN_PROGRESS` |
| `UNREAD(0)` | 置 `IN_PROGRESS(2)` |
| `IN_PROGRESS(2)` | 保持 |
| `FINISHED(1)` | **不动**（已读完的书回看不应退回在读） |

三条实现约束（都有明确理由）：

1. **只在进度上报端点写，不在 `read_book` 的 GET 路由里写**。GET 写库会被页面预取、
   爬虫、刷新误触发；进度上报是真实阅读行为的自然信号。
2. **不碰 `times_started_reading` / `last_time_started_reading`**。这两个字段只被
   Kobo 通道读写（`kobo.py:803-804` 写、`874-877` 回给设备），是设备的阅读统计；
   网页侧写入会让 Kobo 端「阅读次数」凭空增长。
3. **不需要手工创建 `KoboReadingState`**。`kobo.get_or_create_reading_state`
   （`kobo.py:842-854`）在 `kobo_reading_state` 为空时会自动补建，网页侧只插
   `ReadBook` 是安全的。

**收益**：`book_read_link` 回到「唯一真相源」的地位，Kobo / 网页 / 书库过滤 /
成就 / 搜索全部一致。
**成本**：写入点从一个变成两个，需要保证与 Kobo 同步不打架（同一行、只改
`read_status`，冲突面很小）。

### 方案 B（最小改动）：搜索的「在读」改查 `reading_progress`

`adv_search_read_status("in_progress")` 改成对 `reading_progress` 做 EXISTS 判断。

- 优点：不动写路径，改完立刻能搜到 145。
- **致命缺点**：必须同时把「未读」的 `NOT EXISTS` 也改成排除 `reading_progress`，
  否则一本书会同时出现在「在读」和「未读」里（因为它在 `book_read_link` 里仍然
  没有行）。而且这个方案固化了两套数据源——**Kobo 用户搜「在读」依然搜不到自己**
  （Kobo 只写 `book_read_link` 不写 `reading_progress`）。

### 方案 C：A + 一次性回填 + 读取口径收敛

在 A 之上补两件事：

1. **回填历史**：把已有的 `reading_progress` 记录补进 `book_read_link`
   （当前影响 **1 行**，见 §5）。
2. **收敛读取口径**：把「某本书对某用户是什么状态」抽成一个公共函数（或共享
   SQL 片段），供 `search.py` / `render_read_books` / 首页继续阅读共用，避免三处
   各写一遍判定条件、下次再改口径又漏一处。

**推荐 A 作为最小可交付，C 作为收敛形态**（回填只有 1 行，等于顺手做完）。

## 5. 回填 SQL（只读演练过，**未执行**）

```sql
-- 有网页阅读进度、但 book_read_link 里还没有行的书 → 补建为「在读」
INSERT INTO book_read_link
       (book_id, user_id, read_status, last_modified,
        last_time_started_reading, times_started_reading)
SELECT p.book_id, p.user_id, 2, datetime('now'), NULL, 0
FROM reading_progress p
WHERE NOT EXISTS (
    SELECT 1 FROM book_read_link r
    WHERE r.user_id = p.user_id AND r.book_id = p.book_id
);
```

- 影响行数（当前生产库）：**1**
- 显式把 `last_time_started_reading` 留空、`times_started_reading` 置 0——
  不伪造 Kobo 的阅读统计。
- 回滚：`DELETE FROM book_read_link WHERE id IN (<本次插入的 id>)`（先备份）。

## 6. 决策（已定，见 §0）

| # | 问题 | 建议 |
| --- | --- | --- |
| 1 | **只打开不翻页**（percent=0 / page=1）算不算「在读」？ | 算。进度上报只在真实阅读时触发，打开即算符合直觉；若求保守可加 `percent > 0` 门槛 |
| 2 | 已读完的书**回看**要不要退回「在读」？ | 不要。`FINISHED` 是用户显式的完成标记，回看不该撤销 |
| 3 | 「未读」的口径要不要跟着变？ | A 上线后自动收敛（有进度就有 IN_PROGRESS 行 → 自动离开「未读」）。但**回填前有窗口期**：145 会同时算「未读」且「在读」搜不到，所以回填要和代码同批上 |

## 7. 验收清单

- [ ] 搜「在读」能命中 book 145
- [ ] 搜「未读」不再包含 book 145（同一个搜索页两个下拉互斥）
- [ ] 把 145 标记为已读后：搜「在读」不含它，搜「已读」含它
- [ ] 已读完的书再次打开阅读器翻页，状态不被改回「在读」
- [ ] Kobo 设备同步过状态的书，网页阅读后状态不被降级
- [ ] `times_started_reading` 不因网页阅读增长（Kobo 端统计不受污染）
- [ ] 首页「继续阅读」行为不变（仍以 `reading_progress` 为准）

## 8. 一句话给未来的自己

**「模型里有这个字段」≠「数据里有这个值」。**
做界面选项时，除了看常量定义，必须再问一句「谁会写它、多久写一次、现在有多少行」——
这次的「在读」就是只看了 `ReadBook.STATUS_IN_PROGRESS` 就上了界面，用户第一次点就空结果。
