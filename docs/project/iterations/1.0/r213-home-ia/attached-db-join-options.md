# ATTACH 跨库 join 的代价与替代方案

> 状态：**已决——不改架构**（2026-10-24 讨论并定稿；只做治理，不动代码）
> 引出：排查「高级搜索『在读』返回空集」时撞上 `no such table: books`
> 落地：治理三项 → [docs/kb/sql/db-schema-map.md](../../../kb/sql/db-schema-map.md)
> 结论先行：**现在不该改**。真正要治的是「认知成本」和「单连接」，不是 join 本身。

## 0. 先校准概念

这不是通常说的「跨库 join」（不是两个数据库服务器、不是分布式查询、没有网络往返）。

事实是：`cps/db.py:697-705` 建了一个**内存 SQLite 连接**，把两个文件挂上来——

```python
engine = create_engine('sqlite://', poolclass=StaticPool)   # 主库为空的内存库
connection.execute("attach database '<calibre>/metadata.db' as calibre")
connection.execute("attach database '<config>/app.db'      as app_settings")
```

所有 `calibre_db.session` 的查询都在这**一个连接**上执行，`books` 与 `book_read_link`
的 join 是同一个连接内两个 attached schema 的本地 join。SQLite 原生支持，语义完全合法。

所以问题不是「join 对不对」，而是「ATTACH 这套架构的代价我们能不能接受」。

## 1. 真实代价（四条，都可验证）

| # | 代价 | 证据 | 实际影响 |
| --- | --- | --- | --- |
| 1 | **calibre 侧查询串行化** | `poolclass=StaticPool`（`db.py:701`）——因为每个新连接都要重新 ATTACH 两个文件，干脆只留一条连接复用 | 并发上限 = 1。家庭规模无感，多人同时刷书库会排队 |
| 2 | **两个连接同时碰 `app.db`** | `ub.session` 用普通 `create_engine`（`ub.py:748`，QueuePool 多连接）；`calibre_db.session` 又通过 ATTACH 持有 `app.db` | 写要抢锁，理论上可能 `database is locked`。当前容器运行期内 0 次（样本太小，不作结论） |
| 3 | **隐式跨库事务** | `calibre_db.session.commit()` 提交的是该 session 内**所有**改动，包括 `app_settings` 的表 | 现在没人这么写；但将来有人在那个 session 里改 ub 表，会**静默**一起提交，出问题极难查 |
| 4 | **运维与认知成本** | 备份要备两个文件；手工查库不 ATTACH 就 `no such table: books`（本次排查已踩） | 每次排查多花几分钟，新人更容易踩 |

**一个重要的减轻事实**：跨库**只发生在读**。
写操作都是各写各的——`ub.session` 写 `app.db` 的 ub 表，`calibre_db.session` 只写
calibre 表（`editbooks.py` 全量核查：没有一处 `calibre_db.session.add(ub.*)`）。
所以「跨库事务一致性」这条最吓人的风险，目前**不在**风险清单里。

综合判断：**中低风险，代价主要是认知成本和并发天花板，不是正确性**。

## 2. 替代方案

### 方案 A：不动架构，只做治理（推荐）

ATTACH 是 Calibre-Web 上游的核心数据层设计，全仓数百处查询依赖
`calibre_db.session`。拆它 = 重写数据层 + 与上游永久分叉。当前规模
（1 用户、几千本书）完全不值得。

**做三件低成本的事**（合计约 1 小时）：

1. **文档化 schema 归属**：一张表写清「`books`/`authors`/`tags` → `metadata.db`；
   `user`/`book_read_link`/`reading_progress`/`shelf` → `app.db`」，放进
   `docs/kb/`。今天踩的坑就是因为没有这张表。
2. **立一条规矩**：「写 ub 表一律走 `ub.session`；只有『读筛选』才用
   `calibre_db.session` 的跨库 join」。这句话能让代价 #3 永不成真。
3. **监控 `database is locked`**：出现即说明到了该拆的时候，而不是等用户抱怨。

### 方案 B：展示走两段查询（只解决展示，不解决筛选）

先查 calibre 拿书，再按 `book_id` 批量查 `app.db` 拿状态，Python 合并。

- 优点：完全不跨库，写法简单。
- **致命局限**：只能解决「列表上显示已读/在读小徽章」，**不能解决筛选**。
  因为筛选要在 SQL 里做——先分页再过滤，每页数量会不齐、总数也会错。
- 所以它替代不了 `adv_search_read_status` 这条路，只能减少一部分跨库调用。

### 方案 C：筛选时用临时表，把状态搬进 calibre 连接

先在 `ub.session` 查出 `book_id` 集合（几十到几千），在 calibre 连接上
`CREATE TEMP TABLE`，再 `WHERE books.id IN (SELECT id FROM temp_read_state)`。

- 优点：SQL 里只碰单库 + 临时表；绕开 SQLite 绑定参数上限；语义清晰。
- 缺点：多一次查询往返；**StaticPool 单连接意味着 TEMP TABLE 会被跨请求共享**，
  必须每请求 `DROP` 或加请求 ID 前缀，否则并发下互相污染——等于用新的坑换旧的坑。
- 适合：状态集合小、且真的要拆 ATTACH 的时候。

### 方案 D：把状态物化到 `metadata.db`（不推荐）

在 calibre 库里建一张投影表，`read_status` 变化时同步写过去，筛选就在单库内完成。

- 不推荐：**双份真相**。一致性维护成本远大于它省下的那次 join；而且
  `metadata.db` 是 calibre 的书库文件，桌面端也可能打开它，多写入者风险高。

### 方案 E：把 ub 表迁进 `metadata.db`（不推荐）

- 不推荐：calibre 桌面端会读写/重建 `metadata.db`，把用户数据放进去等于和
  calibre 抢同一个文件。迁移本身也是一次高风险数据操作。

## 3. 建议

**现在：方案 A（不动代码，只做文档化和监控）。**

理由是三条事实叠起来：
1. 跨库**只在读**，没有跨库写；
2. 当前规模下单连接毫无压力（并发个位数）；
3. 拆架构的收益（并发、认知）远小于成本（重写数据层 + 与上游分叉）。

**什么时候该真的拆**（触发条件，任一即可）：

- 出现 `database is locked` 且不是偶发；
- 并发用户稳定 > 5，书库页开始明显排队；
- 需要做读写分离或换 PostgreSQL（那时 ATTACH 方案直接不成立，必须拆）。

到那时优先走 **方案 C 的思路**（临时表/两段查询），而不是迁表——迁表会
把「和 calibre 抢文件」这个更大的问题引进来。

## 3.1 决策（2026-10-24）

**结论：不改。** 按方案 A 执行治理，不拆分数据层。

治理三项的落点：

| 治理项 | 落点 | 状态 |
| --- | --- | --- |
| 文档化 schema 归属（哪张表在哪个库） | [docs/kb/sql/db-schema-map.md](../../../kb/sql/db-schema-map.md) | ✅ 已写 |
| 立规矩：「写 ub 表走 `ub.session`；跨库 join 只用于读筛选」 | 同上 §3 规矩一/二 | ✅ 已写 |
| 监控 `database is locked` | 暂不建自动告警，出现时按 §3 触发条件重新评估 | ⏳ 观察中 |

未做（明确不做）：临时表、状态物化、迁表、拆引擎。理由是当前规模收益不成立，
且每一项都会引入新的不一致面。


## 4. 一句话

**ATTACH 不是「跨库 join」的错误，它是「用一个连接换跨库便利」的取舍。**
它的代价没到要付代价去改的程度，但它的认知成本已经真实发生了（今天踩了一次）。
所以先补文档和规矩，把「不知道数据分两个文件」这个坑填了，架构不动。
